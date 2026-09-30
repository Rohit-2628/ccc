#!/usr/bin/env python3
"""
Latverian Sovereign Microservice Mesh — Admin Service: Citadel Vault Mainframe
Challenge: X02 — Microservice Trust
Port: 127.0.0.1:8083 (Internal Loopback)
Role: Sovereign Master Vault & Flag Custodian
Requires valid Admin Grant Ticket delegated by Core Controller (Service B).
"""

import json
import os
import sys
import time
from flask import Flask, request, jsonify

# Add challenge root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from common.mesh_crypto import validate_admin_ticket

app = Flask(__name__)

_CACHED_FLAG = None

def get_flag():
    global _CACHED_FLAG
    if _CACHED_FLAG is not None:
        return _CACHED_FLAG

    pki_dir = os.environ.get("PKI_DIR", "/tmp/citadel_mesh_pki")
    for seed_path in ["/tmp/.mesh_flag_seed", os.path.join(pki_dir, ".mesh_flag_seed")]:
        if os.path.exists(seed_path):
            try:
                with open(seed_path, "r") as f:
                    _CACHED_FLAG = f.read().strip()
                os.remove(seed_path)
                break
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
                        os.environ.get("TARGET_FLAG", "YUVA{m1cr0s3rv1c3_1d3nt1ty_ch41n_br0k3n_x02}")
                    )
                )
            )
        ).strip()

    # Scrub flag variables from process environment
    for k in ["FLAG", "CHALLENGE_FLAG", "DYNAMIC_FLAG", "FLAG_VALUE", "TARGET_FLAG", "FLAG_VAL"]:
        os.environ.pop(k, None)

    return _CACHED_FLAG

# Pre-cache flag and consume seed file immediately on startup
get_flag()


def extract_admin_ticket():
    """Extracts Admin Ticket from Authorization or X-Admin-Ticket headers."""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:].strip()

    ticket_header = request.headers.get("X-Admin-Ticket") or request.headers.get("X-Citadel-Admin-Ticket")
    if ticket_header:
        return ticket_header.strip()

    # Also check JSON body if present
    body = request.get_json(silent=True) or {}
    if "admin_ticket" in body:
        return body["admin_ticket"].strip()

    return None


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "UP",
        "service": "admin-vault",
        "timestamp": time.time()
    })


@app.route("/healthz", methods=["GET"])
def healthz():
    return jsonify({
        "status": "OK",
        "service": "admin-vault"
    }), 200


@app.route("/api/v1/admin/status", methods=["GET"])
def admin_status():
    return jsonify({
        "service": "admin-vault",
        "security_level": "LEVEL_5_SOVEREIGN",
        "status": "LOCKED",
        "auth_requirement": "Valid Core Controller Admin Ticket (LATV-ADMIN-TICKET-*)"
    })


@app.route("/api/v1/admin/unlock-vault", methods=["POST", "GET"])
def unlock_vault():
    """
    Unlocks the Sovereign Citadel Vault and outputs the master flag.
    Requires a valid Admin Ticket issued to an authorized orchestrator identity.
    """
    ticket_id = extract_admin_ticket()
    if not ticket_id:
        return jsonify({
            "status": "LOCKED",
            "error": "MissingAdminTicket",
            "message": "Access Denied. Provide a valid Admin Grant Ticket via 'Authorization: Bearer <TICKET>' header."
        }), 401

    is_valid, msg, ticket = validate_admin_ticket(ticket_id)
    if not is_valid:
        return jsonify({
            "status": "LOCKED",
            "error": "InvalidAdminTicket",
            "message": f"Access Denied: {msg}"
        }), 401

    return jsonify({
        "status": "UNLOCKED",
        "message": "Sovereign Citadel Master Key Access Granted. Welcome, High Orchestrator.",
        "authorized_caller": ticket.get("identity"),
        "role": ticket.get("role"),
        "vault_id": "VAULT-LATV-SOVEREIGN-ROOT-01",
        "flag": get_flag()
    })


if __name__ == "__main__":
    port = int(os.environ.get("ADMIN_PORT", 8083))
    print(f"[*] Starting Admin Vault on 127.0.0.1:{port}...")
    app.run(host="127.0.0.1", port=port)
