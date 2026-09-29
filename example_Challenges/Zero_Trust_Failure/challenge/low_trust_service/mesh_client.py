#!/usr/bin/env python3
"""
Latverian Sovereign Microservice Mesh — Low-Trust Edge Mesh Client
Challenge: X10 — Zero Trust Failure
Library used by Low-Trust Edge Worker to sign identity assertions and communicate with Citadel microservices.
"""

import json
import os
import sys
import urllib.request
import urllib.error

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from common.mesh_identity import (
    create_service_assertion,
    get_mesh_config
)


class CitadelMeshClient:
    def __init__(self):
        self.config = get_mesh_config()
        self.default_identity = self.config.get("default_edge_identity", {})

    def create_assertion(self, service_id: str = None, role: str = None, tier: str = None, capabilities: list = None):
        """Generate a signed service identity assertion token."""
        svc_id = service_id or self.default_identity.get("service_id", "edge-worker")
        svc_role = role or self.default_identity.get("role", "edge-relay")
        svc_tier = tier or self.default_identity.get("tier", "low")
        svc_caps = capabilities or self.default_identity.get("capabilities", ["telemetry:read"])
        return create_service_assertion(svc_id, svc_role, svc_tier, svc_caps)

    def dispatch_internal(self, target_url: str, assertion_token: str = None, data: dict = None, method: str = "POST"):
        """Send a mesh request to an internal Citadel microservice with identity assertion."""
        token = assertion_token or self.create_assertion()
        headers = {
            "Content-Type": "application/json",
            "X-Citadel-Assertion": token
        }
        body = json.dumps(data or {}).encode("utf-8") if method in ["POST", "PUT"] else None

        req = urllib.request.Request(target_url, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                return response.status, json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            try:
                err_body = json.loads(e.read().decode("utf-8"))
            except Exception:
                err_body = {"error": "HTTPError", "status": e.code}
            return e.code, err_body
        except Exception as e:
            return 500, {"error": str(e)}
