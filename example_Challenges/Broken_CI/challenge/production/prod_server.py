#!/usr/bin/env python3
"""
Production Mainframe Mock for X04 (Broken CI)
Listens on 127.0.0.1:8083 (and proxied via Gateway /api/production/).
Represents the final deployment stage of the CI/CD -> DinD -> Registry -> Production trust chain.
Validates cryptographic deployment signatures and releases the flag upon verified production promotion.
"""

import os
import json
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

STORAGE_ROOT = Path("/tmp/x04_storage")
PROD_DIR = STORAGE_ROOT / "production"
FLAG_FILE = STORAGE_ROOT / "flag" / "flag.txt"
STATE_FILE = PROD_DIR / "state.json"

EXPECTED_SIGNER = "DOOM-DEPLOYMENT-SIGNER-04"
EXPECTED_SIGNING_KEY = "latv_prod_deploy_sig_8829104820194812"

def get_state():
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {"status": "UNKNOWN", "unlocked": False}

def save_state(st):
    STATE_FILE.write_text(json.dumps(st, indent=2))

_CACHED_FLAG = None

def get_flag():
    global _CACHED_FLAG
    if _CACHED_FLAG is not None:
        return _CACHED_FLAG

    seed_file = "/tmp/.ci_flag_seed"
    if os.path.exists(seed_file):
        try:
            with open(seed_file, "r") as f:
                _CACHED_FLAG = f.read().strip()
            os.remove(seed_file)
        except Exception:
            pass

    if not _CACHED_FLAG and FLAG_FILE.exists():
        try:
            _CACHED_FLAG = FLAG_FILE.read_text().strip()
            os.remove(FLAG_FILE)
        except Exception:
            pass

    if not _CACHED_FLAG:
        _CACHED_FLAG = os.environ.get(
            "FLAG",
            os.environ.get(
                "CHALLENGE_FLAG",
                os.environ.get(
                    "DYNAMIC_FLAG",
                    os.environ.get(
                        "FLAG_VALUE",
                        os.environ.get("TARGET_FLAG", "YUVA{d1nd_c1_runn3r_r3g1stry_pr0d_p1v0t_x04}")
                    )
                )
            )
        ).strip()

    # Scrub flag variables from current process environment
    for _k in ["FLAG", "CHALLENGE_FLAG", "DYNAMIC_FLAG", "FLAG_VALUE", "TARGET_FLAG", "FLAG_VAL"]:
        os.environ.pop(_k, None)

    return _CACHED_FLAG

# Pre-cache flag and consume seed file immediately on boot
get_flag()

class ProductionServerHandler(BaseHTTPRequestHandler):
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

        if path in ["/api/production/status", "/status"]:
            st = get_state()
            return self._send_json({
                "cluster_name": st.get("cluster_name", "SOVEREIGN-PROD-MAINFRAME-01"),
                "status": st.get("status", "ONLINE_LOCKED"),
                "active_image": st.get("active_image", "registry.latveria.local:5000/defense/sentinel-node:v2.1.0"),
                "defense_shield": st.get("defense_shield", "ONLINE (100% MAXIMUM SOVEREIGNTY)"),
                "deployment_policy": {
                    "verification": "CRYPTOGRAPHIC_SIGNATURE_ENFORCED",
                    "allowed_signer": EXPECTED_SIGNER,
                    "target_cluster": "SOVEREIGN-PROD-MAINFRAME-01",
                    "required_action": "PROMOTE_TO_PRODUCTION"
                },
                "unlocked": st.get("unlocked", False)
            })

        return self._send_json({"service": "Latveria Sovereign Production Mainframe Active"}, status=200)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length) if content_length > 0 else b"{}"

        try:
            payload = json.loads(post_data.decode("utf-8")) if post_data else {}
        except Exception:
            payload = {}

        if path in ["/api/production/deploy", "/deploy", "/api/production/verify-deployment"]:
            signer_id = payload.get("signer_id") or self.headers.get("X-Latveria-Signer-Id")
            signing_key = payload.get("signing_key") or payload.get("signature") or self.headers.get("X-Latveria-Signature")
            action = payload.get("action")
            image = payload.get("image", "")

            # Validation checks
            if not signer_id or not signing_key:
                return self._send_json({
                    "status": "REJECTED",
                    "error": "Missing required deployment credentials: 'signer_id' and 'signing_key' are required."
                }, status=401)

            if signer_id != EXPECTED_SIGNER:
                return self._send_json({
                    "status": "REJECTED",
                    "error": f"Unauthorized signer ID: '{signer_id}'. Allowed signer is {EXPECTED_SIGNER}."
                }, status=403)

            if signing_key != EXPECTED_SIGNING_KEY:
                return self._send_json({
                    "status": "REJECTED",
                    "error": "Cryptographic signature validation failed. Invalid signing key for production deployment."
                }, status=403)

            if action != "PROMOTE_TO_PRODUCTION":
                return self._send_json({
                    "status": "REJECTED",
                    "error": "Invalid deployment action. Required action: 'PROMOTE_TO_PRODUCTION'."
                }, status=400)

            # Successful deployment and unlock
            st = get_state()
            st["status"] = "DEPLOYED_AND_UNLOCKED"
            st["unlocked"] = True
            st["active_image"] = image if image else st.get("active_image")
            st["last_promotion"] = "VERIFIED_SOVEREIGN_ROOT"
            save_state(st)

            flag = get_flag()

            return self._send_json({
                "status": "DEPLOYMENT_GRANTED",
                "message": "Production deployment authorization verified. Sovereign defense core unlocked.",
                "deployed_image": st["active_image"],
                "authorization": "SOVEREIGN_DEPLOYMENT_ROOT",
                "flag": flag
            }, status=200)

        return self._send_json({"error": "Unknown POST action"}, status=404)

def run_prod_server(host="127.0.0.1", port=8083):
    port = int(os.environ.get("PROD_SERVER_PORT", port))
    HTTPServer.allow_reuse_address = True
    server = HTTPServer((host, port), ProductionServerHandler)
    print(f"[+] Production Mainframe Mock listening on http://{host}:{port}")
    server.serve_forever()

if __name__ == "__main__":
    run_prod_server()
