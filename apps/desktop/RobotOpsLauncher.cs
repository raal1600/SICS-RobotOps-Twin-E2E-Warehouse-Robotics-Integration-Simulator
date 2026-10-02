using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Drawing;
using System.IO;
using System.Reflection;
using System.Security.Cryptography;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using System.Web.Script.Serialization;
using System.Windows.Forms;
using Microsoft.Web.WebView2.Core;
using Microsoft.Web.WebView2.WinForms;

[assembly: AssemblyTitle("RobotOps Twin")]
[assembly: AssemblyVersion("1.0.0.0")]
[assembly: System.Runtime.Versioning.TargetFramework(".NETFramework,Version=v4.8")]
internal static class Launcher {
    [STAThread] static int Main(string[] args) {
        Application.EnableVisualStyles(); Application.SetCompatibleTextRenderingDefault(false);
        try {
            var json = new JavaScriptSerializer();
            string folder = AppDomain.CurrentDomain.BaseDirectory;
            var config = json.Deserialize<Dictionary<string,string>>(File.ReadAllText(Path.Combine(folder, "launcher.json")));
            string data = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "RobotOpsTwin");
            string runtime = "blender";
            for (int i=0; i<args.Length; i+=2) {
                if (i+1 == args.Length) throw new ArgumentException("Missing launcher argument.");
                if (args[i] == "--data-root") data=Path.GetFullPath(args[i+1]);
                else if (args[i] == "--runtime" && (args[i+1] == "blender" || args[i+1] == "headless")) runtime=args[i+1];
                else throw new ArgumentException("Unknown launcher argument: " + args[i]);
            }
            string key;
            using (var hash = SHA256.Create()) key=BitConverter.ToString(hash.ComputeHash(Encoding.UTF8.GetBytes(Path.GetFullPath(data).ToLowerInvariant()))).Replace("-", "");
            bool first;
            using (var mutex = new Mutex(true, "Local\\RobotOpsTwin-" + key, out first))
            using (var activate = new EventWaitHandle(false, EventResetMode.AutoReset, "Local\\RobotOpsTwinActivate-" + key)) {
                if (!first) { activate.Set(); return 0; }
                string profile=Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),"RobotOpsTwin","WebView2",key.Substring(0,32));
                Application.Run(new Desktop(config, data, runtime, activate, profile));
            }
            return 0;
        } catch (Exception error) {
            try {
                string logs=Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),"RobotOpsTwin");
                Directory.CreateDirectory(logs);
                File.WriteAllText(Path.Combine(logs,"launcher-error.log"),error.ToString());
            } catch { }
            MessageBox.Show(error.Message, "RobotOps Twin could not start", MessageBoxButtons.OK, MessageBoxIcon.Error);
            return 1;
        }
    }
}

internal sealed class Desktop : Form {
    readonly Dictionary<string,string> config;
    readonly string data, runtime, sessionId, session, profile;
    readonly WebView2 view = new WebView2();
    readonly Label status = new Label();
    readonly System.Windows.Forms.Timer timer = new System.Windows.Forms.Timer();
    readonly CancellationTokenSource cancellation = new CancellationTokenSource();
    readonly EventWaitHandle activate;
    readonly JavaScriptSerializer json = new JavaScriptSerializer();
    OwnedProcess child;
    string origin;
    bool closing, allowClose;

    public Desktop(Dictionary<string,string> configuration, string dataRoot, string mode, EventWaitHandle signal, string browserProfile) {
        config=configuration; data=dataRoot; runtime=mode; activate=signal; profile=browserProfile;
        sessionId=Guid.NewGuid().ToString("N");
        session=Path.Combine(data, "sessions", DateTime.UtcNow.ToString("yyyyMMddTHHmmss") + "-" + sessionId);
        Directory.CreateDirectory(session);
        Text="RobotOps Twin"; Width=1320; Height=900; MinimumSize=new Size(900,640);
        StartPosition=FormStartPosition.CenterScreen;
        Icon=Icon.ExtractAssociatedIcon(Assembly.GetExecutingAssembly().Location);
        status.Dock=DockStyle.Fill; status.TextAlign=ContentAlignment.MiddleCenter;
        status.Font=new Font("Segoe UI",12); status.Text="Starting RobotOps Twin...";
        view.Dock=DockStyle.Fill; Controls.Add(view); Controls.Add(status);
        timer.Interval=500;
        timer.Tick+=(s,e)=>{
            if (activate.WaitOne(0)) { WindowState=FormWindowState.Normal; Show(); Activate(); }
            if (!closing && child != null && child.Process.HasExited) {
                status.Text="The simulator stopped. Close this window and reopen RobotOps Twin.\n\nLogs: " + session;
                status.Visible=true; status.BringToFront(); view.Enabled=false;
            }
        };
        timer.Start();
        Shown+=async(s,e)=>await Start();
        FormClosing+=async(s,e)=>{ if (allowClose) return; e.Cancel=true; if (!closing) await Stop(); };
        FormClosed+=(s,e)=>{ timer.Dispose(); view.Dispose(); if (child != null) child.Dispose(); cancellation.Dispose(); };
    }

    async Task Start() {
        try {
            string repository=Path.GetFullPath(config["repository"]), python=Path.GetFullPath(config["python"]);
            if (!File.Exists(python) || !File.Exists(Path.Combine(repository, "apps/desktop/backend.py")))
                throw new FileNotFoundException("The local project or Python environment is missing. Rebuild the launcher after restoring the project.");
            child=new OwnedProcess(python, new[] { "-u", "-m", "apps.desktop.backend", "--runtime", runtime,
                "--data-dir", Path.Combine(data,"data"), "--session-dir", session, "--session-id", sessionId },
                repository, Path.Combine(session,"server.log"));
            File.WriteAllText(Path.Combine(session,"launcher.json"),json.Serialize(new { pid=Process.GetCurrentProcess().Id, backend_pid=child.Process.Id, session_id=sessionId }));
            var clock=Stopwatch.StartNew();
            while (!File.Exists(Path.Combine(session,"ready.json"))) {
                cancellation.Token.ThrowIfCancellationRequested();
                if (child.Process.HasExited || clock.Elapsed.TotalSeconds > 45)
                    throw new InvalidOperationException("The simulator could not start. See " + Path.Combine(session,"server.log"));
                await Task.Delay(100,cancellation.Token);
            }
            cancellation.Token.ThrowIfCancellationRequested();
            var ready=json.Deserialize<Dictionary<string,object>>(File.ReadAllText(Path.Combine(session,"ready.json")));
            if (Convert.ToString(ready["session_id"]) != sessionId) throw new InvalidDataException("Unexpected backend session.");
            Uri address;
            origin=Convert.ToString(ready["origin"]);
            if (!Uri.TryCreate(origin,UriKind.Absolute,out address) || address.Scheme != "http" || address.Host != "127.0.0.1" || address.Port <= 0)
                throw new InvalidDataException("Backend must bind an owned loopback port.");
            // Chromium profile paths stay short even for long checkout/data roots.
            var environment=await CoreWebView2Environment.CreateAsync(null,profile);
            cancellation.Token.ThrowIfCancellationRequested();
            await view.EnsureCoreWebView2Async(environment);
            cancellation.Token.ThrowIfCancellationRequested();
            view.CoreWebView2.Settings.AreDevToolsEnabled=false;
            view.CoreWebView2.Settings.AreDefaultContextMenusEnabled=false;
            view.CoreWebView2.Settings.IsWebMessageEnabled=false;
            view.CoreWebView2.PermissionRequested+=(s,e)=>e.State=CoreWebView2PermissionState.Deny;
            view.CoreWebView2.NewWindowRequested+=(s,e)=>{ e.Handled=true; OpenLink(e.Uri); };
            view.CoreWebView2.NavigationStarting+=(s,e)=>{ if (!IsLocal(e.Uri)) { e.Cancel=true; OpenLink(e.Uri); } };
            view.CoreWebView2.NavigationCompleted+=(s,e)=>{
                if (closing) return;
                status.Visible=!e.IsSuccess;
                if (e.IsSuccess) File.WriteAllText(Path.Combine(session,"window-ready.json"), json.Serialize(new { session_id=sessionId, origin=origin }));
                else status.Text="Unable to display the dashboard. Close and reopen RobotOps Twin.";
            };
            view.Source=new Uri(origin+"/");
        } catch (OperationCanceledException) {
            // Closing during startup follows the same owned-process shutdown path.
        } catch (Exception error) {
            if (!closing) {
                if (child != null) { child.Dispose(); child=null; }
                status.Text="RobotOps Twin could not open.\n\n" + error.Message;
                File.WriteAllText(Path.Combine(session,"startup-error.log"),error.ToString());
            }
        }
    }

    bool IsLocal(string value) {
        Uri uri;
        return Uri.TryCreate(value,UriKind.Absolute,out uri) && uri.GetLeftPart(UriPartial.Authority)==origin;
    }
    void OpenLink(string value) {
        Uri uri;
        if (Uri.TryCreate(value,UriKind.Absolute,out uri) && (uri.Scheme=="https" || IsLocal(value)))
            Process.Start(new ProcessStartInfo(value) { UseShellExecute=true });
    }
    async Task Stop() {
        closing=true; cancellation.Cancel(); timer.Stop(); view.Enabled=false;
        status.Text="Stopping RobotOps Twin...\nFinishing the current operation and saving evidence.";
        status.Visible=true; status.BringToFront();
        try {
            File.WriteAllText(Path.Combine(session,"stop"),sessionId);
            if (child != null) {
                var owned=child;
                bool drained=await Task.Run(()=>owned.Process.WaitForExit(20000));
                File.WriteAllText(Path.Combine(session,"launcher-stopped.json"),json.Serialize(new { session_id=sessionId, backend_exited=drained, forced=!drained }));
                child.Dispose(); child=null; // Also closes lingering owned Blender children.
            }
        } finally {
            if (child != null) { child.Dispose(); child=null; }
            view.Dispose(); allowClose=true; Close();
        }
    }
}
