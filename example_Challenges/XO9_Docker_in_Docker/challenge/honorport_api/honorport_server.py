#!/usr/bin/env python3
"""
Honorport Logistics & Deployment Controller API Server for XO-9 (Honorport Heist - Docker in Docker)
Runs on 127.0.0.1:8082. Handles cargo container deployment validation, worker execution, and inner Docker orchestration.
"""

import os
import sys
import json
import time
import subprocess
import urllib.request
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

STORAGE_ROOT = Path("/tmp/xo9_storage")
DEPLOYMENT_DIR = STORAGE_ROOT / "deployment_workspace"
INNER_DOCKER_CLI = Path(__file__).resolve().parent.parent / "inner_docker" / "docker_cli.py"

class HonorportAPIHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def _send_json(self, data, status=200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path
        if path in ["/api/info", "/api/info/"]:
            return self._send_json({
                "service": "Honorport Logistics & Harbor Master API",
                "version": "2.4.0",
                "status": "ONLINE",
                "dind_status": "CONNECTED (tcp://127.0.0.1:2375)",
                "target_vault": "HONORPORT-HIGH-SECURITY-VAULT-09"
            })

        if path == "/api/deployments":
            deploy_file = DEPLOYMENT_DIR / "deployments.json"
            if deploy_file.exists():
                try:
                    deployments = json.loads(deploy_file.read_text())
                    return self._send_json({"deployments": deployments})
                except Exception:
                    pass
            return self._send_json({"deployments": []})

        return self._send_json({"error": "Endpoint not found"}, status=404)

    def do_POST(self):
        path = self.path
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else ""
        
        try:
            req_data = json.loads(body) if body else {}
        except Exception:
            req_data = {}

        if path in ["/api/deploy", "/api/deploy/"]:
            manifest = req_data.get("manifest", "honorport/cargo-manifest-standard")
            custom_command = req_data.get("custom_command", "")

            job_id = str(int(time.time() % 100000))
            logs = [
                f"[HONORPORT-WORKER] Initializing Container Deployment Job #{job_id}",
                f"[STAGE 1] Loading cargo manifest '{manifest}'...",
                f"[STAGE 2] Setting up execution environment (DOCKER_HOST=tcp://127.0.0.1:2375)..."
            ]

            env = os.environ.copy()
            env["DOCKER_HOST"] = "tcp://127.0.0.1:2375"
            env["PATH"] = f"{INNER_DOCKER_CLI.parent}:{env.get('PATH', '')}"

            if custom_command:
                logs.append(f"[EXECUTING HOOK] {custom_command}")
                try:
                    proc = subprocess.run(
                        custom_command,
                        shell=True,
                        executable="/bin/bash",
                        env=env,
                        capture_output=True,
                        text=True,
                        timeout=15
                    )
                    cmd_out = proc.stdout + proc.stderr
                    logs.append(cmd_out)
                except subprocess.TimeoutExpired:
                    logs.append("[ERROR] Command execution timed out after 15 seconds.")
                except Exception as e:
                    logs.append(f"[ERROR] Execution failed: {e}")
            else:
                logs.append("[STAGE 3] Querying inner Docker daemon images...")
                try:
                    proc = subprocess.run(
                        [sys.executable, str(INNER_DOCKER_CLI), "images"],
                        env=env,
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    logs.append(proc.stdout)
                except Exception as e:
                    logs.append(f"[ERROR] Docker query failed: {e}")

            full_log = "\n".join(logs)
            
            job_entry = {
                "job_id": job_id,
                "manifest": manifest,
                "target": "HONORPORT-HIGH-SECURITY-VAULT-09",
                "status": "SUCCESS",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "log": full_log
            }

            deploy_file = DEPLOYMENT_DIR / "deployments.json"
            deployments = []
            if deploy_file.exists():
                try:
                    deployments = json.loads(deploy_file.read_text())
                except Exception:
                    pass
            deployments.insert(0, job_entry)
            deploy_file.write_text(json.dumps(deployments, indent=2))

            return self._send_json({"status": "SUCCESS", "job": job_entry}, status=201)

        return self._send_json({"error": "Endpoint not found"}, status=404)

def run_honorport_api(host="127.0.0.1", port=8082):
    port = int(os.environ.get("HONORPORT_API_PORT", port))
    HTTPServer.allow_reuse_address = True
    server = HTTPServer((host, port), HonorportAPIHandler)
    print(f"[+] Honorport Controller API listening on http://{host}:{port}")
    server.serve_forever()

if __name__ == "__main__":
    run_honorport_api()
