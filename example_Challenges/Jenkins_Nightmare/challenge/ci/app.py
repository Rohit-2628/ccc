#!/usr/bin/env python3
"""
Latverian Sovereign CI/CD Gateway & Orchestrator (Jenkins Nightmare)
Main Web Interface (TCP/80) & CI Pipeline Controller
"""

import datetime
import io
import json
import os
import sys
import threading
import time
import urllib.request
import urllib.error
from flask import Flask, request, jsonify, render_template, send_file, redirect, url_for, Response

# Add challenge root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from mock_git import git_server
from build_runtime.runner import BuildRunner, ARTIFACTS_BASE, WORKSPACE_BASE

app = Flask(__name__, template_folder="templates", static_folder="static")
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB max payload

REGISTRY_URL = os.environ.get("REGISTRY_URL", "http://127.0.0.1:5000")
PRODUCTION_URL = os.environ.get("PRODUCTION_URL", "http://127.0.0.1:8081")
PORT = int(os.environ.get("PORT", 80))

# In-memory build database
builds_db = {}
build_counter = 100
build_lock = threading.Lock()

# Seed initial builds
def seed_initial_builds():
    global build_counter
    repo = git_server.get_repository("latveria/defense-core")
    b1 = BuildRunner(
        build_id=101,
        repo_data=repo,
        branch="main",
        build_params={"BUILD_PROFILE": "release"}
    )
    b1.status = "SUCCESS"
    b1.start_time = time.time() - 3600
    b1.end_time = time.time() - 3570
    b1.log("=== Starting CI Build #101 ===")
    b1.log("Target Repository: latveria/defense-core (branch: main)")
    b1.log("Runner Environment: sandboxed-builder-v3 (Hard Timeout: 90s)")
    b1.log("[Stage 1/5: PREPARE_WORKSPACE] Populated 4 source files. Workspace ready.")
    b1.log("[Stage 2/5: STATIC_ANALYSIS] make check -> [OK] No critical flaws detected.")
    b1.log("[Stage 3/5: UNIT_TESTS] make test -> [OK] All 48 tests passed.")
    b1.log("[Stage 4/5: PACKAGE_CONTAINER] Successfully tagged latveria/defense-core:build-101")
    b1.log("[Stage 5/5: PUSH_REGISTRY] Pushed latveria/defense-core:build-101 to registry.")
    b1.log("=== Build #101 Completed Successfully ===")
    builds_db[101] = b1
    build_counter = 102

seed_initial_builds()

# ==================== WEB UI ROUTES ====================

@app.route("/", methods=["GET"])
def index():
    repos = git_server.list_repositories()
    recent_builds = [b.get_details() for b in sorted(builds_db.values(), key=lambda x: x.build_id, reverse=True)[:10]]
    return render_template("index.html", page="dashboard", repos=repos, recent_builds=recent_builds)

@app.route("/repos", methods=["GET"])
def web_repos():
    repos = git_server.list_repositories()
    return render_template("index.html", page="repos", repos=repos)

@app.route("/repos/<path:repo_id>", methods=["GET"])
def web_repo_detail(repo_id):
    repo = git_server.get_repository(repo_id)
    if not repo:
        return render_template("index.html", page="error", message=f"Repository '{repo_id}' not found."), 404
    files = git_server.get_tree(repo_id)
    commits = git_server.get_commits(repo_id)
    selected_file = request.args.get("file", "pipeline.yaml")
    file_content = git_server.get_blob(repo_id, selected_file)
    return render_template("index.html", page="repo_detail", repo=repo, files=files, commits=commits, selected_file=selected_file, file_content=file_content)

@app.route("/pipelines", methods=["GET"])
def web_pipelines():
    repos = git_server.list_repositories()
    return render_template("index.html", page="pipelines", repos=repos)

@app.route("/builds", methods=["GET"])
def web_builds():
    all_builds = [b.get_details() for b in sorted(builds_db.values(), key=lambda x: x.build_id, reverse=True)]
    return render_template("index.html", page="builds", builds=all_builds)

@app.route("/builds/<int:build_id>", methods=["GET"])
def web_build_detail(build_id):
    runner = builds_db.get(build_id)
    if not runner:
        return render_template("index.html", page="error", message=f"Build #{build_id} not found."), 404
    return render_template("index.html", page="build_detail", build=runner.get_details())

# ==================== API ROUTES ====================

@app.route("/api/status", methods=["GET"])
def api_status():
    return jsonify({
        "system": "Latveria Sovereign CI/CD Cluster Gateway",
        "version": "2.4.0-latv-enterprise",
        "status": "OPERATIONAL",
        "active_runners": 1,
        "runner_pool": [
            {
                "id": "sandboxed-builder-v3",
                "status": "IDLE",
                "isolation": "EPHEMERAL_WORKSPACE",
                "timeout_limit_seconds": 90,
                "memory_limit": "2GiB"
            }
        ],
        "registry_target": "http://127.0.0.1:5000",
        "production_target": "http://127.0.0.1:8081",
        "total_builds": len(builds_db)
    })

@app.route("/api/repos", methods=["GET"])
def api_repos():
    return jsonify({"repositories": git_server.list_repositories()})

@app.route("/api/repos/<path:repo_id>/commits", methods=["GET"])
def api_repo_commits(repo_id):
    commits = git_server.get_commits(repo_id)
    if commits is None:
        return jsonify({"error": "Repository not found"}), 404
    return jsonify({"repository": repo_id, "commits": commits})

@app.route("/api/repos/<path:repo_id>/tree", methods=["GET"])
def api_repo_tree(repo_id):
    tree = git_server.get_tree(repo_id)
    if tree is None:
        return jsonify({"error": "Repository not found"}), 404
    return jsonify({"repository": repo_id, "tree": tree})

@app.route("/api/repos/<path:repo_id>/blob", methods=["GET"])
def api_repo_blob(repo_id):
    file_path = request.args.get("path")
    if not file_path:
        return jsonify({"error": "Missing 'path' query parameter"}), 400
    content = git_server.get_blob(repo_id, file_path)
    if content is None:
        return jsonify({"error": "File not found"}), 404
    return jsonify({"repository": repo_id, "path": file_path, "content": content})

@app.route("/api/builds", methods=["GET"])
def api_builds():
    res = [b.get_details() for b in sorted(builds_db.values(), key=lambda x: x.build_id, reverse=True)]
    return jsonify({"builds": res})

@app.route("/api/builds/<int:build_id>", methods=["GET"])
def api_build_detail(build_id):
    runner = builds_db.get(build_id)
    if not runner:
        return jsonify({"error": "Build not found"}), 404
    return jsonify(runner.get_details())

@app.route("/api/builds/<int:build_id>/artifacts", methods=["GET"])
def api_build_artifacts(build_id):
    bundle_path = os.path.join(ARTIFACTS_BASE, f"build_{build_id}", "build_bundle.tar.gz")
    if not os.path.exists(bundle_path):
        return jsonify({"error": "Artifact bundle not found for this build"}), 404
    return send_file(bundle_path, as_attachment=True, download_name=f"build_{build_id}_artifacts.tar.gz")

@app.route("/api/builds/trigger", methods=["POST"])
def api_trigger_build():
    global build_counter
    data = request.get_json(force=True, silent=True) or {}
    repo_id = data.get("repo", "latveria/defense-core")
    branch = data.get("branch", "main")
    build_hook = data.get("build_hook")
    build_params = data.get("build_params") or {}

    repo = git_server.get_repository(repo_id)
    if not repo:
        return jsonify({"error": f"Invalid repository '{repo_id}'"}), 400

    # Limit active concurrent builds
    running_count = sum(1 for b in builds_db.values() if b.status == "RUNNING")
    if running_count >= 2:
        return jsonify({"error": "Runner capacity reached (max 2 concurrent builds). Please wait."}), 429

    with build_lock:
        current_id = build_counter
        build_counter += 1
        runner = BuildRunner(
            build_id=current_id,
            repo_data=repo,
            branch=branch,
            build_hook=build_hook,
            build_params=build_params
        )
        builds_db[current_id] = runner

    # Launch build asynchronously
    t = threading.Thread(target=runner.execute_build, daemon=True)
    t.start()

    return jsonify({
        "status": "QUEUED",
        "build_id": current_id,
        "message": f"Build #{current_id} dispatched to sandboxed-builder-v3.",
        "url": f"/builds/{current_id}",
        "api_url": f"/api/builds/{current_id}"
    }), 202

@app.route("/api/reset", methods=["POST"])
def api_reset():
    """Reset challenge state."""
    with build_lock:
        builds_db.clear()
        seed_initial_builds()
    return jsonify({"status": "SUCCESS", "message": "CI challenge state has been reset to default."})

# ==================== GATEWAY REVERSE PROXIES ====================

@app.route("/registry/v2/", defaults={"subpath": ""}, methods=["GET", "POST", "PUT", "HEAD"])
@app.route("/registry/v2/<path:subpath>", methods=["GET", "POST", "PUT", "HEAD"])
@app.route("/v2/", defaults={"subpath": ""}, methods=["GET", "POST", "PUT", "HEAD"])
@app.route("/v2/<path:subpath>", methods=["GET", "POST", "PUT", "HEAD"])
def proxy_registry(subpath):
    target = f"{REGISTRY_URL}/v2/{subpath}"
    if request.query_string:
        target += f"?{request.query_string.decode('utf-8')}"

    headers = {}
    for h in ["Authorization", "Accept", "Content-Type"]:
        if h in request.headers:
            headers[h] = request.headers[h]

    body = request.get_data() if request.method in ["POST", "PUT"] else None

    req = urllib.request.Request(target, data=body, headers=headers, method=request.method)
    try:
        with urllib.request.urlopen(req) as resp:
            content = resp.read()
            out_resp = Response(content, status=resp.status, mimetype=resp.headers.get("Content-Type"))
            for h in ["Docker-Content-Digest", "Www-Authenticate"]:
                if h in resp.headers:
                    out_resp.headers[h] = resp.headers[h]
            return out_resp
    except urllib.error.HTTPError as e:
        err_content = e.read()
        out_resp = Response(err_content, status=e.code, mimetype=e.headers.get("Content-Type", "application/json"))
        if "Www-Authenticate" in e.headers:
            out_resp.headers["Www-Authenticate"] = e.headers["Www-Authenticate"]
        return out_resp
    except Exception as e:
        return jsonify({"error": f"Failed to connect to local registry: {e}"}), 502

@app.route("/api/v1/production/<path:subpath>", methods=["GET", "POST", "PUT"])
@app.route("/production/api/v1/<path:subpath>", methods=["GET", "POST", "PUT"])
@app.route("/production/<path:subpath>", methods=["GET", "POST", "PUT"])
def proxy_production(subpath):
    if subpath.startswith("production/"):
        target = f"{PRODUCTION_URL}/api/v1/{subpath}"
    else:
        target = f"{PRODUCTION_URL}/api/v1/production/{subpath}"
    headers = {}
    for h in ["X-Latveria-Deploy-Agent", "X-Latveria-Signature", "Content-Type"]:
        if h in request.headers:
            headers[h] = request.headers[h]

    body = request.get_data() if request.method in ["POST", "PUT"] else None

    req = urllib.request.Request(target, data=body, headers=headers, method=request.method)
    try:
        with urllib.request.urlopen(req) as resp:
            return Response(resp.read(), status=resp.status, mimetype=resp.headers.get("Content-Type", "application/json"))
    except urllib.error.HTTPError as e:
        return Response(e.read(), status=e.code, mimetype=e.headers.get("Content-Type", "application/json"))
    except Exception as e:
        return jsonify({"error": f"Failed to connect to production mock: {e}"}), 502

if __name__ == "__main__":
    print(f"[*] Starting Latveria Sovereign CI Gateway on 0.0.0.0:{PORT}")
    app.run(host="0.0.0.0", port=PORT, debug=False)
