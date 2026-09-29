#!/usr/bin/env python3
"""
Latverian Sovereign Microservice Mesh — Citadel Admin Vault & Flag Custodian
Challenge: X10 — Zero Trust Failure
Port: 127.0.0.1:8083
Protects the Sovereign Flag behind Admin Ticket authorization.
"""

import os
import sys
import time
from flask import Flask, request, jsonify

# Add challenge root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from common.mesh_identity import (
    ensure_mesh_initialized,
    validate_and_consume_admin_ticket,
    get_current_flag
)

app = Flask(__name__)
ensure_mesh_initialized()
# Pre-cache flag and consume seed file immediately on startup
get_current_flag()


@app.route("/api/v1/admin/status", methods=["GET"])
def admin_status():
    return jsonify({
        "status": "SEALED",
        "service": "citadel-admin-vault",
        "role": "sovereign-vault-custodian",
        "trust_tier": "SOVEREIGN_ROOT",
        "unseal_requirement": "LATV-ADMIN-PASS-* Ticket (issued by Trusted Core Engine)",
        "timestamp": int(time.time())
    })


@app.route("/api/v1/admin/unseal", methods=["POST"])
def admin_unseal():
    # Check ticket from Authorization header or X-Admin-Ticket header or JSON payload
    ticket = request.headers.get("X-Admin-Ticket", "")
    if not ticket:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            ticket = auth[7:].strip()

    if not ticket:
        data = request.get_json(silent=True) or {}
        ticket = data.get("admin_ticket", "")

    if not ticket:
        return jsonify({
            "status": "UNAUTHORIZED",
            "error": "MissingAdminTicket",
            "message": "Header 'X-Admin-Ticket' or 'Authorization: Bearer <TICKET>' is required to unseal the vault."
        }), 401

    is_valid, msg = validate_and_consume_admin_ticket(ticket)
    if not is_valid:
        return jsonify({
            "status": "FORBIDDEN",
            "error": "TicketInvalidOrConsumed",
            "message": f"Vault unseal denied: {msg}"
        }), 403

    flag = get_current_flag()
    return jsonify({
        "status": "UNSEALED",
        "vault_state": "OPEN",
        "access_level": "SOVEREIGN_ROOT",
        "message": "Citadel Sovereign Vault unsealed. Autonomous kernel authorization verified.",
        "flag": flag
    }), 200


@app.route("/healthz", methods=["GET"])
def healthz():
    return jsonify({"status": "OK", "service": "admin_service"}), 200


if __name__ == "__main__":
    print("[*] Starting Admin Service (Citadel Sovereign Vault) on 127.0.0.1:8083...")
    app.run(host="127.0.0.1", port=8083)
