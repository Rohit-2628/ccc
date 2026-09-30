#!/usr/bin/env python3
"""
Honorport Mainframe Vault Production Server for XO-9 (Honorport Heist - Docker in Docker)
Runs on 127.0.0.1:8083. Validates HMAC-SHA256 signatures generated with the Harbor Master secret key.
Returns team flag upon successful override authorization.
"""

import os
import json
import time
import hmac
import hashlib
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

STORAGE_ROOT = Path("/tmp/xo9_storage")
PRODUCTION_DIR = STORAGE_ROOT / "production"
FLAG_DIR = STORAGE_ROOT / "flag"

DEFAULT_FLAG = "YUVA{d1nd_h0n0rp0rt_h31st_d0ck3r_1n_d0ck3r_x09}"
EXPECTED_HARBOR_MASTER_ID = "HONORPORT-HARBOR-MASTER-09"
EXPECTED_SECRET_KEY = "honorport_vault_sig_7749102837194821"

def get_flag():
    flag_file = FLAG_DIR / "flag.txt"
    if flag_file.exists():
        return flag_file.read_text().strip()
    return DEFAULT_FLAG

class HonorportVaultHandler(BaseHTTPRequestHandler):
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
        if path in ["/api/production/status", "/api/production/status/"]:
            state_file = PRODUCTION_DIR / "state.json"
            if state_file.exists():
                try:
                    state = json.loads(state_file.read_text())
                    return self._send_json(state)
                except Exception:
                    pass
            return self._send_json({
                "vault_id": "HONORPORT-HIGH-SECURITY-VAULT-09",
                "status": "LOCKED",
                "unlocked": False
            })

        return self._send_json({"error": "Endpoint not found"}, status=404)

    def do_POST(self):
        path = self.path
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else ""

        try:
            req_data = json.loads(body) if body else {}
        except Exception:
            req_data = {}

        if path in ["/api/production/override", "/api/production/override/"]:
            harbor_master_id = req_data.get("harbor_master_id", "")
            timestamp = str(req_data.get("timestamp", ""))
            signature = req_data.get("signature", "")

            if harbor_master_id != EXPECTED_HARBOR_MASTER_ID:
                return self._send_json({
                    "status": "DENIED",
                    "reason": f"Invalid Harbor Master ID '{harbor_master_id}'"
                }, status=403)

            # HMAC verification
            msg = f"{harbor_master_id}:{timestamp}".encode("utf-8")
            expected_sig = hmac.new(EXPECTED_SECRET_KEY.encode("utf-8"), msg, hashlib.sha256).hexdigest()

            if hmac.compare_digest(signature.lower(), expected_sig.lower()):
                flag = get_flag()
                
                # Update state
                state_file = PRODUCTION_DIR / "state.json"
                if state_file.exists():
                    try:
                        st = json.loads(state_file.read_text())
                        st["status"] = "UNLOCKED_OVERRIDDEN"
                        st["unlocked"] = True
                        st["override_timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                        state_file.write_text(json.dumps(st, indent=2))
                    except Exception:
                        pass

                return self._send_json({
                    "status": "SUCCESS",
                    "message": "Honorport High-Security Vault Override Authorized.",
                    "vault_id": "HONORPORT-HIGH-SECURITY-VAULT-09",
                    "flag": flag
                }, status=200)
            else:
                return self._send_json({
                    "status": "DENIED",
                    "reason": "HMAC-SHA256 signature verification failed for Honorport Mainframe."
                }, status=401)

        return self._send_json({"error": "Endpoint not found"}, status=404)

def run_production_server(host="127.0.0.1", port=8083):
    port = int(os.environ.get("PRODUCTION_PORT", port))
    HTTPServer.allow_reuse_address = True
    server = HTTPServer((host, port), HonorportVaultHandler)
    print(f"[+] Honorport Vault Production Server listening on http://{host}:{port}")
    server.serve_forever()

if __name__ == "__main__":
    run_production_server()
