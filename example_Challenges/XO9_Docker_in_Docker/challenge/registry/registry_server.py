#!/usr/bin/env python3
"""
Challenge-Local OCI / Docker Registry v2 Server for XO-9 (Honorport Heist - Docker in Docker)
Runs on 127.0.0.1:5000. Serves manifest schemas, layer diff blobs, and repository catalogs.
"""

import os
import json
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

STORAGE_ROOT = Path("/tmp/xo9_storage")
REGISTRY_DIR = STORAGE_ROOT / "registry"

class RegistryHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def _send_bytes(self, content_type, data, status=200, headers=None):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Docker-Distribution-Api-Version", "registry/2.0")
        if headers:
            for k, v in headers.items():
                self.send_header(k, v)
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = self.path
        if path == "/v2/" or path == "/v2":
            return self._send_bytes("application/json", b"{}", status=200)

        if path == "/v2/_catalog":
            catalog = {
                "repositories": [
                    "system/base-os",
                    "defense/vault-gatekeeper",
                    "internal/harbor-master-signer"
                ]
            }
            return self._send_bytes("application/json", json.dumps(catalog).encode("utf-8"))

        # Manifest requests: /v2/<repo...>/manifests/<reference>
        if "/manifests/" in path and path.startswith("/v2/"):
            parts = path[4:].split("/manifests/")
            if len(parts) == 2:
                repo_name = parts[0]
                reference = parts[1]
                
                manifest_file = REGISTRY_DIR / "manifests" / repo_name / f"{reference}.json"
                if not manifest_file.exists():
                    # Try reference as digest match
                    found = list((REGISTRY_DIR / "manifests" / repo_name).glob("*.json"))
                    if found:
                        manifest_file = found[0]

                if manifest_file.exists():
                    data = manifest_file.read_bytes()
                    return self._send_bytes("application/vnd.docker.distribution.manifest.v2+json", data)

        # Blob requests: /v2/<repo...>/blobs/<digest>
        if "/blobs/" in path and path.startswith("/v2/"):
            parts = path[4:].split("/blobs/")
            if len(parts) == 2:
                digest = parts[1].replace(":", "_")
                blob_file = REGISTRY_DIR / "blobs" / digest
                if blob_file.exists():
                    data = blob_file.read_bytes()
                    return self._send_bytes("application/octet-stream", data)

        return self._send_bytes("application/json", b'{"errors":[{"code":"NAME_UNKNOWN","message":"repository name not known to registry"}]}', status=404)

def run_registry_server(host="127.0.0.1", port=5000):
    port = int(os.environ.get("REGISTRY_PORT", port))
    HTTPServer.allow_reuse_address = True
    server = HTTPServer((host, port), RegistryHandler)
    print(f"[+] OCI Registry Server listening on http://{host}:{port}")
    server.serve_forever()

if __name__ == "__main__":
    run_registry_server()
