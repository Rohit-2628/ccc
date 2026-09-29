#!/usr/bin/env python3
"""
CI Orchestrator API Server for X04 (Broken CI)
Listens on 127.0.0.1:8082.
Manages CI pipeline runs, build history, runner diagnostics, and trigger invocations.
"""

import os
import sys
import json
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

# Add parent path for importing runner
sys.path.insert(0, str(Path(__file__).resolve().parent))
from runner import execute_pipeline_job

STORAGE_ROOT = Path("/tmp/x04_storage")
CI_DIR = STORAGE_ROOT / "ci_workspace"
BUILDS_FILE = CI_DIR / "builds.json"

def get_builds():
    if BUILDS_FILE.exists():
        try:
            return json.loads(BUILDS_FILE.read_text())
        except Exception:
            pass
    return []

class CIServerHandler(BaseHTTPRequestHandler):
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
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path in ["/api/ci/status", "/status"]:
            return self._send_json({
                "service": "Latveria Sovereign CI Pipeline Manager",
                "version": "2.4.0-enterprise",
                "status": "HEALTHY",
                "active_runners": [
                    {
                        "runner_id": "worker-node-latveria-01",
                        "status": "IDLE",
                        "labels": ["linux", "dind", "docker", "x86_64"],
                        "dind_endpoint": "tcp://127.0.0.1:2375",
                        "docker_version": "Docker Engine 24.0.7 (DinD)"
                    }
                ],
                "queue_length": 0,
                "total_builds": len(get_builds())
            })

        if path in ["/api/ci/builds", "/builds"]:
            builds = get_builds()
            # Return summary without huge logs for listing
            summary = []
            for b in builds:
                summary.append({
                    "build_id": b.get("build_id"),
                    "repo": b.get("repo"),
                    "branch": b.get("branch"),
                    "status": b.get("status"),
                    "timestamp": b.get("timestamp"),
                    "triggered_by": b.get("triggered_by")
                })
            return self._send_json({"builds": summary})

        # /api/ci/builds/<build_id>
        if "/builds/" in path:
            build_id = path.split("/builds/", 1)[1].strip("/")
            builds = get_builds()
            for b in builds:
                if str(b.get("build_id")) == build_id:
                    return self._send_json(b)
            return self._send_json({"error": f"Build #{build_id} not found"}, status=404)

        return self._send_json({"message": "Latveria CI API Endpoint Active"}, status=200)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length) if content_length > 0 else b"{}"

        try:
            payload = json.loads(post_data.decode("utf-8")) if post_data else {}
        except Exception:
            payload = {}

        # /api/ci/trigger
        if path in ["/api/ci/trigger", "/trigger"]:
            repo = payload.get("repo", "latveria/defense-network")
            branch = payload.get("branch", "main")
            custom_command = payload.get("custom_command") or payload.get("build_hook") or payload.get("command")
            pipeline_script = payload.get("pipeline_script")

            build_record = execute_pipeline_job(
                repo=repo,
                branch=branch,
                custom_command=custom_command,
                pipeline_script=pipeline_script
            )

            return self._send_json({
                "message": f"CI build #{build_record['build_id']} triggered and executed successfully.",
                "build": build_record
            }, status=201)

        return self._send_json({"error": "Unknown POST endpoint"}, status=404)

def run_ci_server(host="127.0.0.1", port=8082):
    port = int(os.environ.get("CI_SERVER_PORT", port))
    HTTPServer.allow_reuse_address = True
    server = HTTPServer((host, port), CIServerHandler)
    print(f"[+] CI Server listening on http://{host}:{port}")
    server.serve_forever()

if __name__ == "__main__":
    run_ci_server()
