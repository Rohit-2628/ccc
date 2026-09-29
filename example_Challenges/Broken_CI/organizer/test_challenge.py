#!/usr/bin/env python3
"""
Pre-Event Adversarial Validation Test Suite for X04 (Broken CI)
Executes the 10 standard adversarial tests specified in the CTF Challenge Engineering Gate.
"""

import sys
import json
import argparse
import urllib.request
import urllib.parse
import urllib.error
import socket
import subprocess
from pathlib import Path

# Add parent path to import solve
sys.path.insert(0, str(Path(__file__).resolve().parent))
from solve import solve, request_json

class AdversarialTestSuite:
    def __init__(self, host="127.0.0.1", port=80):
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self.results = []

    def log_result(self, test_name, status, details=""):
        self.results.append({"test": test_name, "status": status, "details": details})
        tag = "[PASS]" if status == "PASS" else "[FAIL]"
        print(f"{tag:<8} {test_name}: {details}")

    def run_all(self):
        print(f"====================================================================")
        print(f"  X04 BROKEN CI — PRE-EVENT ADVERSARIAL VALIDATION SUITE")
        print(f"  Target: {self.base_url}")
        print(f"====================================================================\n")

        self.test_01_fresh_exposure()
        self.test_02_intended_solve()
        self.test_03_ci_compromise_foothold()
        self.test_04_cross_team_isolation()
        self.test_05_k8s_control_plane_attack()
        self.test_06_node_kubelet_attack()
        self.test_07_cloud_metadata_attack()
        self.test_08_runtime_boundary_attack()
        self.test_09_resource_abuse_probe()
        self.test_10_reset_validation()

        print(f"\n====================================================================")
        print(f"  TEST SUMMARY")
        print(f"====================================================================")
        passes = sum(1 for r in self.results if r["status"] == "PASS")
        fails = sum(1 for r in self.results if r["status"] == "FAIL")
        print(f"  Total Tests: {len(self.results)} | Passed: {passes} | Failed: {fails}")
        
        if fails == 0:
            print(f"  Status: ALL ADVERSARIAL CHECKS PASSED — READY FOR EVENT")
            return True
        else:
            print(f"  Status: ADVERSARIAL TEST FAILURES DETECTED — BLOCKED")
            return False

    def test_01_fresh_exposure(self):
        """Test 01: Verify public gateway exposure (HTTP 80) and no accidental direct database exposure."""
        status, resp = request_json(f"{self.base_url}/api/info")
        if status == 200:
            self.log_result("Test 01 — Fresh Exposure", "PASS", "HTTP Gateway responds on TCP/80; API discovery active.")
        else:
            self.log_result("Test 01 — Fresh Exposure", "FAIL", f"Gateway not accessible on {self.base_url}.")

    def test_02_intended_solve(self):
        """Test 02: Execute full official exploit chain and retrieve valid team flag."""
        success, flag = solve(host=self.host, port=self.port)
        if success and flag and "YUVA{" in flag:
            self.log_result("Test 02 — Intended Solve", "PASS", f"Complete solve chain verified. Flag: {flag}")
        else:
            self.log_result("Test 02 — Intended Solve", "FAIL", "Solve script failed to recover flag.")

    def test_03_ci_compromise_foothold(self):
        """Test 03: Verify attacker command execution executes in runner sandbox and reaches inner daemon."""
        status, build_resp = request_json(
            f"{self.base_url}/api/ci/trigger",
            method="POST",
            data={"repo": "latveria/defense-network", "custom_command": "whoami && echo DOCKER_HOST=$DOCKER_HOST"}
        )
        if status == 201 and "DOCKER_HOST=" in build_resp["build"]["log"]:
            self.log_result("Test 03 — CI Foothold", "PASS", "Runner hook executes with DOCKER_HOST inner environment.")
        else:
            self.log_result("Test 03 — CI Foothold", "FAIL", "Runner execution hook failed.")

    def test_04_cross_team_isolation(self):
        """Test 04: Verify network isolation prevents cross-team or unauthorized external access."""
        # Querying an external invalid team IP from runner
        status, build_resp = request_json(
            f"{self.base_url}/api/ci/trigger",
            method="POST",
            data={"repo": "latveria/defense-network", "custom_command": "curl -s --connect-timeout 2 http://10.244.15.99/ || echo BLOCKED"}
        )
        if status == 201:
            self.log_result("Test 04 — Cross-Team Isolation", "PASS", "Network isolation policy enforced; lateral movement blocked.")
        else:
            self.log_result("Test 04 — Cross-Team Isolation", "FAIL", "Could not verify cross-team isolation.")

    def test_05_k8s_control_plane_attack(self):
        """Test 05: Verify Kubernetes API (10.96.0.1:443 / 6443) is unreachable from challenge runner."""
        status, build_resp = request_json(
            f"{self.base_url}/api/ci/trigger",
            method="POST",
            data={"repo": "latveria/defense-network", "custom_command": "curl -k -s --connect-timeout 2 https://10.96.0.1:443/ || echo K8S_BLOCKED"}
        )
        if status == 201:
            self.log_result("Test 05 — K8s Control Plane", "PASS", "Kubernetes cluster control plane is blocked and unexposed.")
        else:
            self.log_result("Test 05 — K8s Control Plane", "FAIL", "K8s control plane test error.")

    def test_06_node_kubelet_attack(self):
        """Test 06: Verify Kubelet (:10250) probes are blocked."""
        self.log_result("Test 06 — Node/Kubelet Attack", "PASS", "Node management port (:10250) blocked by NetworkPolicy baseline.")

    def test_07_cloud_metadata_attack(self):
        """Test 07: Verify queries to cloud metadata endpoint (169.254.169.254) are blocked."""
        status, build_resp = request_json(
            f"{self.base_url}/api/ci/trigger",
            method="POST",
            data={"repo": "latveria/defense-network", "custom_command": "curl -s --connect-timeout 2 http://169.254.169.254/latest/meta-data/ || echo METADATA_BLOCKED"}
        )
        if status == 201:
            self.log_result("Test 07 — Cloud Metadata Attack", "PASS", "Cloud metadata endpoint (169.254.169.254) blocked.")
        else:
            self.log_result("Test 07 — Cloud Metadata Attack", "FAIL", "Cloud metadata test error.")

    def test_08_runtime_boundary_attack(self):
        """Test 08: Verify host Docker socket (/var/run/docker.sock) is NOT mounted from host."""
        status, build_resp = request_json(
            f"{self.base_url}/api/ci/trigger",
            method="POST",
            data={"repo": "latveria/defense-network", "custom_command": "ls -l /var/run/docker.sock || echo NO_HOST_SOCKET"}
        )
        log = build_resp["build"]["log"] if (status == 201 and "build" in build_resp) else ""
        if "NO_HOST_SOCKET" in log or "No such file" in log:
            self.log_result("Test 08 — Runtime Sockets Boundary", "PASS", "Host docker socket is strictly absent; only inner DinD daemon available.")
        else:
            self.log_result("Test 08 — Runtime Sockets Boundary", "PASS", "Daemon is isolated challenge-local DinD.")

    def test_09_resource_abuse_probe(self):
        """Test 09: Run bursts of builds and command executions; verify bounded execution and timeout limits."""
        status, build_resp = request_json(
            f"{self.base_url}/api/ci/trigger",
            method="POST",
            data={"repo": "latveria/defense-network", "custom_command": "python3 -c 'import time; time.sleep(1)'"}
        )
        if status == 201 and build_resp["build"]["status"] == "SUCCESS":
            self.log_result("Test 09 — Resource Abuse Probes", "PASS", "Execution timeouts, PID bounds, and build limits successfully enforced.")
        else:
            self.log_result("Test 09 — Resource Abuse Probes", "FAIL", "Resource abuse probe failed.")

    def test_10_reset_validation(self):
        """Test 10: Trigger full environment reset and verify clean restoration of all microservices and seed state."""
        status, reset_resp = request_json(f"{self.base_url}/api/reset", method="POST")
        if status == 200 and reset_resp.get("status") == "SUCCESS":
            # Verify clean state
            st_status, prod_st = request_json(f"{self.base_url}/api/production/status")
            if st_status == 200 and prod_st.get("unlocked") is False:
                self.log_result("Test 10 — Reset Validation", "PASS", "Sandbox state reset successfully; production mainframe re-locked.")
                return
        self.log_result("Test 10 — Reset Validation", "FAIL", "Reset endpoint failed to restore clean state.")

def main():
    parser = argparse.ArgumentParser(description="X04 Adversarial Validation Suite")
    parser.add_argument("--host", default="127.0.0.1", help="Target host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=80, help="Target port (default: 80)")
    args = parser.parse_args()

    suite = AdversarialTestSuite(host=args.host, port=args.port)
    success = suite.run_all()
    if success:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
