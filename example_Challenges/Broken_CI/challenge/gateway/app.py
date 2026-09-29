#!/usr/bin/env python3
"""
Unified Reverse Proxy Gateway & Web Console for X04 (Broken CI)
Listens on 0.0.0.0:80 (or PORT env var).
Routes incoming traffic to:
- /api/git/*        -> Git HTTP Server (127.0.0.1:8081)
- /api/ci/*         -> CI Pipeline Server (127.0.0.1:8082)
- /registry/v2/*    -> OCI Registry Server (127.0.0.1:5000)
- /v2/*             -> OCI Registry Server (127.0.0.1:5000)
- /api/production/* -> Production Mainframe Server (127.0.0.1:8083)
- /api/reset        -> Challenge Snapshot Reset
- /api/info         -> Challenge Topology Info
- /                 -> Latveria CI/CD Web Console Dashboard
"""

import os
import sys
import json
import urllib.request
import urllib.error
from flask import Flask, render_template, request, Response, jsonify
from pathlib import Path

# Add parent path for snapshot reset utility
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "snapshot"))
from seed_state import reset_all

app = Flask(__name__, template_folder="templates", static_folder="static")

GIT_SERVER_URL = "http://127.0.0.1:8081"
CI_SERVER_URL = "http://127.0.0.1:8082"
REGISTRY_SERVER_URL = "http://127.0.0.1:5000"
PROD_SERVER_URL = "http://127.0.0.1:8083"

def proxy_request(target_base_url, subpath=""):
    url = f"{target_base_url}{subpath}"
    if request.query_string:
        url += f"?{request.query_string.decode('utf-8')}"

    req_headers = {k: v for k, v in request.headers if k.lower() not in ["host", "content-length"]}
    data = request.get_data() if request.method in ["POST", "PUT", "PATCH"] else None

    req = urllib.request.Request(url, data=data, method=request.method, headers=req_headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            content = resp.read()
            headers = [(k, v) for k, v in resp.getheaders() if k.lower() not in ["content-encoding", "transfer-encoding"]]
            return Response(content, status=resp.status, headers=headers)
    except urllib.error.HTTPError as e:
        content = e.read()
        headers = [(k, v) for k, v in e.headers.items() if k.lower() not in ["content-encoding", "transfer-encoding"]]
        return Response(content, status=e.code, headers=headers)
    except Exception as e:
        return jsonify({"error": f"Gateway proxy failure to backend {target_base_url}: {e}"}), 502

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/healthz")
@app.route("/health")
def healthz():
    return jsonify({"status": "OK", "service": "gateway"}), 200

@app.route("/api/info")
def challenge_info():
    return jsonify({
        "challenge_id": "X04",
        "name": "Broken CI",
        "category": "Git / CI / DinD / Container Registry / Deployment",
        "difficulty": "Expert / Bonus",
        "topology": {
            "git_gateway": {"http": "/api/git/defense-network.git", "ssh": "git@target:22/defense-network.git"},
            "ci_pipeline": {"status": "/api/ci/status", "builds": "/api/ci/builds", "trigger": "/api/ci/trigger"},
            "inner_docker_daemon": {"endpoint": "tcp://127.0.0.1:2375", "mode": "DinD (Isolated)"},
            "registry_v2": {"catalog": "/registry/v2/_catalog", "manifests": "/registry/v2/<name>/manifests/<tag>"},
            "production_mock": {"status": "/api/production/status", "deploy": "/api/production/deploy"}
        }
    })

@app.route("/api/reset", methods=["POST", "GET"])
def handle_reset():
    try:
        reset_all()
        return jsonify({"status": "SUCCESS", "message": "X04 challenge state completely reset to seed snapshot."}), 200
    except Exception as e:
        return jsonify({"status": "ERROR", "message": str(e)}), 500

# Proxy routes
@app.route("/api/git", defaults={"subpath": ""}, methods=["GET", "POST"])
@app.route("/api/git/<path:subpath>", methods=["GET", "POST"])
def proxy_git(subpath):
    return proxy_request(GIT_SERVER_URL, f"/api/git/{subpath}" if subpath else "/api/git")

@app.route("/api/ci", defaults={"subpath": ""}, methods=["GET", "POST"])
@app.route("/api/ci/<path:subpath>", methods=["GET", "POST"])
def proxy_ci(subpath):
    return proxy_request(CI_SERVER_URL, f"/api/ci/{subpath}" if subpath else "/api/ci")

@app.route("/registry/v2", defaults={"subpath": ""}, methods=["GET", "POST", "PUT"])
@app.route("/registry/v2/<path:subpath>", methods=["GET", "POST", "PUT"])
def proxy_registry_v2(subpath):
    return proxy_request(REGISTRY_SERVER_URL, f"/v2/{subpath}" if subpath else "/v2")

@app.route("/v2", defaults={"subpath": ""}, methods=["GET", "POST", "PUT"])
@app.route("/v2/<path:subpath>", methods=["GET", "POST", "PUT"])
def proxy_registry_direct(subpath):
    return proxy_request(REGISTRY_SERVER_URL, f"/v2/{subpath}" if subpath else "/v2")

@app.route("/api/production", defaults={"subpath": ""}, methods=["GET", "POST"])
@app.route("/api/production/<path:subpath>", methods=["GET", "POST"])
def proxy_production(subpath):
    return proxy_request(PROD_SERVER_URL, f"/api/production/{subpath}" if subpath else "/api/production")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 80))
    app.run(host="0.0.0.0", port=port, debug=False)
