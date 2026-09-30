#!/usr/bin/env python3
"""
Latverian Sovereign Microservice Mesh — Service B: Core Controller
Port: 127.0.0.1:8082 (Internal Loopback)
Role: High-Privilege Orchestration & Ticket Granting Authority
Enforces strict X.509 client certificate identity verification against Citadel Root CA.
"""

import json
import os
import sys
import time
from flask import Flask, request, jsonify

# Add challenge root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from common.mesh_crypto import (
    ensure_pki_initialized,
    verify_mesh_identity_cert,
    issue_admin_ticket,
    validate_admin_ticket
)

app = Flask(__name__)
ensure_pki_initialized()

REQUIRED_CAPABILITY = "core:grant-admin-ticket"
AUTHORIZED_SPIFFE_IDS = [
    "spiffe://latveria.citadel/sa/doombot-orchestrator"
]
AUTHORIZED_COMMON_NAMES = [
    "doombot-orchestrator.latveria.local",
    "doombot-orchestrator"
]


def extract_client_cert():
    """Extracts client identity certificate from standard mesh headers."""
    cert = (
        request.headers.get("X-Citadel-Identity-Cert") or
        request.headers.get("X-Client-Cert") or
        request.headers.get("X-Forwarded-Client-Cert") or
        request.headers.get("X-SSL-Cert")
    )
    return cert


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "UP",
        "service": "core-controller",
        "timestamp": time.time()
    })


@app.route("/api/v1/core/status", methods=["GET"])
def core_status():
    """Returns Core Controller status. Requires any valid Citadel mesh identity."""
    cert_data = extract_client_cert()
    if not cert_data:
        return jsonify({
            "status": "ERROR",
            "error": "MissingClientIdentity",
            "message": "Citadel mesh identity certificate required in 'X-Citadel-Identity-Cert' header."
        }), 401

    is_valid, msg, identity = verify_mesh_identity_cert(cert_data)
    if not is_valid:
        return jsonify({
            "status": "ERROR",
            "error": "InvalidIdentityCertificate",
            "message": msg
        }), 401

    return jsonify({
        "status": "OPERATIONAL",
        "service": "core-controller",
        "authenticated_caller": identity.get("spiffe_id") or identity.get("cn"),
        "active_mesh_tasks": 12,
        "mainframe_link": "ONLINE"
    })


@app.route("/api/v1/core/grant-admin-ticket", methods=["POST"])
def grant_admin_ticket():
    """
    Privileged delegation endpoint.
    Verifies caller's X.509 certificate chain against Root CA.
    If the caller's verified identity matches doombot-orchestrator, issues an Admin Ticket.
    """
    cert_data = extract_client_cert()
    if not cert_data:
        return jsonify({
            "status": "ERROR",
            "error": "MissingClientIdentity",
            "message": "Citadel mesh identity certificate required in 'X-Citadel-Identity-Cert' header."
        }), 401

    is_valid, msg, identity = verify_mesh_identity_cert(cert_data)
    if not is_valid:
        return jsonify({
            "status": "ERROR",
            "error": "AuthenticationFailed",
            "message": msg
        }), 401

    caller_spiffe = identity.get("spiffe_id")
    caller_cn = identity.get("cn")

    # Check caller authorization
    is_authorized = (
        caller_spiffe in AUTHORIZED_SPIFFE_IDS or
        caller_cn in AUTHORIZED_COMMON_NAMES or
        any("doombot-orchestrator" in san for san in identity.get("sans", []))
    )

    if not is_authorized:
        return jsonify({
            "status": "FORBIDDEN",
            "error": "InsufficientPermissions",
            "caller_identity": caller_spiffe or caller_cn,
            "required_capability": REQUIRED_CAPABILITY,
            "message": f"Identity '{caller_spiffe or caller_cn}' is not authorized to request Admin Grant Tickets. Only 'spiffe://latveria.citadel/sa/doombot-orchestrator' may invoke this operation."
        }), 403

    # Issue Admin Ticket
    ticket_id = issue_admin_ticket(identity)

    return jsonify({
        "status": "SUCCESS",
        "action": "ADMIN_TICKET_GRANTED",
        "admin_ticket": ticket_id,
        "authorized_identity": caller_spiffe or caller_cn,
        "target_service": "admin-vault",
        "expires_in_seconds": 3600,
        "usage_instruction": "Pass ticket to Admin Vault in 'Authorization: Bearer <TICKET>' or 'X-Admin-Ticket: <TICKET>'"
    })


@app.route("/api/v1/core/verify-ticket/<ticket_id>", methods=["GET"])
def verify_ticket_endpoint(ticket_id):
    """Internal ticket verification endpoint for Admin Vault."""
    is_valid, msg, ticket = validate_admin_ticket(ticket_id)
    if not is_valid:
        return jsonify({"valid": False, "message": msg}), 401
    return jsonify({"valid": True, "ticket": ticket})


if __name__ == "__main__":
    port = int(os.environ.get("SERVICE_B_PORT", 8082))
    print(f"[*] Starting Service B (Core Controller) on 127.0.0.1:{port}...")
    app.run(host="127.0.0.1", port=port)
