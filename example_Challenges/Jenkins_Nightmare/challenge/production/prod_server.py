#!/usr/bin/env python3
"""
Latverian Sovereign Defense Grid — Production Mock Mainframe Server
Runs on private internal loopback (127.0.0.1:8081).
Requires HMAC-SHA256 authenticated production deployment requests with agent ID.
"""

import hmac
import hashlib
import json
import os
import sys
from flask import Flask, request, jsonify

app = Flask(__name__)

# Master credentials (loaded from env or synthetic default)
PROD_MASTER_KEY = os.environ.get("PROD_MASTER_KEY", "latv_prod_master_sec_9918230184719204").encode("utf-8")
AUTHORIZED_AGENT_ID = os.environ.get("AUTHORIZED_AGENT_ID", "DOOM-PROD-ORCHESTRATOR-01")

# Robust dynamic flag resolution
FLAG_FILE = "/tmp/.prod_flag_seed"
if os.path.exists(FLAG_FILE):
    try:
        with open(FLAG_FILE, "r") as f:
            CHALLENGE_FLAG = f.read().strip()
        os.remove(FLAG_FILE)
    except Exception:
        CHALLENGE_FLAG = os.environ.get("FLAG", "YUVA{c1_cd_ch41n_0f_trust_c0mpr0m1s3d_x01}")
else:
    CHALLENGE_FLAG = os.environ.get(
        "FLAG",
        os.environ.get(
            "CHALLENGE_FLAG",
            os.environ.get(
                "DYNAMIC_FLAG",
                os.environ.get(
                    "FLAG_VALUE",
                    os.environ.get("TARGET_FLAG", "YUVA{c1_cd_ch41n_0f_trust_c0mpr0m1s3d_x01}")
                )
            )
        )
    )

# Scrub flag variables from current process environment to prevent leak via /proc
for _k in ["FLAG", "CHALLENGE_FLAG", "DYNAMIC_FLAG", "FLAG_VALUE", "TARGET_FLAG", "FLAG_VAL"]:
    os.environ.pop(_k, None)

@app.route("/", methods=["GET"])
def index():
    return jsonify({
        "service": "Latveria Production Sovereign Core Mainframe",
        "status": "ONLINE",
        "state": "ENFORCING_DEFENSE_GRID",
        "version": "v1.0.0-production-isolated"
    })

@app.route("/api/v1/health", methods=["GET"])
def health():
    return jsonify({"status": "HEALTHY", "environment": "PRODUCTION_SECURE"})

@app.route("/api/v1/production/unlock", methods=["POST"])
def unlock_production():
    deploy_agent = request.headers.get("X-Latveria-Deploy-Agent")
    signature = request.headers.get("X-Latveria-Signature")

    if not deploy_agent:
        return jsonify({
            "status": "ACCESS_DENIED",
            "error": "Missing header: X-Latveria-Deploy-Agent"
        }), 401

    if deploy_agent != AUTHORIZED_AGENT_ID:
        return jsonify({
            "status": "ACCESS_DENIED",
            "error": f"Unauthorized deploy agent '{deploy_agent}'. Access restricted to '{AUTHORIZED_AGENT_ID}'."
        }), 403

    if not signature:
        return jsonify({
            "status": "ACCESS_DENIED",
            "error": "Missing header: X-Latveria-Signature (HMAC-SHA256 required)"
        }), 401

    raw_body = request.get_data()
    expected_sig = hmac.new(PROD_MASTER_KEY, raw_body, hashlib.sha256).hexdigest()

    if not hmac.compare_digest(signature.lower(), expected_sig.lower()):
        return jsonify({
            "status": "ACCESS_DENIED",
            "error": "Invalid HMAC-SHA256 signature for payload."
        }), 403

    try:
        data = json.loads(raw_body.decode("utf-8")) if raw_body else {}
    except Exception:
        return jsonify({"status": "BAD_REQUEST", "error": "Invalid JSON body"}), 400

    action = data.get("action")
    target = data.get("target")

    if action != "OVERRIDE_PRODUCTION_MAINFRAME" or target != "SOVEREIGN_CORE":
        return jsonify({
            "status": "REJECTED",
            "error": "Required payload fields: {'action': 'OVERRIDE_PRODUCTION_MAINFRAME', 'target': 'SOVEREIGN_CORE'}"
        }), 400

    return jsonify({
        "status": "AUTHORIZATION_VERIFIED",
        "message": "Sovereign defense mainframe production override granted.",
        "deploy_agent": deploy_agent,
        "flag": CHALLENGE_FLAG
    }), 200

if __name__ == "__main__":
    port = int(os.environ.get("PROD_PORT", 8081))
    print(f"[*] Starting Production Mock Mainframe on 127.0.0.1:{port}")
    app.run(host="127.0.0.1", port=port, debug=False)
