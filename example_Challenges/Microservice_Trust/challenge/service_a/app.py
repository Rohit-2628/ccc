#!/usr/bin/env python3
"""
Latverian Sovereign Microservice Mesh — Service A: Edge Telemetry Agent
Port: 127.0.0.1:8081 (Internal Loopback)
Role: Low-Trust Edge Diagnostics & Telemetry Collector
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
    get_ca_cert_pem,
    get_service_a_cert_pem,
    get_service_a_key_pem
)

app = Flask(__name__)
ensure_pki_initialized()

SERVICE_CONFIG = {
    "service_id": "doombot-telemetry-agent",
    "cluster_node": "latv-edge-node-04.internal",
    "role": "telemetry-agent",
    "spiffe_id": "spiffe://latveria.citadel/sa/telemetry-agent",
    "trust_domain": "latveria.citadel",
    "mesh_version": "v2.4.1-sovereign",
    "internal_topology": {
        "gateway": "http://127.0.0.1:80",
        "service_a_telemetry": "http://127.0.0.1:8081",
        "service_b_core_controller": "http://127.0.0.1:8082",
        "admin_vault_mainframe": "http://127.0.0.1:8083"
    },
    "authentication_spec": {
        "protocol": "Citadel Microservice Identity Assertion",
        "identity_header": "X-Citadel-Identity-Cert",
        "root_ca_authority": "CN=Latveria Citadel Root CA",
        "allowed_capabilities": {
            "spiffe://latveria.citadel/sa/telemetry-agent": [
                "telemetry:read",
                "telemetry:write",
                "diagnostics:probe"
            ],
            "spiffe://latveria.citadel/sa/doombot-orchestrator": [
                "telemetry:read",
                "telemetry:write",
                "core:grant-admin-ticket",
                "core:orchestrate",
                "admin:vault-unlock"
            ]
        }
    }
}


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "UP",
        "service": "doombot-telemetry-agent",
        "timestamp": time.time()
    })


@app.route("/api/v1/telemetry/status", methods=["GET"])
def telemetry_status():
    return jsonify({
        "node": SERVICE_CONFIG["cluster_node"],
        "service": SERVICE_CONFIG["service_id"],
        "identity": SERVICE_CONFIG["spiffe_id"],
        "status": "OPERATIONAL",
        "mesh_metrics": {
            "cpu_utilization": "14.2%",
            "memory_usage": "184MB / 1024MB",
            "active_mesh_peers": 4,
            "citadel_grid_power": "99.8%",
            "doombot_units_online": 128
        }
    })


@app.route("/api/v1/telemetry/config", methods=["GET"])
def telemetry_config():
    """Returns the internal service mesh configuration and endpoint routing."""
    return jsonify(SERVICE_CONFIG)


@app.route("/api/v1/diagnostics/export", methods=["GET"])
def diagnostics_export():
    """
    Diagnostic support bundle endpoint.
    Exposes Service A's internal mesh credentials and policy descriptor for local debugging.
    """
    try:
        ca_cert = get_ca_cert_pem()
        service_cert = get_service_a_cert_pem()
        service_key = get_service_a_key_pem()

        return jsonify({
            "status": "SUCCESS",
            "bundle_type": "CITADEL_EDGE_DIAGNOSTIC_BUNDLE",
            "service_id": SERVICE_CONFIG["service_id"],
            "spiffe_id": SERVICE_CONFIG["spiffe_id"],
            "mesh_policy": SERVICE_CONFIG["authentication_spec"],
            "credentials": {
                "ca_certificate": ca_cert,
                "service_certificate": service_cert,
                "service_private_key": service_key
            },
            "security_notice": "Citadel internal credentials must be kept secure. Verified callers must present their certificate chain in X-Citadel-Identity-Cert."
        })
    except Exception as e:
        return jsonify({"status": "ERROR", "message": str(e)}), 500


@app.route("/api/v1/diagnostics/probe", methods=["POST"])
def diagnostics_probe():
    data = request.get_json(silent=True) or {}
    target = data.get("target", "service_b")
    return jsonify({
        "status": "PROBE_ACK",
        "target": target,
        "caller_identity": SERVICE_CONFIG["spiffe_id"],
        "latency_ms": 0.42
    })


if __name__ == "__main__":
    port = int(os.environ.get("SERVICE_A_PORT", 8081))
    print(f"[*] Starting Service A (Telemetry Agent) on 127.0.0.1:{port}...")
    app.run(host="127.0.0.1", port=port)
