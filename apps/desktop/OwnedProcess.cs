// A private Windows Job Object owns only this launcher's backend and descendants.
// Start suspended, assign before execution, then resume: no child-spawn race.
using System;
using System.ComponentModel;
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Text;

internal sealed class OwnedProcess : IDisposable {
    IntPtr job;
    public Process Process { get; private set; }

    [StructLayout(LayoutKind.Sequential)] struct BasicLimits {
        public long ProcessTime, JobTime;
        public uint Flags;
        public UIntPtr MinWorkingSet, MaxWorkingSet;
        public uint ActiveProcesses;
        public UIntPtr Affinity;
        public uint Priority, Scheduling;
    }
    [StructLayout(LayoutKind.Sequential)] struct IoCounters {
        public ulong ReadOps, WriteOps, OtherOps, ReadBytes, WriteBytes, OtherBytes;
    }
    [StructLayout(LayoutKind.Sequential)] struct ExtendedLimits {
        public BasicLimits Basic;
        public IoCounters Io;
        public UIntPtr ProcessMemory, JobMemory, PeakProcessMemory, PeakJobMemory;
    }
    [StructLayout(LayoutKind.Sequential)] struct Security {
        public int Length;
        public IntPtr Descriptor;
        [MarshalAs(UnmanagedType.Bool)] public bool Inherit;
    }
    [StructLayout(LayoutKind.Sequential, CharSet=CharSet.Unicode)] struct Startup {
        public int Size;
        public string Reserved, Desktop, Title;
        public uint X, Y, Width, Height, XChars, YChars, Fill, Flags;
        public short Show, ReservedSize;
        public IntPtr ReservedBytes, Input, Output, Error;
    }
    [StructLayout(LayoutKind.Sequential)] struct ProcessInfo {
        public IntPtr Process, Thread;
        public uint ProcessId, ThreadId;
    }
    [DllImport("kernel32.dll", SetLastError=true)] static extern IntPtr CreateJobObject(IntPtr attributes, string name);
    [DllImport("kernel32.dll", SetLastError=true)] static extern bool SetInformationJobObject(IntPtr job, int kind, ref ExtendedLimits limits, uint size);
    [DllImport("kernel32.dll", SetLastError=true)] static extern bool AssignProcessToJobObject(IntPtr job, IntPtr process);
    [DllImport("kernel32.dll", SetLastError=true, CharSet=CharSet.Unicode)] static extern bool CreateProcess(string executable, StringBuilder command, IntPtr processAttributes, IntPtr threadAttributes, bool inheritHandles, uint flags, IntPtr environment, string directory, ref Startup startup, out ProcessInfo info);
    [DllImport("kernel32.dll", SetLastError=true, CharSet=CharSet.Unicode)] static extern IntPtr CreateFile(string path, uint access, uint sharing, ref Security attributes, uint disposition, uint flags, IntPtr template);
    [DllImport("kernel32.dll", SetLastError=true)] static extern uint ResumeThread(IntPtr thread);
    [DllImport("kernel32.dll", SetLastError=true)] static extern bool TerminateProcess(IntPtr process, uint exitCode);
    [DllImport("kernel32.dll")] static extern bool CloseHandle(IntPtr handle);

    internal static string Quote(string value) {
        // Windows CommandLineToArgvW quoting, including trailing backslashes.
        var text = new StringBuilder("\"");
        int slashes = 0;
        foreach (char ch in value) {
            if (ch == '\\') { slashes++; continue; }
            if (ch == '"') { text.Append('\\', slashes * 2 + 1); text.Append(ch); }
            else { text.Append('\\', slashes); text.Append(ch); }
            slashes = 0;
        }
        text.Append('\\', slashes * 2); text.Append('"'); return text.ToString();
    }

    public OwnedProcess(string executable, string[] arguments, string directory, string log) {
        IntPtr output = IntPtr.Zero, input = IntPtr.Zero;
        var info = new ProcessInfo();
        try {
            job = CreateJobObject(IntPtr.Zero, null);
            if (job == IntPtr.Zero) throw new Win32Exception();
            var limits = new ExtendedLimits();
            limits.Basic.Flags = 0x2000; // JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            if (!SetInformationJobObject(job, 9, ref limits, (uint)Marshal.SizeOf(limits))) throw new Win32Exception();
            var security = new Security { Length=Marshal.SizeOf(typeof(Security)), Inherit=true };
            output = CreateFile(log, 0x40000000, 3, ref security, 2, 0x80, IntPtr.Zero);
            input = CreateFile("NUL", 0x80000000, 3, ref security, 3, 0x80, IntPtr.Zero);
            if (output == new IntPtr(-1) || input == new IntPtr(-1)) throw new Win32Exception();
            var startup = new Startup { Size=Marshal.SizeOf(typeof(Startup)), Flags=0x100, Input=input, Output=output, Error=output };
            var command = new StringBuilder(Quote(executable));
            foreach (string arg in arguments) command.Append(" ").Append(Quote(arg));
            if (!CreateProcess(executable, command, IntPtr.Zero, IntPtr.Zero, true, 0x08000004, IntPtr.Zero, directory, ref startup, out info)) throw new Win32Exception();
            if (!AssignProcessToJobObject(job, info.Process)) throw new Win32Exception();
            Process = Process.GetProcessById((int)info.ProcessId);
            // Hold the real process handle, so a recycled PID cannot substitute another process.
            IntPtr held = Process.Handle;
            if (ResumeThread(info.Thread) == UInt32.MaxValue) throw new Win32Exception();
        } catch {
            if (info.Process != IntPtr.Zero) TerminateProcess(info.Process, 1);
            Dispose(); throw;
        } finally {
            foreach (IntPtr handle in new[] { output, input, info.Thread, info.Process })
                if (handle != IntPtr.Zero && handle != new IntPtr(-1)) CloseHandle(handle);
        }
    }
    public void Dispose() {
        if (job != IntPtr.Zero) { CloseHandle(job); job=IntPtr.Zero; }
        if (Process != null) { Process.Dispose(); Process=null; }
    }
}
