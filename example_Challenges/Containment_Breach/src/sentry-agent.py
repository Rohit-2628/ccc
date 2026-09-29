#!/usr/bin/env python3
"""
Sentinel IPC Telemetry & Snapshot Agent (sentry-agent)
Stage 2: Background Internal Telemetry Daemon
Listens on /run/sentinel/sentry.sock as user 'sentry'.
"""

import os
import sys
import json
import base64
import socket
import select
import traceback

SOCKET_PATH = "/run/sentinel/sentry.sock"
TOKEN_PATH = "/var/run/sentinel/sentry.token"
SNAPSHOT_DIR = "/var/log/sentinel/snapshots"

def get_auth_token():
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, "r") as f:
            return f.read().strip()
    return "SENTINEL_DEFAULT_LOCAL_TOKEN"

def handle_client(conn, auth_token):
    try:
        raw = conn.recv(65536)
        if not raw:
            return
        
        try:
            req = json.loads(raw.decode("utf-8"))
        except Exception:
            conn.sendall(json.dumps({"status": "error", "message": "Invalid JSON packet"}).encode())
            return

        client_token = req.get("auth_token", "")
        if client_token != auth_token:
            conn.sendall(json.dumps({"status": "error", "message": "Unauthorized: Invalid auth_token"}).encode())
            return

        action = req.get("action", "")

        if action == "ping":
            conn.sendall(json.dumps({"status": "ok", "message": "pong"}).encode())

        elif action == "status":
            conn.sendall(json.dumps({
                "status": "ok",
                "service": "sentry-agent",
                "user": "sentry",
                "snapshot_dir": SNAPSHOT_DIR
            }).encode())

        elif action == "save_snapshot":
            filename = req.get("filename", "default.log")
            raw_data = req.get("data", "")
            is_b64 = req.get("base64", False)

            if is_b64:
                try:
                    payload_bytes = base64.b64decode(raw_data)
                except Exception as e:
                    conn.sendall(json.dumps({"status": "error", "message": f"Base64 decode failed: {e}"}).encode())
                    return
            else:
                payload_bytes = raw_data.encode("utf-8")

            # Vulnerable path resolution: os.path.join ignores base if filename starts with '/'
            target_path = os.path.normpath(os.path.join(SNAPSHOT_DIR, filename))
            
            # Ensure parent dir exists
            parent_dir = os.path.dirname(target_path)
            if parent_dir and not os.path.exists(parent_dir):
                os.makedirs(parent_dir, mode=0o755, exist_ok=True)

            with open(target_path, "wb") as f:
                f.write(payload_bytes)

            try:
                os.chmod(target_path, 0o600)
            except Exception:
                pass

            conn.sendall(json.dumps({
                "status": "ok",
                "message": f"Snapshot archived successfully",
                "path": target_path,
                "bytes_written": len(payload_bytes)
            }).encode())

        else:
            conn.sendall(json.dumps({"status": "error", "message": f"Unknown action: {action}"}).encode())

    except Exception as e:
        traceback.print_exc()
        try:
            conn.sendall(json.dumps({"status": "error", "message": str(e)}).encode())
        except Exception:
            pass
    finally:
        conn.close()

def run_server():
    os.makedirs(os.path.dirname(SOCKET_PATH), exist_ok=True)
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)

    if os.path.exists(SOCKET_PATH):
        os.remove(SOCKET_PATH)

    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(SOCKET_PATH)
    server.listen(16)

    # Allow group sentinel-users to access socket
    try:
        os.chmod(SOCKET_PATH, 0o660)
    except Exception:
        pass

    auth_token = get_auth_token()
    print(f"[sentry-agent] Listening on {SOCKET_PATH} (auth token loaded)")
    sys.stdout.flush()

    while True:
        try:
            conn, _ = server.accept()
            handle_client(conn, auth_token)
        except Exception as e:
            traceback.print_exc()

if __name__ == "__main__":
    run_server()
