param([ValidateSet('headless','blender')][string]$Runtime='headless',[string]$DataRoot)
$ErrorActionPreference='Stop'
$repository=Split-Path -Parent $PSScriptRoot
$executable=Join-Path $repository 'artifacts\desktop\RobotOps Twin\RobotOps Twin.exe'
$root=Join-Path $repository ('artifacts\desktop-smoke\'+[guid]::NewGuid().ToString('N')+' test data')
if ($DataRoot) { $root=[IO.Path]::GetFullPath($DataRoot) }
New-Item -ItemType Directory -Path $root -Force | Out-Null
Add-Type -TypeDefinition @'
using System; using System.Text; using System.Runtime.InteropServices;
public static class RobotOpsOwnedWindow {
 delegate bool EnumProc(IntPtr h, IntPtr l);
 [DllImport("user32.dll")] static extern bool EnumWindows(EnumProc cb,IntPtr l);
 [DllImport("user32.dll")] static extern uint GetWindowThreadProcessId(IntPtr h,out uint p);
 [DllImport("user32.dll",CharSet=CharSet.Unicode)] static extern int GetWindowText(IntPtr h,StringBuilder t,int c);
 [DllImport("user32.dll")] static extern bool PostMessage(IntPtr h,uint m,IntPtr w,IntPtr l);
 public static bool Close(int pid) { bool sent=false; EnumWindows((h,l)=>{uint p;GetWindowThreadProcessId(h,out p);var t=new StringBuilder(256);GetWindowText(h,t,256);if(p==pid && t.ToString()=="RobotOps Twin") sent=PostMessage(h,0x10,IntPtr.Zero,IntPtr.Zero);return true;},IntPtr.Zero);return sent; }
}
'@
function Wait-Condition([scriptblock]$Condition,[string]$Message,[int]$Seconds=45) {
    $watch=[Diagnostics.Stopwatch]::StartNew()
    while (-not (& $Condition)) {
        if ($watch.Elapsed.TotalSeconds -gt $Seconds) { throw $Message }
        Start-Sleep -Milliseconds 100
    }
}
function Start-OwnedApp {
    $process=Start-Process -FilePath $executable -ArgumentList ('--runtime '+$Runtime+' --data-root "'+$root+'"') -WindowStyle Hidden -PassThru
    try {
    Wait-Condition { (Get-ChildItem -Path (Join-Path $root 'sessions\*\launcher.json') -ErrorAction SilentlyContinue | Where-Object { (Get-Content -LiteralPath $_.FullName -Raw | ConvertFrom-Json).pid -eq $process.Id }).Count -eq 1 } 'No launcher identity'
    $identity=Get-ChildItem -Path (Join-Path $root 'sessions\*\launcher.json') | Where-Object { (Get-Content -LiteralPath $_.FullName -Raw | ConvertFrom-Json).pid -eq $process.Id }
    $session=$identity.DirectoryName
    Wait-Condition { Test-Path -LiteralPath (Join-Path $session 'window-ready.json') } ('Desktop did not render: '+$session)
    $ready=Get-Content -LiteralPath (Join-Path $session 'ready.json') -Raw | ConvertFrom-Json
    $backend=Get-Process -Id $ready.pid
    $held=$backend.Handle
    return @{ process=$process; backend=$backend; session=$session; origin=$ready.origin }
    } catch {
        $diagnostic=Join-Path $env:LOCALAPPDATA 'RobotOpsTwin\launcher-error.log'
        if (Test-Path -LiteralPath $diagnostic) { Write-Host (Get-Content -LiteralPath $diagnostic -Raw) }
        if (-not $process.HasExited) { $process.Kill(); $null=$process.WaitForExit(5000) }
        throw
    }
}
function Assert-Exited($App) {
    if (-not $App.process.WaitForExit(25000)) { throw 'Desktop did not stop' }
    if (-not $App.backend.WaitForExit(5000)) { throw 'Backend outlived the desktop' }
    $client=New-Object Net.Sockets.TcpClient
    try {
        $port=([uri]$App.origin).Port
        $pending=$client.ConnectAsync('127.0.0.1',$port)
        try { $null=$pending.Wait(1500) } catch {}
        if ($client.Connected) { throw 'Owned port still accepts connections' }
    } finally { $client.Dispose() }
}
function Begin-BlenderPick($App,[string]$Product) {
    Add-Type -AssemblyName System.Net.Http
    $body=@{order_id=$Product;lines=@(@{order_line_id='line';product_id=$Product;source_id='source';destination_id='destination'})} | ConvertTo-Json -Depth 5
    $order=Invoke-RestMethod -Uri ($App.origin+'/orders') -Method Post -Headers @{'Idempotency-Key'=$Product} -ContentType application/json -Body $body
    $http=New-Object Net.Http.HttpClient
    $content=New-Object Net.Http.StringContent('{}',[Text.Encoding]::UTF8,'application/json')
    $task=$http.PostAsync(($App.origin+'/jobs/'+$order.job_ids[0]+'/run'),$content)
    Wait-Condition { @(Get-CimInstance Win32_Process -Filter ('ParentProcessId='+$App.backend.Id) | Where-Object Name -EQ 'blender.exe').Count -gt 0 } 'No real Blender child started' 15
    $native=Get-CimInstance Win32_Process -Filter ('ParentProcessId='+$App.backend.Id) | Where-Object Name -EQ 'blender.exe' | Select-Object -First 1
    $blender=Get-Process -Id $native.ProcessId
    $held=$blender.Handle
    return @{ client=$http; task=$task; blender=$blender }
}
$record=@{ runtime=$Runtime; source_commit=(git -C $repository rev-parse HEAD); source_dirty=[bool](git -C $repository status --porcelain); checks=@(); data=$root; test_script_sha256=(Get-FileHash -LiteralPath $MyInvocation.MyCommand.Path -Algorithm SHA256).Hash.ToLowerInvariant() }
$first=$null; $second=$null; $third=$null; $fourth=$null
try {
    $first=Start-OwnedApp
    $record.checks+='native window rendered with owned loopback API'
    $count=@(Get-ChildItem -LiteralPath (Join-Path $root 'sessions') -Directory).Count
    $duplicate=Start-Process -FilePath $executable -ArgumentList ('--runtime '+$Runtime+' --data-root "'+$root+'"') -WindowStyle Hidden -PassThru
    if (-not $duplicate.WaitForExit(5000) -or $duplicate.ExitCode -ne 0) { throw 'Duplicate launch did not activate existing instance' }
    if (@(Get-ChildItem -LiteralPath (Join-Path $root 'sessions') -Directory).Count -ne $count) { throw 'Duplicate launch created another backend' }
    $record.checks+='duplicate launch reuses window without new backend'
    $payload=@{order_id='desktop-smoke';lines=@(@{order_line_id='line';product_id='product-red';source_id='source';destination_id='destination'})} | ConvertTo-Json -Depth 5
    $order=Invoke-RestMethod -Uri ($first.origin+'/orders') -Method Post -Headers @{'Idempotency-Key'='desktop-smoke'} -ContentType application/json -Body $payload
    $job=Invoke-RestMethod -Uri ($first.origin+'/jobs/'+$order.job_ids[0]+'/run') -Method Post -ContentType application/json -Body '{"fault":"DROP_ACK_AFTER_EFFECT"}' -TimeoutSec 90
    if ($job.state -ne 'UNKNOWN_OUTCOME') { throw 'Lost acknowledgement did not remain uncertain' }
    if (-not [RobotOpsOwnedWindow]::Close($first.process.Id)) { throw 'No owned desktop window to close' }
    Assert-Exited $first
    $stop=Get-Content -LiteralPath (Join-Path $first.session 'launcher-stopped.json') -Raw | ConvertFrom-Json
    if ($stop.forced) { throw 'Normal close unnecessarily forced the backend' }
    $record.checks+='window close drains backend and releases port'
    $second=Start-OwnedApp
    $recovered=Invoke-RestMethod -Uri ($second.origin+'/jobs/'+$order.job_ids[0])
    if ($recovered.state -ne 'COMPLETED' -or $recovered.command_id -ne $job.command_id) { throw 'Reopen did not safely reconcile the original command' }
    $timeline=Invoke-RestMethod -Uri ($second.origin+'/orders/desktop-smoke/timeline')
    if (@($timeline | Where-Object event_type -EQ 'PICK_EFFECT').Count -ne 1) { throw 'Expected exactly one pick effect' }
    $record.checks+='reopen reconciles original command with exactly one pick'
    $second.process.Kill() # Only the process started by this test; exercise OS job cleanup.
    Assert-Exited $second
    $record.checks+='abrupt desktop termination also stops owned backend'
    $third=Start-OwnedApp
    $thirdJob=Invoke-RestMethod -Uri ($third.origin+'/jobs/'+$order.job_ids[0])
    if ($thirdJob.state -ne 'COMPLETED') { throw 'Persisted result lost after forced close' }
    if ($Runtime -eq 'blender') { $inflight=Begin-BlenderPick $third 'product-blue' }
    if (-not [RobotOpsOwnedWindow]::Close($third.process.Id)) { throw 'Final window close failed' }
    Assert-Exited $third
    $record.checks+='reopen after forced close preserves completed work'
    if ($Runtime -eq 'blender') {
        $response=$inflight.task.GetAwaiter().GetResult()
        $finished=$response.Content.ReadAsStringAsync().GetAwaiter().GetResult() | ConvertFrom-Json
        if ($finished.state -ne 'COMPLETED' -or -not $inflight.blender.WaitForExit(5000)) { throw 'Closing during a real pick did not drain safely' }
        $inflight.client.Dispose()
        $record.checks+='normal window close during a real Blender pick drains it to completion'
        $fourth=Start-OwnedApp
        $interrupted=Begin-BlenderPick $fourth 'product-green'
        $fourth.process.Kill()
        Assert-Exited $fourth
        if (-not $interrupted.blender.WaitForExit(5000)) { throw 'Owned Blender escaped the crashed desktop job' }
        $interrupted.client.Dispose()
        $record.checks+='abrupt close during a real Blender pick terminates its owned process tree'
    }
    $record.passed=$true
} finally {
    foreach ($app in @($first,$second,$third,$fourth)) {
        if ($app -and -not $app.process.HasExited) { $app.process.Kill(); $null=$app.process.WaitForExit(5000) }
    }
    $record | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $root 'evidence.json') -Encoding UTF8
}
$record | ConvertTo-Json -Depth 5
