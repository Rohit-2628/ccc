#!/usr/bin/env python3
"""
Unified Gateway & Web UI Reverse Proxy for XO-9 (Honorport Heist - Docker in Docker)
Listens on TCP/80 (or PORT env, default 8080).
Routes requests to internal sub-services (Honorport API on 8082, Production Mainframe on 8083).
"""

import os
import sys
import json
import urllib.request
import urllib.parse
import urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

CHALLENGE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(CHALLENGE_DIR / "snapshot"))
import seed_state

HONORPORT_API_URL = "http://127.0.0.1:8082"
PRODUCTION_API_URL = "http://127.0.0.1:8083"
STATIC_DIR = Path(__file__).resolve().parent / "static"
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"

class GatewayHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def _send_bytes(self, content_type, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _proxy_request(self, target_url, method="GET", body=None, headers=None):
        req = urllib.request.Request(target_url, method=method)
        if headers:
            for k, v in headers.items():
                if k.lower() not in ["host", "content-length"]:
                    req.add_header(k, v)
        if body:
            req.data = body if isinstance(body, bytes) else body.encode("utf-8")

        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = resp.read()
                ct = resp.headers.get("Content-Type", "application/json")
                return self._send_bytes(ct, data, status=resp.status)
        except urllib.error.HTTPError as e:
            data = e.read()
            ct = e.headers.get("Content-Type", "application/json")
            return self._send_bytes(ct, data, status=e.code)
        except Exception as e:
            err = json.dumps({"error": f"Gateway Proxy Error: {e}"}).encode("utf-8")
            return self._send_bytes("application/json", err, status=502)

    def do_GET(self):
        path = self.path

        if path in ["/", "/index.html"]:
            idx_file = TEMPLATES_DIR / "index.html"
            if idx_file.exists():
                return self._send_bytes("text/html; charset=utf-8", idx_file.read_bytes())
            return self._send_bytes("text/plain", b"Honorport Logistics Console")

        if path.startswith("/static/"):
            rel_path = path[len("/static/"):]
            file_path = STATIC_DIR / rel_path
            if file_path.exists() and file_path.is_file():
                if rel_path.endswith(".css"):
                    ct = "text/css"
                elif rel_path.endswith(".js"):
                    ct = "application/javascript"
                elif rel_path.endswith(".png"):
                    ct = "image/png"
                else:
                    ct = "text/plain"
                return self._send_bytes(ct, file_path.read_bytes())

        # Reset endpoint
        if path == "/api/reset":
            seed_state.reset_all()
            return self._send_bytes("application/json", json.dumps({"status": "SUCCESS", "message": "Sandbox state reset cleanly"}).encode("utf-8"))

        # Route to Honorport API
        if path.startswith("/api/info") or path.startswith("/api/deployments") or path.startswith("/api/deploy"):
            target = f"{HONORPORT_API_URL}{path}"
            return self._proxy_request(target, method="GET")

        # Route to Production Mainframe API
        if path.startswith("/api/production/"):
            target = f"{PRODUCTION_API_URL}{path}"
            return self._proxy_request(target, method="GET")

        return self._send_bytes("application/json", b'{"error":"Not Found"}', status=404)

    def do_POST(self):
        path = self.path
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b""

        # Reset endpoint
        if path in ["/api/reset", "/api/reset/"]:
            seed_state.reset_all()
            return self._send_bytes("application/json", json.dumps({"status": "SUCCESS", "message": "Sandbox state reset cleanly"}).encode("utf-8"))

        if path.startswith("/api/deploy"):
            target = f"{HONORPORT_API_URL}{path}"
            return self._proxy_request(target, method="POST", body=body, headers={"Content-Type": self.headers.get("Content-Type", "application/json")})

        if path.startswith("/api/production/"):
            target = f"{PRODUCTION_API_URL}{path}"
            return self._proxy_request(target, method="POST", body=body, headers={"Content-Type": self.headers.get("Content-Type", "application/json")})

        return self._send_bytes("application/json", b'{"error":"Not Found"}', status=404)

def run_gateway(host="0.0.0.0", port=8080):
    port = int(os.environ.get("PORT", port))
    HTTPServer.allow_reuse_address = True
    server = HTTPServer((host, port), GatewayHandler)
    print(f"[+] Unified Web Gateway listening on http://{host}:{port}")
    server.serve_forever()

if __name__ == "__main__":
    run_gateway()
