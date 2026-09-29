#!/usr/bin/env python3
"""
Latverian Sovereign Microservice Mesh — Zero-Trust Identity & Attestation Core
Challenge: X10 — Zero Trust Failure
Challenge-local service identity assertion generation, cryptographic verification, and state lifecycle.
"""

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from typing import Any, Dict, List, Optional, Tuple

STATE_DIR = os.environ.get("STATE_DIR", "/tmp/citadel_mesh_state")
CONFIG_FILE = os.path.join(STATE_DIR, "mesh_config.json")
TICKETS_FILE = os.path.join(STATE_DIR, "admin_tickets.json")

DEFAULT_FLAG = "YUVA{z3r0_trust_f41lur3_s3rv1c3_1d3nt1ty_x10}"
_CACHED_FLAG: Optional[str] = None


def get_current_flag() -> str:
    """Retrieve dynamic instance-scoped flag."""
    global _CACHED_FLAG
    if _CACHED_FLAG is not None:
        return _CACHED_FLAG

    seed_file = "/tmp/.citadel_flag_seed"
    if os.path.exists(seed_file):
        try:
            with open(seed_file, "r") as f:
                _CACHED_FLAG = f.read().strip()
            os.remove(seed_file)
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
                        os.environ.get("TARGET_FLAG", DEFAULT_FLAG)
                    )
                )
            )
        ).strip()

    # Scrub flag variables from current process environment
    for _k in ["FLAG", "CHALLENGE_FLAG", "DYNAMIC_FLAG", "FLAG_VALUE", "TARGET_FLAG", "FLAG_VAL"]:
        os.environ.pop(_k, None)

    return _CACHED_FLAG


def ensure_mesh_initialized() -> Dict[str, Any]:
    """Ensure mesh configuration and challenge-local signing key are initialized."""
    os.makedirs(STATE_DIR, exist_ok=True)

    if not os.path.exists(CONFIG_FILE):
        # Generate challenge-local mesh signing key and configuration
        mesh_key = f"latv_mesh_key_{secrets.token_hex(24)}"
        initial_config = {
            "mesh_domain": "latveria.citadel.mesh",
            "version": "v3.2-ZeroTrustEnclave",
            "mesh_signing_key": mesh_key,
            "signature_algorithm": "HMAC-SHA256",
            "default_edge_identity": {
                "service_id": "edge-worker",
                "role": "edge-relay",
                "tier": "low",
                "capabilities": ["telemetry:read", "diagnostics:run", "relay:proxy"]
            },
            "authorized_core_identity": {
                "service_id": "core-orchestrator",
                "role": "citadel-orchestrator",
                "tier": "autonomous-kernel",
                "capabilities": ["core:admin", "vault:unseal", "system:override"]
            },
            "internal_endpoints": {
                "gateway": "http://127.0.0.1:80",
                "low_trust_app": "http://127.0.0.1:8081",
                "trusted_service": "http://127.0.0.1:8082",
                "admin_service": "http://127.0.0.1:8083"
            }
        }
        with open(CONFIG_FILE, "w") as f:
            json.dump(initial_config, f, indent=2)

    if not os.path.exists(TICKETS_FILE):
        with open(TICKETS_FILE, "w") as f:
            json.dump({}, f)

    with open(CONFIG_FILE, "r") as f:
        return json.load(f)


def get_mesh_config() -> Dict[str, Any]:
    """Get active mesh configuration."""
    if not os.path.exists(CONFIG_FILE):
        return ensure_mesh_initialized()
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)


def create_service_assertion(
    service_id: str,
    role: str,
    tier: str,
    capabilities: List[str],
    ttl: int = 3600
) -> str:
    """
    Generate a challenge-local service identity assertion token.
    Format: base64(json_payload) . hmac_sha256(payload_b64, mesh_signing_key)
    """
    config = get_mesh_config()
    mesh_key = config.get("mesh_signing_key", "").encode("utf-8")

    now = int(time.time())
    payload = {
        "service_id": service_id,
        "role": role,
        "tier": tier,
        "capabilities": capabilities,
        "trust_domain": config.get("mesh_domain", "latveria.citadel.mesh"),
        "iat": now,
        "exp": now + ttl,
        "nonce": secrets.token_hex(8)
    }

    payload_json = json.dumps(payload, separators=(',', ':'), sort_keys=True)
    payload_b64 = base64.urlsafe_b64encode(payload_json.encode("utf-8")).decode("utf-8").rstrip("=")

    signature = hmac.new(mesh_key, payload_b64.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{payload_b64}.{signature}"


def verify_service_assertion(assertion_token: str) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """
    Cryptographically verify a service identity assertion using the challenge-local mesh key.
    Returns: (is_valid, payload_dict, reason)
    """
    if not assertion_token or "." not in assertion_token:
        return False, None, "Malformed assertion token format. Expected: <payload_b64>.<signature_hex>"

    parts = assertion_token.strip().split(".")
    if len(parts) != 2:
        return False, None, "Invalid token structure"

    payload_b64, signature = parts[0], parts[1]

    config = get_mesh_config()
    mesh_key = config.get("mesh_signing_key", "").encode("utf-8")

    # Recompute HMAC signature
    expected_sig = hmac.new(mesh_key, payload_b64.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected_sig):
        return False, None, "Invalid assertion signature: cryptographic HMAC verification failed"

    # Decode and parse payload
    try:
        # Add padding if needed
        padding = "=" * ((4 - len(payload_b64) % 4) % 4)
        payload_bytes = base64.urlsafe_b64decode(payload_b64 + padding)
        payload = json.loads(payload_bytes.decode("utf-8"))
    except Exception as e:
        return False, None, f"Failed to parse assertion payload: {str(e)}"

    # Check expiration
    now = int(time.time())
    if payload.get("exp", 0) < now:
        return False, None, "Service assertion token has expired"

    return True, payload, "Valid"


def issue_admin_ticket(service_id: str, tier: str) -> str:
    """Issue a single-use Citadel Admin Ticket."""
    os.makedirs(STATE_DIR, exist_ok=True)
    ticket_id = f"LATV-ADMIN-PASS-{secrets.token_hex(20).upper()}"
    
    tickets = {}
    if os.path.exists(TICKETS_FILE):
        try:
            with open(TICKETS_FILE, "r") as f:
                tickets = json.load(f)
        except Exception:
            tickets = {}

    tickets[ticket_id] = {
        "issued_to": service_id,
        "tier": tier,
        "issued_at": int(time.time()),
        "used": False
    }

    with open(TICKETS_FILE, "w") as f:
        json.dump(tickets, f, indent=2)

    return ticket_id


def validate_and_consume_admin_ticket(ticket_id: str) -> Tuple[bool, str]:
    """Validate Admin Ticket and unlock the vault."""
    if not os.path.exists(TICKETS_FILE):
        return False, "No active admin tickets found"

    try:
        with open(TICKETS_FILE, "r") as f:
            tickets = json.load(f)
    except Exception:
        return False, "Ticket storage corrupted"

    ticket = tickets.get(ticket_id)
    if not ticket:
        return False, "Invalid or unrecognized admin ticket"

    if ticket.get("used", False):
        return False, "Admin ticket has already been consumed"

    # Mark as used
    ticket["used"] = True
    ticket["consumed_at"] = int(time.time())
    tickets[ticket_id] = ticket

    with open(TICKETS_FILE, "w") as f:
        json.dump(tickets, f, indent=2)

    return True, "Ticket verified successfully"


def reset_mesh_state():
    """Wipe and regenerate mesh signing key and clear tickets for challenge reset."""
    if os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)
    if os.path.exists(TICKETS_FILE):
        os.remove(TICKETS_FILE)
    ensure_mesh_initialized()
