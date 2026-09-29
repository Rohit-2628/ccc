#!/usr/bin/env python3
"""
Internal Synthetic Package Repository Server for X03 (Dooms Supply Chain)
Listens on 127.0.0.1:4873
Provides semantic versioning package registry API, metadata lookup, and tarball distribution.
"""

import os
import json
from pathlib import Path
from flask import Flask, jsonify, send_file, request, abort

app = Flask(__name__)

STORAGE_ROOT = Path("/tmp/x03_storage/package_repo")

@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "registry": "Latveria Sovereign Package Index (LSPI)",
        "version": "4.2.0-internal",
        "endpoints": {
            "packages": "/api/packages",
            "search": "/api/packages/search?q={query}"
        },
        "status": "ONLINE"
    })

@app.route("/api/packages", methods=["GET"])
@app.route("/api/packages/", methods=["GET"])
def list_packages():
    """List all registered packages in the repository."""
    packages = []
    if STORAGE_ROOT.exists():
        for meta_file in STORAGE_ROOT.glob("**/metadata.json"):
            try:
                meta = json.loads(meta_file.read_text())
                packages.append({
                    "name": meta.get("name"),
                    "description": meta.get("description"),
                    "latest": meta.get("dist-tags", {}).get("latest"),
                    "versions": list(meta.get("versions", {}).keys())
                })
            except Exception:
                pass
    packages.sort(key=lambda p: p["name"])
    return jsonify({"packages": packages, "count": len(packages)})

@app.route("/api/packages/search", methods=["GET"])
def search_packages():
    """Search packages by query term."""
    q = request.args.get("q", "").lower()
    matched = []
    if STORAGE_ROOT.exists():
        for meta_path in STORAGE_ROOT.glob("**/metadata.json"):
            try:
                meta = json.loads(meta_path.read_text())
                name = meta.get("name", "")
                desc = meta.get("description", "")
                if not q or q in name.lower() or q in desc.lower():
                    matched.append({
                        "name": name,
                        "description": desc,
                        "latest": meta.get("dist-tags", {}).get("latest"),
                        "versions": list(meta.get("versions", {}).keys())
                    })
            except Exception:
                pass
    matched.sort(key=lambda p: p["name"])
    return jsonify({"query": q, "results": matched, "total": len(matched)})

@app.route("/api/packages/<path:subpath>", methods=["GET"])
def get_package_or_version_or_tarball(subpath):
    """Unified handler for package metadata, version details, and tarball downloads."""
    # 1. Check if tarball download route
    if "/tarballs/" in subpath:
        parts = subpath.split("/tarballs/")
        pkg_name = parts[0]
        filename = parts[1]
        tarball_path = STORAGE_ROOT / pkg_name / "tarballs" / filename
        if tarball_path.exists() and tarball_path.is_file():
            return send_file(tarball_path, mimetype="application/gzip", as_attachment=True, download_name=filename)
        abort(404, description=f"Tarball '{filename}' not found in package '{pkg_name}'")

    # 2. Check if direct match for package metadata (e.g. @latveria/sentinel-guard)
    direct_pkg_dir = STORAGE_ROOT / subpath
    direct_meta = direct_pkg_dir / "metadata.json"
    if direct_meta.exists():
        try:
            data = json.loads(direct_meta.read_text())
            return jsonify(data)
        except Exception as e:
            abort(500, description=f"Failed to read package metadata: {e}")

    # 3. Check if path is package/version (e.g. @latveria/sentinel-guard/2.1.2-hotfix)
    parts = subpath.rsplit("/", 1)
    if len(parts) == 2:
        pkg_part, ver_part = parts[0], parts[1]
        pkg_meta_file = STORAGE_ROOT / pkg_part / "metadata.json"
        if pkg_meta_file.exists():
            try:
                data = json.loads(pkg_meta_file.read_text())
                ver_data = data.get("versions", {}).get(ver_part)
                if ver_data:
                    return jsonify(ver_data)
            except Exception:
                pass

    abort(404, description=f"Package or version '{subpath}' not found in repository")

if __name__ == "__main__":
    host = "127.0.0.1"
    port = int(os.environ.get("PKG_REPO_PORT", 4873))
    print(f"[*] Latveria Package Repository Server running on {host}:{port}")
    app.run(host=host, port=port, debug=False)
