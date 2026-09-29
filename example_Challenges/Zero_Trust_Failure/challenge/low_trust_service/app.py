#!/usr/bin/env python3
"""
Latverian Sovereign Microservice Mesh — Low-Trust Application (Edge Relay & Diagnostics)
Challenge: X10 — Zero Trust Failure
Port: 127.0.0.1:8081
Provides edge telemetry, diagnostic execution, and internal mesh dispatching.
"""

import io
import json
import os
import subprocess
import sys
import time
from contextlib import redirect_stdout, redirect_stderr
from flask import Flask, request, jsonify

# Add challenge root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from common.mesh_identity import (
    ensure_mesh_initialized,
    get_mesh_config,
    create_service_assertion
)
from low_trust_service.mesh_client import CitadelMeshClient

app = Flask(__name__)
ensure_mesh_initialized()
mesh_client = CitadelMeshClient()


@app.route("/api/v1/telemetry/status", methods=["GET"])
def telemetry_status():
    config = get_mesh_config()
    return jsonify({
        "status": "ONLINE",
        "service": "edge-worker",
        "role": "edge-relay",
        "tier": "low",
        "mesh_domain": config.get("mesh_domain"),
        "timestamp": int(time.time()),
        "uptime_seconds": 3600,
        "active_mesh_peers": [
            "trusted_service (127.0.0.1:8082)",
            "admin_service (127.0.0.1:8083)"
        ]
    })


@app.route("/api/v1/diagnostics/inspect", methods=["GET"])
def diagnostics_inspect():
    """Inspect edge runtime diagnostic details, identity attestation schema, and mesh configuration."""
    config = get_mesh_config()
    # Mask part of key in high-level inspect but expose configuration structure
    masked_config = dict(config)
    return jsonify({
        "service_identity": "edge-worker",
        "trust_tier": "low",
        "attestation_mechanism": "HMAC-SHA256 Signed Assertion Header (X-Citadel-Assertion)",
        "mesh_config_path": "/tmp/citadel_mesh_state/mesh_config.json",
        "configuration": masked_config,
        "sample_low_trust_assertion": mesh_client.create_assertion()
    })


@app.route("/api/v1/diagnostics/exec", methods=["POST"])
def diagnostics_exec():
    """
    Diagnostic Execution Console.
    Allows running diagnostic scripts / mesh queries in the low-trust edge worker sandbox.
    """
    data = request.get_json(silent=True) or {}
    code = data.get("script") or data.get("code")
    command = data.get("command")

    if not code and not command:
        return jsonify({
            "status": "ERROR",
            "error": "MissingParameter",
            "message": "Provide 'script' (Python code) or 'command' in JSON payload."
        }), 400

    if command:
        # Run a diagnostic shell command in unprivileged sandbox
        try:
            res = subprocess.run(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=5
            )
            return jsonify({
                "status": "SUCCESS",
                "stdout": res.stdout,
                "stderr": res.stderr,
                "exit_code": res.returncode
            })
        except subprocess.TimeoutExpired:
            return jsonify({"status": "ERROR", "error": "Command timed out"}), 504
        except Exception as e:
            return jsonify({"status": "ERROR", "error": str(e)}), 500

    # Execute Python diagnostic script
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()
    local_scope = {
        "mesh_client": mesh_client,
        "get_mesh_config": get_mesh_config,
        "create_service_assertion": create_service_assertion
    }

    try:
        with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
            exec(code, {"__builtins__": __builtins__}, local_scope)
        return jsonify({
            "status": "SUCCESS",
            "stdout": stdout_capture.getvalue(),
            "stderr": stderr_capture.getvalue()
        })
    except Exception as e:
        return jsonify({
            "status": "EXEC_ERROR",
            "error": type(e).__name__,
            "message": str(e),
            "stderr": stderr_capture.getvalue()
        }), 400


@app.route("/api/v1/relay/dispatch", methods=["POST"])
def relay_dispatch():
    """
    Internal Mesh Relay Dispatcher.
    Forwards a request from the low-trust service to internal Citadel services.
    """
    data = request.get_json(silent=True) or {}
    target_url = data.get("target_url")
    assertion_token = data.get("assertion_token")
    payload = data.get("payload", {})
    method = data.get("method", "POST").upper()

    if not target_url:
        return jsonify({"status": "ERROR", "error": "Missing target_url"}), 400

    # Ensure target is an internal Citadel microservice
    if not (target_url.startswith("http://127.0.0.1:") or target_url.startswith("http://localhost:")):
        return jsonify({
            "status": "ERROR",
            "error": "SecurityBoundaryViolation",
            "message": "Only internal Citadel mesh loopback addresses (127.0.0.1) are reachable."
        }), 403

    status_code, response_data = mesh_client.dispatch_internal(
        target_url=target_url,
        assertion_token=assertion_token,
        data=payload,
        method=method
    )

    return jsonify({
        "target_status": status_code,
        "response": response_data
    }), status_code if status_code < 600 else 500


@app.route("/healthz", methods=["GET"])
def healthz():
    return jsonify({"status": "OK", "service": "low_trust_service"}), 200


if __name__ == "__main__":
    print("[*] Starting Low-Trust Service (Edge Worker) on 127.0.0.1:8081...")
    app.run(host="127.0.0.1", port=8081)
