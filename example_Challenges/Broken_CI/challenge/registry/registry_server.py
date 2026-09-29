#!/usr/bin/env python3
"""
OCI / Docker Distribution Registry v2 Server for X04 (Broken CI)
Listens on 127.0.0.1:5000 (and proxied via Gateway /registry/v2/ and /v2/).
Serves manifests, tags, layer blobs, and catalog for challenge-local images.
"""

import os
import json
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

STORAGE_ROOT = Path("/tmp/x04_storage")
REGISTRY_DIR = STORAGE_ROOT / "registry"
BLOBS_DIR = REGISTRY_DIR / "blobs"
MANIFESTS_DIR = REGISTRY_DIR / "manifests"

class RegistryV2Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def _send_json(self, data, status=200, content_type="application/json"):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Docker-Distribution-Api-Version", "registry/2.0")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_bytes(self, data, status=200, content_type="application/octet-stream", digest=None):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Docker-Distribution-Api-Version", "registry/2.0")
        if digest:
            self.send_header("Docker-Content-Digest", digest)
            self.send_header("Etag", f'"{digest}"')
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # Strip optional /registry prefix from gateway proxy
        if path.startswith("/registry"):
            path = path[len("/registry"):]
        if not path.startswith("/"):
            path = "/" + path

        # Base ping: /v2/
        if path in ["/v2/", "/v2"]:
            return self._send_json({"version": "registry/2.0", "name": "latveria-internal-oci-registry"})

        # Catalog: /v2/_catalog
        if path == "/v2/_catalog":
            repos = []
            if MANIFESTS_DIR.exists():
                for org_p in MANIFESTS_DIR.iterdir():
                    if org_p.is_dir():
                        for repo_p in org_p.iterdir():
                            if repo_p.is_dir():
                                repos.append(f"{org_p.name}/{repo_p.name}")
            return self._send_json({"repositories": sorted(repos)})

        # Tags list: /v2/<name>/tags/list
        if path.endswith("/tags/list"):
            repo_name = path[len("/v2/"):-len("/tags/list")].strip("/")
            repo_path = MANIFESTS_DIR / repo_name
            tags = []
            if repo_path.exists():
                for f in repo_path.glob("*.json"):
                    tag_name = f.stem
                    if tag_name != "latest":
                        tags.append(tag_name)
                if (repo_path / "latest.json").exists():
                    tags.append("latest")
            return self._send_json({"name": repo_name, "tags": tags})

        # Manifests: /v2/<name>/manifests/<reference>
        if "/manifests/" in path:
            prefix, ref = path.rsplit("/manifests/", 1)
            repo_name = prefix[len("/v2/"):].strip("/")
            repo_path = MANIFESTS_DIR / repo_name
            
            manifest_file = None
            if repo_path.exists():
                if (repo_path / f"{ref}.json").exists():
                    manifest_file = repo_path / f"{ref}.json"
                elif (repo_path / ref).exists():
                    manifest_file = repo_path / ref
                elif ref.startswith("sha256:"):
                    blob_file = BLOBS_DIR / ref.replace(":", "_")
                    if blob_file.exists():
                        manifest_file = blob_file

            if manifest_file and manifest_file.exists():
                data = manifest_file.read_bytes()
                return self._send_bytes(data, content_type="application/vnd.docker.distribution.manifest.v2+json", digest=f"sha256:{manifest_file.stem}")
            
            return self._send_json({"errors": [{"code": "MANIFEST_UNKNOWN", "message": f"manifest unknown: {ref}"}]}, status=404)

        # Blobs: /v2/<name>/blobs/<digest>
        if "/blobs/" in path:
            digest = path.split("/blobs/", 1)[1].strip("/")
            blob_file = BLOBS_DIR / digest.replace(":", "_")
            if blob_file.exists():
                data = blob_file.read_bytes()
                return self._send_bytes(data, digest=digest)
            return self._send_json({"errors": [{"code": "BLOB_UNKNOWN", "message": f"blob unknown: {digest}"}]}, status=404)

        return self._send_json({"errors": [{"code": "UNSUPPORTED", "message": "The action is not supported."}]}, status=404)

def run_registry_server(host="127.0.0.1", port=5000):
    port = int(os.environ.get("REGISTRY_PORT", port))
    HTTPServer.allow_reuse_address = True
    server = HTTPServer((host, port), RegistryV2Handler)
    print(f"[+] OCI Registry v2 Server listening on http://{host}:{port}")
    server.serve_forever()

if __name__ == "__main__":
    run_registry_server()
