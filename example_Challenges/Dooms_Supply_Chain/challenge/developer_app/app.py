#!/usr/bin/env python3
"""
Public Developer Application & API Gateway for X03 (Dooms Supply Chain)
Listens on TCP/80 (0.0.0.0:80)
Provides the public web interface, developer portal, and unified API gateway proxying
to internal synthetic microservices.
"""

import os
import sys
import json
import urllib.request
import urllib.parse
import urllib.error
from pathlib import Path
from flask import Flask, render_template, jsonify, request, Response, send_file

app = Flask(__name__, template_folder="templates", static_folder="static")

PKG_REPO_URL = os.environ.get("PKG_REPO_URL", "http://127.0.0.1:4873")
CI_URL = os.environ.get("CI_URL", "http://127.0.0.1:8082")
REGISTRY_URL = os.environ.get("REGISTRY_URL", "http://127.0.0.1:5000")
DEPLOYMENT_URL = os.environ.get("DEPLOYMENT_URL", "http://127.0.0.1:8083")

def proxy_request(target_url, headers=None, data=None, method=None, stream=False):
    """Utility function to proxy HTTP requests to internal microservices."""
    if headers is None:
        headers = {}
    
    # Forward select headers
    forward_headers = {}
    for h in ["Content-Type", "Accept", "X-Latveria-Override-Key", "X-Override-Token", "Authorization"]:
        if h in request.headers:
            forward_headers[h] = request.headers[h]
    forward_headers.update(headers)
    
    if data is None and request.method in ["POST", "PUT", "PATCH"]:
        data = request.get_data()
        
    req_method = method or request.method
    
    req = urllib.request.Request(target_url, data=data if data else None, headers=forward_headers, method=req_method)
    
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            content = resp.read()
            content_type = resp.headers.get("Content-Type", "application/json")
            status = resp.status
            custom_resp = Response(content, status=status, mimetype=content_type)
            for hk in ["Docker-Distribution-API-Version", "Docker-Content-Digest", "Content-Disposition"]:
                if hk in resp.headers:
                    custom_resp.headers[hk] = resp.headers[hk]
            return custom_resp
    except urllib.error.HTTPError as e:
        err_content = e.read()
        content_type = e.headers.get("Content-Type", "application/json")
        return Response(err_content, status=e.code, mimetype=content_type)
    except Exception as e:
        return jsonify({"error": "INTERNAL_PROXY_ERROR", "message": str(e), "target": target_url}), 502

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/healthz")
@app.route("/health")
def healthz():
    return jsonify({"status": "OK", "service": "latveria-supply-chain-gateway"}), 200


@app.route("/api/app/info", methods=["GET"])
def app_info():
    return jsonify({
        "platform": "Latveria Cyber-Supply Chain Control Center",
        "version": "v4.2.0-SOVEREIGN",
        "author": "Doctor Victor von Doom Autonomous Systems",
        "challenge_id": "X03",
        "architecture": {
            "developer_app": "http://0.0.0.0:80",
            "package_repository": "http://127.0.0.1:4873 (/api/packages)",
            "ci_pipeline": "http://127.0.0.1:8082 (/api/ci)",
            "image_registry": "http://127.0.0.1:5000 (/api/registry or /registry/v2)",
            "deployment_target": "http://127.0.0.1:8083 (/api/deployment)"
        },
        "description": "Autonomous Doombot supply chain management console. Manages package dependencies, automated CI builds, OCI container image provenance, and sovereign production cluster deployments."
    })

# --- Package Repository Proxy Routes ---
@app.route("/api/packages", methods=["GET"])
@app.route("/api/packages/", methods=["GET"])
def proxy_packages():
    return proxy_request(f"{PKG_REPO_URL}/api/packages")

@app.route("/api/packages/search", methods=["GET"])
def proxy_packages_search():
    q = request.args.get("q", "")
    return proxy_request(f"{PKG_REPO_URL}/api/packages/search?q={urllib.parse.quote(q)}")

@app.route("/api/packages/<path:subpath>", methods=["GET"])
def proxy_package_subpath(subpath):
    return proxy_request(f"{PKG_REPO_URL}/api/packages/{subpath}")

# --- CI Pipeline Proxy Routes ---
@app.route("/api/ci/status", methods=["GET"])
def proxy_ci_status():
    return proxy_request(f"{CI_URL}/api/ci/status")

@app.route("/api/ci/pipelines", methods=["GET"])
def proxy_ci_pipelines():
    return proxy_request(f"{CI_URL}/api/ci/pipelines")

@app.route("/api/ci/builds", methods=["GET"])
def proxy_ci_builds():
    return proxy_request(f"{CI_URL}/api/ci/builds")

@app.route("/api/ci/builds/<build_id>", methods=["GET"])
def proxy_ci_build_detail(build_id):
    return proxy_request(f"{CI_URL}/api/ci/builds/{build_id}")

@app.route("/api/ci/build", methods=["POST"])
def proxy_ci_trigger():
    return proxy_request(f"{CI_URL}/api/ci/build")

# --- Container Registry Proxy Routes ---
@app.route("/v2/", methods=["GET"])
@app.route("/registry/v2/", methods=["GET"])
@app.route("/api/registry/v2/", methods=["GET"])
def proxy_registry_v2():
    return proxy_request(f"{REGISTRY_URL}/v2/")

@app.route("/v2/_catalog", methods=["GET"])
@app.route("/registry/v2/_catalog", methods=["GET"])
@app.route("/api/registry/v2/_catalog", methods=["GET"])
def proxy_registry_catalog():
    return proxy_request(f"{REGISTRY_URL}/v2/_catalog")

@app.route("/v2/<path:subpath>", methods=["GET"])
@app.route("/registry/v2/<path:subpath>", methods=["GET"])
@app.route("/api/registry/v2/<path:subpath>", methods=["GET"])
def proxy_registry_subpath(subpath):
    return proxy_request(f"{REGISTRY_URL}/v2/{subpath}")

# --- Production Deployment Proxy Routes ---
@app.route("/api/deployment/status", methods=["GET"])
@app.route("/production/status", methods=["GET"])
def proxy_deployment_status():
    return proxy_request(f"{DEPLOYMENT_URL}/api/deployment/status")

@app.route("/api/deployment/telemetry", methods=["GET"])
@app.route("/production/telemetry", methods=["GET"])
def proxy_deployment_telemetry():
    return proxy_request(f"{DEPLOYMENT_URL}/api/deployment/telemetry")

@app.route("/api/deployment/override", methods=["POST"])
@app.route("/api/v1/override", methods=["POST"])
@app.route("/production/override", methods=["POST"])
def proxy_deployment_override():
    return proxy_request(f"{DEPLOYMENT_URL}/api/deployment/override")

# --- Reset Endpoint ---
@app.route("/api/reset", methods=["POST"])
def challenge_reset():
    """Restores challenge state from the clean seed snapshot."""
    try:
        from challenge.snapshot.seed_state import reset_all
        reset_all()
        return jsonify({
            "status": "RESET_SUCCESSFUL",
            "message": "Challenge package repository, container registry, CI workspace, and production deployment restored to pristine seed state."
        })
    except Exception as e:
        return jsonify({"status": "RESET_ERROR", "message": str(e)}), 500

if __name__ == "__main__":
    # Ensure initial snapshot state exists
    try:
        from challenge.snapshot.seed_state import reset_all
        if not Path("/tmp/x03_storage/package_repo").exists():
            reset_all()
    except Exception as e:
        print(f"[!] Warning initializing seed state: {e}")
        
    host = "0.0.0.0"
    port = int(os.environ.get("PORT", 80))
    print(f"[*] Latveria Developer App & Gateway running on {host}:{port}")
    app.run(host=host, port=port, debug=False)
