#!/usr/bin/env python3
"""
Internal Synthetic OCI v2 Container Registry Server for X03 (Dooms Supply Chain)
Listens on 127.0.0.1:5000
Implements OCI / Docker Distribution Registry v2 specification endpoints.
"""

import os
import json
from pathlib import Path
from flask import Flask, jsonify, send_file, request, Response, abort

app = Flask(__name__)

STORAGE_ROOT = Path("/tmp/x03_storage/registry")

@app.route("/v2/", methods=["GET"])
@app.route("/api/registry/v2/", methods=["GET"])
def v2_check():
    resp = jsonify({"status": "ok", "message": "Latveria Sovereign OCI Registry v2.0"})
    resp.headers["Docker-Distribution-API-Version"] = "registry/2.0"
    return resp

@app.route("/v2/_catalog", methods=["GET"])
@app.route("/api/registry/v2/_catalog", methods=["GET"])
def catalog():
    """List available container image repositories."""
    repos = []
    manifests_root = STORAGE_ROOT / "manifests"
    if manifests_root.exists():
        for org_dir in manifests_root.iterdir():
            if org_dir.is_dir():
                for repo_dir in org_dir.iterdir():
                    if repo_dir.is_dir():
                        repos.append(f"{org_dir.name}/{repo_dir.name}")
    return jsonify({"repositories": sorted(repos)})

@app.route("/v2/<path:name>/tags/list", methods=["GET"])
@app.route("/api/registry/v2/<path:name>/tags/list", methods=["GET"])
def list_tags(name):
    """List available tags for an image repository."""
    manifest_dir = STORAGE_ROOT / "manifests" / name
    if not manifest_dir.exists():
        abort(404, description=f"Repository '{name}' not found")
    
    tags = []
    for manifest_file in manifest_dir.glob("*.json"):
        tags.append(manifest_file.stem)
    
    return jsonify({"name": name, "tags": sorted(tags)})

@app.route("/v2/<path:name>/manifests/<reference>", methods=["GET"])
@app.route("/api/registry/v2/<path:name>/manifests/<reference>", methods=["GET"])
def get_manifest(name, reference):
    """Retrieve image manifest by tag or digest."""
    manifest_dir = STORAGE_ROOT / "manifests" / name
    manifest_file = manifest_dir / f"{reference}.json"
    
    # Check if reference is a digest
    if not manifest_file.exists() and reference.startswith("sha256:"):
        blob_file = STORAGE_ROOT / "blobs" / reference.replace(":", "_")
        if blob_file.exists():
            manifest_file = blob_file

    if not manifest_file.exists():
        abort(404, description=f"Manifest '{reference}' for '{name}' not found")
    
    data = manifest_file.read_bytes()
    resp = Response(data, mimetype="application/vnd.docker.distribution.manifest.v2+json")
    resp.headers["Docker-Content-Digest"] = reference if reference.startswith("sha256:") else f"sha256:{reference}"
    return resp

@app.route("/v2/<path:name>/blobs/<digest>", methods=["GET"])
@app.route("/api/registry/v2/<path:name>/blobs/<digest>", methods=["GET"])
def get_blob(name, digest):
    """Download container image layer or config blob."""
    clean_digest = digest.replace(":", "_")
    blob_path = STORAGE_ROOT / "blobs" / clean_digest
    if not blob_path.exists():
        abort(404, description=f"Blob '{digest}' not found")
    
    return send_file(blob_path, mimetype="application/octet-stream", as_attachment=False)

if __name__ == "__main__":
    host = "127.0.0.1"
    port = int(os.environ.get("REGISTRY_PORT", 5000))
    print(f"[*] Latveria OCI Container Registry running on {host}:{port}")
    app.run(host=host, port=port, debug=False)
