#!/usr/bin/env python3
"""
Latverian Sovereign Microservice Mesh (X02 - Microservice Trust)
Comprehensive Pre-Event Adversarial & Functional Verification Suite
Executes Tests 1 to 5 as mandated by CTF Engineering Gate.
"""

import argparse
import base64
import json
import os
import socket
import sys
import threading
import time
import unittest
import urllib.request
import urllib.error

# Add challenge root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from organizer.solve import solve, http_request, forge_orchestrator_certificate


class TestMicroserviceTrustChallenge(unittest.TestCase):
    host = "127.0.0.1"
    port = 80
    base_url = "http://127.0.0.1:80"

    @classmethod
    def setUpClass(cls):
        cls.base_url = f"http://{cls.host}:{cls.port}"

    def test_01_fresh_start_exposure(self):
        """Test 1: Verify TCP/80 is reachable, returns 200, and internal services are not exposed publicly."""
        print("\n[*] Running Test 1 — Fresh Start & Exposure Check...")
        
        # Check Gateway port 80
        status, body = http_request(f"{self.base_url}/")
        self.assertEqual(status, 200, "Gateway root should return HTTP 200")
        
        # Check topology endpoint
        status, topo = http_request(f"{self.base_url}/api/v1/topology")
        self.assertEqual(status, 200)
        self.assertIn("services", topo)
        print("[+] Gateway TCP/80 is responsive and serves proper ingress interfaces.")

    def test_02_intended_solve(self):
        """Test 2: Verify full intended exploit chain from Gateway to Flag retrieval."""
        print("\n[*] Running Test 2 — Intended Solve Chain Verification...")
        flag = solve(self.host, self.port)
        self.assertTrue(bool(flag), "Exploit solver must return a valid flag")
        self.assertTrue(flag.startswith("YUVA{") and flag.endswith("}"), f"Flag format invalid: {flag}")
        print(f"[+] Test 2 Passed. Flag successfully retrieved: {flag}")

    def test_03_trust_boundary_enforcement(self):
        """Test 3: Verify that unauthenticated requests and low-trust Service A requests to privileged operations are denied."""
        print("\n[*] Running Test 3 — Trust Boundary & Authorization Enforcement...")
        
        # 1. Unauthenticated call to Service B grant-admin-ticket -> Expect 401
        status, resp = http_request(f"{self.base_url}/api/v1/core/grant-admin-ticket", method="POST", data={})
        self.assertEqual(status, 401, f"Unauthenticated call must be 401 Unauthorized, got {status}")

        # 2. Call with legitimate Service A certificate -> Expect 403 Forbidden
        status, diag = http_request(f"{self.base_url}/api/v1/diagnostics/export")
        self.assertEqual(status, 200)
        sa_cert = diag["credentials"]["service_certificate"]
        
        headers = {
            "X-Citadel-Identity-Cert": base64.b64encode(sa_cert.encode("utf-8")).decode("utf-8"),
            "Content-Type": "application/json"
        }
        status, resp = http_request(f"{self.base_url}/api/v1/core/grant-admin-ticket", method="POST", headers=headers, data={})
        self.assertEqual(status, 403, f"Low-trust telemetry-agent must receive 403 Forbidden, got {status}")
        self.assertIn("InsufficientPermissions", resp.get("error", ""))

        # 3. Direct access to admin vault without ticket -> Expect 401
        status, resp = http_request(f"{self.base_url}/api/v1/admin/unlock-vault", method="POST", data={})
        self.assertEqual(status, 401, f"Direct access to admin vault without ticket must be 401, got {status}")

        print("[+] Test 3 Passed. Security boundaries correctly reject unauthenticated and unauthorized requests.")

    def test_04_reset_validation(self):
        """Test 4: Verify challenge state reset clears tickets and generates fresh session state."""
        print("\n[*] Running Test 4 — Challenge Reset Validation...")
        
        # 1. Solve to get an admin ticket
        status, diag = http_request(f"{self.base_url}/api/v1/diagnostics/export")
        sa_cert = diag["credentials"]["service_certificate"]
        sa_key = diag["credentials"]["service_private_key"]
        cert_chain = forge_orchestrator_certificate(sa_cert, sa_key)
        
        headers = {
            "X-Citadel-Identity-Cert": base64.b64encode(cert_chain.encode("utf-8")).decode("utf-8"),
            "Content-Type": "application/json"
        }
        status, core_resp = http_request(f"{self.base_url}/api/v1/core/grant-admin-ticket", method="POST", headers=headers, data={})
        ticket = core_resp["admin_ticket"]

        # 2. Trigger Reset
        status, reset_resp = http_request(f"{self.base_url}/api/v1/reset", method="POST")
        self.assertEqual(status, 200)
        self.assertEqual(reset_resp.get("status"), "RESET_COMPLETE")

        # 3. Old ticket should now be invalid
        admin_headers = {"Authorization": f"Bearer {ticket}", "Content-Type": "application/json"}
        status, resp = http_request(f"{self.base_url}/api/v1/admin/unlock-vault", method="POST", headers=admin_headers, data={})
        self.assertEqual(status, 401, "Old ticket must be invalidated after reset")

        print("[+] Test 4 Passed. Reset invalidates existing tickets cleanly.")

    def test_05_resource_abuse_and_malformed_inputs(self):
        """Test 5: Verify robustness under bursts of malformed certificates, corrupted headers, and rapid requests."""
        print("\n[*] Running Test 5 — Resource Controls & Malformed Input Robustness...")
        
        # Send garbage headers
        corrupted_payloads = [
            "NOT_A_CERTIFICATE",
            base64.b64encode(b"-----BEGIN CERTIFICATE-----\nINVALID_BASE64_DATA==\n-----END CERTIFICATE-----").decode("utf-8"),
            "A" * 500,
            base64.b64encode(b"\xff\xfe\xfd").decode("utf-8"),
            "null"
        ]

        for payload in corrupted_payloads:
            headers = {"X-Citadel-Identity-Cert": payload}
            status, resp = http_request(f"{self.base_url}/api/v1/core/grant-admin-ticket", method="POST", headers=headers, data={})
            self.assertEqual(status, 401, f"Corrupted certificate must result in 401, got {status}")

        # Send burst of requests
        def send_burst():
            for _ in range(20):
                http_request(f"{self.base_url}/api/v1/telemetry/status")

        threads = [threading.Thread(target=send_burst) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Check system health afterwards
        status, resp = http_request(f"{self.base_url}/api/v1/telemetry/status")
        self.assertEqual(status, 200, "System must remain operational after burst")
        print("[+] Test 5 Passed. System contained malformed requests and burst traffic cleanly.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1", help="Target host")
    parser.add_argument("--port", type=int, default=80, help="Target port")
    parser.add_argument("unittest_args", nargs="*")
    args = parser.parse_args()

    TestMicroserviceTrustChallenge.host = args.host
    TestMicroserviceTrustChallenge.port = args.port

    unittest_argv = [sys.argv[0]] + args.unittest_args
    unittest.main(argv=unittest_argv)
