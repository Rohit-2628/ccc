#!/usr/bin/env python3
"""
Synthetic SSH Git Server for X04 (Broken CI)
Listens on TCP/22 (or configured SSH port).
Supports Git SSH commands ('git-upload-pack', 'git-receive-pack') and interactive status session.
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

STORAGE_ROOT = Path("/tmp/x04_storage")
GIT_DIR = STORAGE_ROOT / "git_repos"
HOST_KEY_FILE = STORAGE_ROOT / "ssh_host_rsa"

def ensure_host_key():
    if not HOST_KEY_FILE.exists():
        if paramiko:
            key = paramiko.RSAKey.generate(2048)
            key.write_private_key_file(str(HOST_KEY_FILE))
    if paramiko and HOST_KEY_FILE.exists():
        return paramiko.RSAKey(filename=str(HOST_KEY_FILE))
    return None

if paramiko:
    class GitSSHInterface(paramiko.ServerInterface):
        def __init__(self):
            self.event = threading.Event()
            self.command = None

        def check_channel_request(self, kind, chanid):
            if kind == "session":
                return paramiko.OPEN_SUCCEEDED
            return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

        def check_auth_password(self, username, password):
            # Accept 'git', 'developer', or any valid challenge role
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
        server = GitSSHInterface()
        t.start_server(server=server)

        chan = t.accept(20)
        if chan is None:
            t.close()
            return

        server.event.wait(10)
        cmd = server.command

        if cmd:
            # Handle git commands: git-upload-pack 'defense-network.git'
            parts = cmd.strip().split()
            git_bin = parts[0]
            repo_arg = parts[1].strip("'\"") if len(parts) > 1 else "defense-network.git"
            repo_name = repo_arg.split("/")[-1]
            if not repo_name.endswith(".git"):
                repo_name += ".git"
            repo_path = GIT_DIR / repo_name

            if git_bin in ["git-upload-pack", "git-receive-pack"] and repo_path.exists():
                proc = subprocess.Popen(
                    [git_bin, str(repo_path)],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )

                def forward_in():
                    while True:
                        try:
                            data = chan.recv(1024)
                            if not data:
                                break
                            proc.stdin.write(data)
                            proc.stdin.flush()
                        except Exception:
                            break
                    try:
                        proc.stdin.close()
                    except Exception:
                        pass

                def forward_out():
                    while True:
                        try:
                            data = proc.stdout.read(1024)
                            if not data:
                                break
                            chan.send(data)
                        except Exception:
                            break

                t_in = threading.Thread(target=forward_in)
                t_out = threading.Thread(target=forward_out)
                t_in.start()
                t_out.start()
                proc.wait()
                t_out.join()
                chan.send_exit_status(proc.returncode)
            else:
                chan.send(f"Latveria Sovereign SSH Gateway: Command '{cmd}' received.\r\n".encode("utf-8"))
                chan.send_exit_status(0)
        else:
            # Interactive shell welcome message
            welcome = (
                "\r\n"
                "====================================================================\r\n"
                "  LATVERIA SOVEREIGN CYBER-INFRASTRUCTURE — GIT SSH GATEWAY (TCP/22)\r\n"
                "====================================================================\r\n"
                "  Available Repositories:\r\n"
                "    - defense-network.git  (Clone: git clone git@target:defense-network.git)\r\n"
                "\r\n"
                "  CI/CD Orchestration:\r\n"
                "    - Web Interface: http://<TARGET>:80/\r\n"
                "    - REST API:      http://<TARGET>:80/api/ci/status\r\n"
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

def run_ssh_server(host="0.0.0.0", port=2222):
    if not paramiko:
        print("[!] Paramiko not installed; SSH Git server running in mock mode.")
        return

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        sock.bind((host, port))
    except Exception as e:
        print(f"[!] Could not bind SSH to {host}:{port}: {e}. Retrying on fallback port 2222...")
        port = 2222
        sock.bind((host, port))

    sock.listen(100)
    print(f"[+] Git SSH Server listening on {host}:{port}")

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
