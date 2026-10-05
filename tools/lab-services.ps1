<#
Portable, task-scoped PostgreSQL and RabbitMQ for Windows integration tests.
No Windows services, system PATH edits, reboot, or administrator installation.
All binaries and durable data stay under ignored artifacts/ by default.
#>
[CmdletBinding()]
param(
    [ValidateSet('Install', 'Start', 'Stop', 'Status')]
    [string]$Action = 'Status',
    [string]$DataRoot = '',
    [ValidateRange(1024, 65535)]
    [int]$PostgresPort = 5432,
    [ValidateRange(1024, 45535)]
    [int]$RabbitPort = 5672
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$toolRoot = Join-Path $repoRoot 'artifacts\lab-tools'
if (-not $DataRoot) { $DataRoot = Join-Path $repoRoot 'artifacts\lab-services' }
$DataRoot = [IO.Path]::GetFullPath($DataRoot)
$postgresBin = Join-Path $toolRoot 'pgsql\bin'
$postgresData = Join-Path $DataRoot 'postgres-data'
$rabbitBase = Join-Path $DataRoot 'rabbitmq'
$rabbitBin = Join-Path $toolRoot 'rabbitmq_server-4.3.6\sbin'
$erlangRoot = Join-Path $toolRoot 'erlang'
$nodeName = 'robotopslab@localhost'

# Digests are pinned to the official release archives linked in the documentation.
$archives = @(
    @{
        File = 'postgresql.zip'
        Url = 'https://get.enterprisedb.com/postgresql/postgresql-17.11-1-windows-x64-binaries.zip'
        Hash = '6EABDF00D2893713B75DB4336A23C3FDF505F056E217EC6E2E95D901750CFEA3'
        Target = $toolRoot
        Probe = (Join-Path $postgresBin 'pg_ctl.exe')
    },
    @{
        File = 'erlang.zip'
        Url = 'https://github.com/erlang/otp/releases/download/OTP-27.3.4.18/otp_win64_27.3.4.18.zip'
        Hash = '2AF5D35D521211C16E9FA31B23F76E44B7B3284A27C6C1295FBEB382D2FF211F'
        Target = $erlangRoot
        Probe = (Join-Path $erlangRoot 'bin\erl.exe')
    },
    @{
        File = 'rabbitmq.zip'
        Url = 'https://github.com/rabbitmq/rabbitmq-server/releases/download/v4.3.6/rabbitmq-server-windows-4.3.6.zip'
        Hash = '48161B084F1257EDC112B24FCCDA378CC3E83C8E4B94984801CD6651817981F1'
        Target = $toolRoot
        Probe = (Join-Path $rabbitBin 'rabbitmq-server.bat')
    }
)

function Install-LabTools {
    $downloadRoot = Join-Path $toolRoot 'downloads'
    New-Item -ItemType Directory -Path $downloadRoot -Force | Out-Null
    foreach ($archive in $archives) {
        $archivePath = Join-Path $downloadRoot $archive.File
        if (-not (Test-Path -LiteralPath $archivePath)) {
            Write-Host ('Downloading ' + $archive.File)
            & curl.exe --fail --location --retry 3 --silent --show-error --output $archivePath $archive.Url
            if ($LASTEXITCODE -ne 0) { throw ('Download failed: ' + $archive.File) }
        }
        if ((Get-FileHash -Algorithm SHA256 -LiteralPath $archivePath).Hash -ne $archive.Hash) {
            throw ('Archive checksum mismatch: ' + $archivePath)
        }
        if (-not (Test-Path -LiteralPath $archive.Probe)) {
            New-Item -ItemType Directory -Path $archive.Target -Force | Out-Null
            & tar.exe -xf $archivePath -C $archive.Target
            if ($LASTEXITCODE -ne 0) { throw ('Extraction failed: ' + $archive.File) }
        }
    }
}

function Set-RabbitEnvironment {
    # These assignments affect only this process and its children.
    $env:ERLANG_HOME = $erlangRoot
    $env:ERL_EPMD_ADDRESS = '127.0.0.1'
    $env:RABBITMQ_BASE = $rabbitBase
    $env:RABBITMQ_NODENAME = $nodeName
    $env:RABBITMQ_CONFIG_FILE = Join-Path $rabbitBase 'rabbitmq'
    $env:RABBITMQ_SERVER_ADDITIONAL_ERL_ARGS = '+S 2:2'
}

function Test-LocalPort([int]$Port) {
    $client = [Net.Sockets.TcpClient]::new()
    try {
        $connect = $client.ConnectAsync('127.0.0.1', $Port)
        if (-not $connect.Wait(1000)) { return $false }
        return $client.Connected
    } catch { return $false } finally { $client.Dispose() }
}

function Show-LabStatus {
    [pscustomobject]@{
        postgres = Test-LocalPort $PostgresPort
        rabbitmq = Test-LocalPort $RabbitPort
        postgres_port = $PostgresPort
        rabbitmq_port = $RabbitPort
        data_root = $DataRoot
        scope = 'TCP readiness only; run the documented SQL/AMQP smoke test for protocol evidence'
    } | ConvertTo-Json
}

if ($Action -eq 'Install') { Install-LabTools; exit 0 }
if ($Action -eq 'Status') { Show-LabStatus; exit 0 }
Set-RabbitEnvironment

if ($Action -eq 'Stop') {
    # pg_ctl addresses only the exact task data directory. No recursive data deletion.
    if (Test-Path -LiteralPath (Join-Path $postgresData 'postmaster.pid')) {
        & (Join-Path $postgresBin 'pg_ctl.exe') -D $postgresData -m fast -w stop
        if ($LASTEXITCODE -ne 0) { throw 'PostgreSQL did not stop cleanly' }
    }
    if ((Test-Path -LiteralPath (Join-Path $DataRoot 'rabbitmq-launcher.pid')) -and (Test-LocalPort $RabbitPort)) {
        & (Join-Path $rabbitBin 'rabbitmqctl.bat') -n $nodeName stop
        if ($LASTEXITCODE -ne 0) { throw 'RabbitMQ did not stop cleanly' }
    }
    Show-LabStatus
    exit 0
}

if (-not (Test-Path -LiteralPath (Join-Path $postgresBin 'pg_ctl.exe')) -or
    -not (Test-Path -LiteralPath (Join-Path $erlangRoot 'bin\erl.exe')) -or
    -not (Test-Path -LiteralPath (Join-Path $rabbitBin 'rabbitmq-server.bat'))) {
    Install-LabTools
}
New-Item -ItemType Directory -Path $DataRoot -Force | Out-Null

if (-not (Test-Path -LiteralPath (Join-Path $postgresData 'PG_VERSION'))) {
    if (Test-LocalPort $PostgresPort) { throw 'PostgreSQL port occupied; refusing to initialize a second owner' }
    $passwordFile = Join-Path $DataRoot 'postgres-init-password.txt'
    # Deliberately public, local synthetic-lab credential, not a production secret.
    'demo-only' | Set-Content -LiteralPath $passwordFile -Encoding ASCII
    try {
        & (Join-Path $postgresBin 'initdb.exe') -D $postgresData -U robotops --pwfile=$passwordFile -A scram-sha-256 -E UTF8 --locale=C
        if ($LASTEXITCODE -ne 0) { throw 'PostgreSQL initialization failed' }
    } finally { Remove-Item -LiteralPath $passwordFile -ErrorAction SilentlyContinue }
    @"
listen_addresses = '127.0.0.1'
port = $PostgresPort
max_connections = 60
shared_buffers = '32MB'
"@ | Add-Content -LiteralPath (Join-Path $postgresData 'postgresql.conf') -Encoding ASCII
}
if (-not (Test-LocalPort $PostgresPort)) {
    $postgresArgs = @('-D', ('"' + $postgresData + '"'), '-l', ('"' + (Join-Path $DataRoot 'postgres.log') + '"'), '-w', 'start')
    $pgLaunch = Start-Process -FilePath (Join-Path $postgresBin 'pg_ctl.exe') -ArgumentList $postgresArgs -WindowStyle Hidden -PassThru
    # Wait only for pg_ctl, not its deliberately long-lived postgres descendants.
    if (-not $pgLaunch.WaitForExit(50000)) { throw 'PostgreSQL startup observation timed out; inspect postgres.log and process before retrying' }
    if ($pgLaunch.ExitCode -ne 0) { throw 'PostgreSQL startup failed; inspect postgres.log' }
}
$env:PGPASSWORD = 'demo-only'
$serverData = & (Join-Path $postgresBin 'psql.exe') -h 127.0.0.1 -p $PostgresPort -U robotops -d postgres -tAc "SHOW data_directory"
if ($LASTEXITCODE -ne 0) { throw 'PostgreSQL authentication failed' }
if ([IO.Path]::GetFullPath($serverData.Trim()).TrimEnd('\') -ne $postgresData.TrimEnd('\')) {
    throw 'PostgreSQL endpoint belongs to a different data directory; refusing to mutate it'
}
$existing = & (Join-Path $postgresBin 'psql.exe') -h 127.0.0.1 -p $PostgresPort -U robotops -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='robotops'"
if ($LASTEXITCODE -ne 0) { throw 'PostgreSQL authentication failed' }
if ($existing -ne '1') {
    & (Join-Path $postgresBin 'createdb.exe') -h 127.0.0.1 -p $PostgresPort -U robotops robotops
    if ($LASTEXITCODE -ne 0) { throw 'Lab database creation failed' }
}

if (-not (Test-LocalPort $RabbitPort)) {
    New-Item -ItemType Directory -Path $rabbitBase -Force | Out-Null
    @"
listeners.tcp.1 = 127.0.0.1:$RabbitPort
distribution.listener.interface = 127.0.0.1
default_user = guest
default_pass = guest
"@ | Set-Content -LiteralPath (Join-Path $rabbitBase 'rabbitmq.conf') -Encoding ASCII
    $rabbitBatch = Join-Path $rabbitBin 'rabbitmq-server.bat'
    $rabbitLaunch = Start-Process -FilePath $env:ComSpec -ArgumentList @('/d', '/c', ('"' + $rabbitBatch + '"')) -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $DataRoot 'rabbitmq.stdout.log') -RedirectStandardError (Join-Path $DataRoot 'rabbitmq.stderr.log')
    $rabbitLaunch.Id | Set-Content -LiteralPath (Join-Path $DataRoot 'rabbitmq-launcher.pid') -Encoding ASCII
    $deadline = [DateTime]::UtcNow.AddSeconds(50)
    while (-not (Test-LocalPort $RabbitPort)) {
        if ($rabbitLaunch.HasExited -or [DateTime]::UtcNow -gt $deadline) {
            throw 'RabbitMQ startup failed; inspect rabbitmq stdout/stderr logs'
        }
        Start-Sleep -Milliseconds 300
    }
}
& (Join-Path $rabbitBin 'rabbitmq-diagnostics.bat') -q -n $nodeName ping
if ($LASTEXITCODE -ne 0) { throw 'RabbitMQ endpoint is not the expected task node, or its control channel is not ready' }
Show-LabStatus
