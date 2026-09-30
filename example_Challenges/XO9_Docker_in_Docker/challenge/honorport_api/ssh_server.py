#!/usr/bin/env python3
"""
Synthetic SSH Gateway Server for XO-9 (Honorport Heist - Docker in Docker)
Listens on TCP/22 (or configured SSH port, e.g. SSH_PORT env var).
Provides interactive terminal access and command execution over SSH.
"""

import os
import sys
import socket
import threading
import subprocess
from pathlib import Path

try:
    import paramiko
except ImportError:
    paramiko = None

STORAGE_ROOT = Path("/tmp/xo9_storage")
HOST_KEY_FILE = STORAGE_ROOT / "ssh_host_rsa"

def ensure_host_key():
    if not HOST_KEY_FILE.exists():
        if paramiko:
            os.makedirs(STORAGE_ROOT, exist_ok=True)
            key = paramiko.RSAKey.generate(2048)
            key.write_private_key_file(str(HOST_KEY_FILE))
    if paramiko and HOST_KEY_FILE.exists():
        return paramiko.RSAKey(filename=str(HOST_KEY_FILE))
    return None

if paramiko:
    class HonorportSSHInterface(paramiko.ServerInterface):
        def __init__(self):
            self.event = threading.Event()
            self.command = None

        def check_channel_request(self, kind, chanid):
            if kind == "session":
                return paramiko.OPEN_SUCCEEDED
            return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

        def check_auth_password(self, username, password):
            return paramiko.AUTH_SUCCESSFUL

        def check_auth_publickey(self, username, key):
            return paramiko.AUTH_SUCCESSFUL

        def check_auth_none(self, username):
            return paramiko.AUTH_SUCCESSFUL

        def get_allowed_auths(self, username):
            return "password,publickey,none"

        def check_channel_exec_request(self, channel, command):
            self.command = command.decode("utf-8", errors="ignore")
            self.event.set()
            return True

        def check_channel_shell_request(self, channel):
            self.event.set()
            return True

        def check_channel_pty_request(self, channel, term, width, height, pixelwidth, pixelheight, modes):
            return True

def handle_client(client_sock):
    if not paramiko:
        client_sock.close()
        return

    try:
        t = paramiko.Transport(client_sock)
        host_key = ensure_host_key()
        if not host_key:
            client_sock.close()
            return
        t.add_server_key(host_key)
        server = HonorportSSHInterface()
        t.start_server(server=server)

        chan = t.accept(20)
        if chan is None:
            t.close()
            return

        server.event.wait(10)
        cmd = server.command

        if cmd:
            env = os.environ.copy()
            env["DOCKER_HOST"] = "tcp://127.0.0.1:2375"
            try:
                proc = subprocess.run(
                    cmd,
                    shell=True,
                    executable="/bin/bash",
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=15
                )
                output = proc.stdout + proc.stderr
                chan.send(output.encode("utf-8"))
                chan.send_exit_status(proc.returncode)
            except Exception as e:
                chan.send(f"Execution Error: {e}\r\n".encode("utf-8"))
                chan.send_exit_status(1)
        else:
            welcome = (
                "\r\n"
                "====================================================================\r\n"
                "  HONORPORT LOGISTICS — SECURE SSH GATEWAY (TCP/22)\r\n"
                "====================================================================\r\n"
                "  Sovereign Harbor Master & Container Deployment Terminal\r\n"
                "  DOCKER_HOST=tcp://127.0.0.1:2375\r\n"
                "====================================================================\r\n\r\n"
            )
            chan.send(welcome.encode("utf-8"))
            chan.close()

    except Exception as e:
        pass
    finally:
        try:
            t.close()
        except Exception:
            pass

def run_ssh_server(host="0.0.0.0", port=22):
    if not paramiko:
        print("[!] Paramiko not installed; SSH server running in mock mode.")
        return

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    for p in [port, 2222, 2223, 2224]:
        try:
            sock.bind((host, p))
            port = p
            break
        except Exception:
            continue

    try:
        sock.listen(100)
        print(f"[+] Honorport SSH Gateway Server listening on {host}:{port}")
    except Exception as e:
        print(f"[!] SSH server failed to listen: {e}")
        return

    while True:
        try:
            client, addr = sock.accept()
            th = threading.Thread(target=handle_client, args=(client,), daemon=True)
            th.start()
        except Exception:
            pass

if __name__ == "__main__":
    p = int(sys.argv[1]) if len(sys.argv) > 1 else int(os.environ.get("SSH_PORT", 22))
    run_ssh_server(port=p)
