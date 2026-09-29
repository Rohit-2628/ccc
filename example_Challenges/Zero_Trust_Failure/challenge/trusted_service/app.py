#!/usr/bin/env python3
"""
Latverian Sovereign Microservice Mesh — Trusted Internal Service (Citadel Core Policy Engine)
Challenge: X10 — Zero Trust Failure
Port: 127.0.0.1:8082
Enforces service assertion verification and grants privileged admin tickets to authorized identities.
"""

import os
import sys
import time
from flask import Flask, request, jsonify

# Add challenge root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from common.mesh_identity import (
    ensure_mesh_initialized,
    verify_service_assertion,
    issue_admin_ticket
)

app = Flask(__name__)
ensure_mesh_initialized()


@app.route("/api/v1/core/status", methods=["GET"])
def core_status():
    return jsonify({
        "status": "ONLINE",
        "service": "citadel-core-policy",
        "role": "mesh-policy-enforcer",
        "trust_level": "HIGH_PRIVILEGE",
        "identity_verification": "HMAC-SHA256 Challenge-Local Mesh Attestation",
        "timestamp": int(time.time())
    })


@app.route("/api/v1/core/telemetry/report", methods=["POST"])
def telemetry_report():
    assertion = request.headers.get("X-Citadel-Assertion", "")
    is_valid, payload, reason = verify_service_assertion(assertion)
    if not is_valid:
        return jsonify({
            "status": "UNAUTHORIZED",
            "error": "InvalidAssertion",
            "message": f"Mesh assertion rejection: {reason}"
        }), 401

    return jsonify({
        "status": "ACCEPTED",
        "service": payload.get("service_id"),
        "tier": payload.get("tier"),
        "message": "Telemetry metrics recorded by Core Policy Engine."
    })


@app.route("/api/v1/core/request-admin-ticket", methods=["POST", "GET"])
@app.route("/api/v1/core/admin-grant", methods=["POST", "GET"])
def admin_grant():
    """
    Issue Admin Grant Ticket to authorized high-privilege service identities.
    Flawed assumption: Service assumes anyone with a valid mesh signature is authorized
    to assert whatever service identity is contained in the payload.
    """
    assertion = request.headers.get("X-Citadel-Assertion", "")
    if not assertion:
        # Check Authorization header fallback
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            assertion = auth[7:]

    if not assertion:
        return jsonify({
            "status": "UNAUTHORIZED",
            "error": "MissingAssertion",
            "message": "Header 'X-Citadel-Assertion' missing. Provide signed mesh assertion token."
        }), 401

    is_valid, payload, reason = verify_service_assertion(assertion)
    if not is_valid:
        return jsonify({
            "status": "UNAUTHORIZED",
            "error": "InvalidAssertion",
            "message": f"Cryptographic verification failed: {reason}"
        }), 401

    service_id = payload.get("service_id", "unknown")
    role = payload.get("role", "unknown")
    tier = payload.get("tier", "low")
    capabilities = payload.get("capabilities", [])

    # Check privilege tier
    if tier == "low" or service_id == "edge-worker":
        return jsonify({
            "status": "FORBIDDEN",
            "error": "InsufficientPrivilege",
            "identity": service_id,
            "tier": tier,
            "message": f"Identity '{service_id}' with tier '{tier}' is not authorized for Admin Grant. Required: 'core-orchestrator' or tier 'autonomous-kernel'."
        }), 403

    if service_id == "core-orchestrator" or tier == "autonomous-kernel" or "core:admin" in capabilities:
        # Generate Admin Ticket
        ticket_id = issue_admin_ticket(service_id=service_id, tier=tier)
        return jsonify({
            "status": "GRANTED",
            "access_tier": "AUTONOMOUS_KERNEL",
            "identity": service_id,
            "role": role,
            "message": "Citadel Core Policy verification successful. Admin Ticket minted.",
            "admin_ticket": ticket_id,
            "admin_service_endpoint": "http://127.0.0.1:8083/api/v1/admin/unseal"
        }), 200

    return jsonify({
        "status": "FORBIDDEN",
        "error": "UnrecognizedIdentity",
        "message": f"Service identity '{service_id}' does not match authorized Citadel admin profiles."
    }), 403


@app.route("/healthz", methods=["GET"])
def healthz():
    return jsonify({"status": "OK", "service": "trusted_service"}), 200


if __name__ == "__main__":
    print("[*] Starting Trusted Internal Service (Core Policy Engine) on 127.0.0.1:8082...")
    app.run(host="127.0.0.1", port=8082)
