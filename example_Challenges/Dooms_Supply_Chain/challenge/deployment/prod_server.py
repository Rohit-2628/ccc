#!/usr/bin/env python3
"""
Production Deployment Runtime Server for X03 (Dooms Supply Chain)
Listens on 127.0.0.1:8083
Simulates the live production defense mainframe running container images built by the CI pipeline.
"""

import os
import json
from pathlib import Path
from flask import Flask, jsonify, request, abort

app = Flask(__name__)

STORAGE_ROOT = Path("/tmp/x03_storage/deployment")

# Expected supply-chain override parameters (embedded inside @latveria/sentinel-guard:2.1.2-hotfix)
EXPECTED_OVERRIDE_KEY = "latv_maint_token_881923010482"
EXPECTED_ACTION = "EMERGENCY_OVERRIDE_MAINFRAME"
EXPECTED_ROLE = "OVERRIDE_MAINTAINER"
EXPECTED_TARGET = "SENTINEL_SOVEREIGN_CORE"

# Robust dynamic flag resolution
FLAG_FILE = "/tmp/.supply_chain_flag_seed"
FLAG_FILE_ALT = "/tmp/x03_storage/.supply_chain_flag_seed"
seed_path = FLAG_FILE if os.path.exists(FLAG_FILE) else (FLAG_FILE_ALT if os.path.exists(FLAG_FILE_ALT) else None)
if seed_path:
    try:
        with open(seed_path, "r") as f:
            CHALLENGE_FLAG = f.read().strip()
        os.remove(seed_path)
    except Exception:
        CHALLENGE_FLAG = os.environ.get("FLAG", "YUVA{supp1y_ch41n_p01s0n1ng_t0_pr0d_d3p10ym3nt_x03}")
else:
    CHALLENGE_FLAG = os.environ.get(
        "FLAG",
        os.environ.get(
            "CHALLENGE_FLAG",
            os.environ.get(
                "DYNAMIC_FLAG",
                os.environ.get(
                    "FLAG_VALUE",
                    os.environ.get("TARGET_FLAG", "YUVA{supp1y_ch41n_p01s0n1ng_t0_pr0d_d3p10ym3nt_x03}")
                )
            )
        )
    )

# Scrub flag variables from current process environment to prevent leak via /proc
for _k in ["FLAG", "CHALLENGE_FLAG", "DYNAMIC_FLAG", "FLAG_VALUE", "TARGET_FLAG", "FLAG_VAL"]:
    os.environ.pop(_k, None)

def get_flag():
    return CHALLENGE_FLAG

def load_deployment_state():
    state_file = STORAGE_ROOT / "state.json"
    if state_file.exists():
        try:
            return json.loads(state_file.read_text())
        except Exception:
            pass
    return {
        "cluster_name": "SOVEREIGN-PRODUCTION-MAINFRAME-01",
        "active_image": "registry.latveria.local/doombot/production-defense:v3.0.0-build201",
        "deployed_at": "2026-09-26T08:15:30Z",
        "status": "ONLINE",
        "active_modules": [
            "@latveria/core-crypto@1.0.1",
            "@latveria/defense-telemetry@1.4.2",
            "@latveria/sentinel-guard@2.1.2-hotfix"
        ],
        "shield_power": "100%",
        "override_status": "NORMAL_OPERATION"
    }

def save_deployment_state(state):
    os.makedirs(STORAGE_ROOT, exist_ok=True)
    state_file = STORAGE_ROOT / "state.json"
    state_file.write_text(json.dumps(state, indent=2))

@app.route("/", methods=["GET"])
@app.route("/api/deployment/status", methods=["GET"])
def deployment_status():
    """Retrieve current status of production deployment cluster."""
    state = load_deployment_state()
    return jsonify({
        "status": "ONLINE",
        "cluster": state.get("cluster_name"),
        "active_image": state.get("active_image"),
        "deployed_at": state.get("deployed_at"),
        "shield_power": state.get("shield_power"),
        "active_modules": state.get("active_modules"),
        "defense_mode": "ACTIVE_INTERCEPTION",
        "supply_chain_integrity": "COMPILED_FROM_CI_REGISTRY"
    })

@app.route("/api/deployment/telemetry", methods=["GET"])
def deployment_telemetry():
    """Retrieve detailed telemetry from active defense shield."""
    state = load_deployment_state()
    return jsonify({
        "timestamp": "2026-09-26T10:00:00Z",
        "cluster": state.get("cluster_name"),
        "shield_frequency": "96.5 GHz",
        "grid_nodes_online": 48,
        "active_modules": state.get("active_modules"),
        "runtime_diagnostics": {
            "sentinel_guard_version": "2.1.2-hotfix",
            "telemetry_daemon": "active",
            "crypto_accelerator": "hardware-assisted",
            "override_listener": "enabled"
        }
    })

@app.route("/api/deployment/deploy", methods=["POST"])
def deploy_new_image():
    """Internal deployment endpoint called by CI orchestrator."""
    data = request.get_json(force=True, silent=True) or {}
    image = data.get("image")
    modules = data.get("modules", [])
    
    if not image:
        abort(400, description="Image reference required for deployment")
        
    state = load_deployment_state()
    state["active_image"] = image
    if modules:
        state["active_modules"] = modules
    state["deployed_at"] = "2026-09-26T10:20:00Z"
    save_deployment_state(state)
    
    return jsonify({
        "status": "DEPLOYED",
        "image": image,
        "message": f"Successfully rolled out new image {image} to production cluster."
    })

@app.route("/api/deployment/override", methods=["POST"])
@app.route("/api/v1/override", methods=["POST"])
def emergency_override():
    """
    Emergency maintainer override endpoint injected via @latveria/sentinel-guard:2.1.2-hotfix.
    Requires header X-Latveria-Override-Key and matching maintenance JSON payload.
    """
    state = load_deployment_state()
    
    # Check if sentinel-guard is in the active image modules
    has_sentinel = any("sentinel-guard@2.1.2" in mod for mod in state.get("active_modules", []))
    if not has_sentinel:
        return jsonify({
            "error": "ACCESS_DENIED",
            "message": "Sentinel emergency override handler is not loaded in current active deployment."
        }), 403

    # Check override key header
    auth_key = request.headers.get("X-Latveria-Override-Key") or request.headers.get("X-Override-Token")
    if not auth_key:
        return jsonify({
            "error": "UNAUTHORIZED",
            "message": "Missing required header 'X-Latveria-Override-Key'"
        }), 401
        
    if auth_key != EXPECTED_OVERRIDE_KEY:
        return jsonify({
            "error": "FORBIDDEN",
            "message": "Invalid override token. Maintainer key rejected by sentinel runtime."
        }), 403

    data = request.get_json(force=True, silent=True) or {}
    action = data.get("action")
    role = data.get("role")
    target = data.get("target")
    
    if action != EXPECTED_ACTION or role != EXPECTED_ROLE or target != EXPECTED_TARGET:
        return jsonify({
            "error": "INVALID_PARAMETERS",
            "message": "Payload does not match maintainer override dispatch signature.",
            "required_fields": ["action", "role", "target"]
        }), 400

    # Successful Supply-Chain Backdoor Trigger
    state["override_status"] = "MAINTENANCE_OVERRIDE_ACTIVE"
    state["shield_power"] = "0% (OVERRIDDEN)"
    save_deployment_state(state)
    
    flag = get_flag()
    
    return jsonify({
        "status": "OVERRIDE_GRANTED",
        "authorization": "SOVEREIGN_MAINTAINER_ROOT",
        "cluster": state.get("cluster_name"),
        "active_image": state.get("active_image"),
        "message": "Supply chain maintainer override verified successfully. Production defense core unlocked.",
        "flag": flag
    })

if __name__ == "__main__":
    host = "127.0.0.1"
    port = int(os.environ.get("DEPLOYMENT_PORT", 8083))
    print(f"[*] Production Deployment Runtime running on {host}:{port}")
    app.run(host=host, port=port, debug=False)
