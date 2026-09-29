#!/usr/bin/env python3
"""
Latveria Citadel Zero-Trust Enclave (X10) — Comprehensive Test Suite
Executes the 5 Masterbook Validation Tests:
- Test 1: Fresh Start / Exposure
- Test 2: Intended Solve
- Test 3: Boundary & Security Enforcement
- Test 4: Reset Lifecycle
- Test 5: Resource & Malformed Input Stability
"""

import argparse
import base64
import hashlib
import hmac
import json
import sys
import time
import requests

from solve import solve


def run_tests(target_url: str):
    base = target_url.rstrip("/")
    print(f"============================================================")
    print(f"   RUNNING MASTERBOOK VALIDATION SUITE FOR X10: ZERO TRUST FAILURE")
    print(f"   Target: {base}")
    print(f"============================================================\n")

    # Test 1: Fresh Start & Interface Exposure
    print("[*] TEST 1: Fresh Start & Interface Exposure Check...")
    r = requests.get(f"{base}/", timeout=5)
    assert r.status_code == 200, f"Expected 200 for index, got {r.status_code}"
    assert "Zero-Trust" in r.text, "Index HTML missing expected branding"

    # Verify that direct external requests to internal core and admin are blocked by Gateway
    r_core = requests.get(f"{base}/api/v1/core/status", timeout=5)
    assert r_core.status_code == 403, f"Expected 403 for direct external core access, got {r_core.status_code}"
    
    r_admin = requests.get(f"{base}/api/v1/admin/status", timeout=5)
    assert r_admin.status_code == 403, f"Expected 403 for direct external admin access, got {r_admin.status_code}"
    print("[+] Test 1 PASSED: Only documented public gateway interfaces are accessible.")

    # Test 2: Intended Solve Path
    print("\n[*] TEST 2: Intended Solve Path Verification...")
    flag = solve(base)
    assert flag.startswith("YUVA{"), f"Invalid flag format: {flag}"
    print(f"[+] Test 2 PASSED: Intended solve path successfully recovered flag: {flag}")

    # Test 3: Boundary & Security Enforcement
    print("\n[*] TEST 3: Boundary & Security Enforcement Verification...")
    
    # 3a. Extract active config
    res = requests.post(f"{base}/api/v1/diagnostics/exec", json={
        "script": "import json\nprint(json.dumps(get_mesh_config()))"
    }, timeout=5)
    config = json.loads(res.json()["stdout"].strip())
    mesh_key = config["mesh_signing_key"].encode("utf-8")

    # 3b. Verify that Low-Trust Identity (edge-worker) cannot obtain Admin Ticket
    low_trust_claims = {
        "service_id": "edge-worker",
        "role": "edge-relay",
        "tier": "low",
        "capabilities": ["telemetry:read"],
        "trust_domain": "latveria.citadel.mesh",
        "iat": int(time.time()),
        "exp": int(time.time()) + 3600,
        "nonce": "test_nonce_low"
    }
    low_b64 = base64.urlsafe_b64encode(json.dumps(low_trust_claims).encode()).decode().rstrip("=")
    low_sig = hmac.new(mesh_key, low_b64.encode(), hashlib.sha256).hexdigest()
    low_token = f"{low_b64}.{low_sig}"

    res = requests.post(f"{base}/api/v1/relay/dispatch", json={
        "target_url": "http://127.0.0.1:8082/api/v1/core/request-admin-ticket",
        "assertion_token": low_token,
        "method": "POST"
    }, timeout=5)
    assert res.status_code == 403, f"Expected 403 for low-trust identity, got {res.status_code}"
    print("    [+] 3a. Low-trust identity properly rejected with 403 Forbidden.")

    # 3c. Verify that an invalid HMAC signature is rejected with 401
    bad_token = f"{low_b64}.0000000000000000000000000000000000000000000000000000000000000000"
    res = requests.post(f"{base}/api/v1/relay/dispatch", json={
        "target_url": "http://127.0.0.1:8082/api/v1/core/request-admin-ticket",
        "assertion_token": bad_token,
        "method": "POST"
    }, timeout=5)
    assert res.status_code == 401, f"Expected 401 for invalid signature, got {res.status_code}"
    print("    [+] 3b. Invalid assertion signature properly rejected with 401 Unauthorized.")

    # 3d. Verify that external/non-loopback destination addresses are blocked
    res = requests.post(f"{base}/api/v1/relay/dispatch", json={
        "target_url": "http://169.254.169.254/latest/meta-data/",
        "assertion_token": low_token,
        "method": "GET"
    }, timeout=5)
    assert res.status_code == 403, f"Expected 403 for external IP relay attempt, got {res.status_code}"
    print("    [+] 3c. Cloud metadata / external routing attempt properly blocked with 403.")
    print("[+] Test 3 PASSED: All boundary enforcement checks verified.")

    # Test 4: Reset Lifecycle
    print("\n[*] TEST 4: Challenge Reset Lifecycle Verification...")
    r = requests.post(f"{base}/api/v1/reset", timeout=5)
    assert r.status_code == 200, f"Expected 200 for reset, got {r.status_code}"
    assert r.json().get("status") == "RESET_COMPLETE", "Reset status mismatch"

    # After reset, old tokens must fail
    res = requests.post(f"{base}/api/v1/relay/dispatch", json={
        "target_url": "http://127.0.0.1:8082/api/v1/core/request-admin-ticket",
        "assertion_token": low_token,
        "method": "POST"
    }, timeout=5)
    assert res.status_code in [401, 403], f"Old token should fail after reset, got {res.status_code}"

    # Verify that a fresh solve succeeds immediately after reset
    flag_after_reset = solve(base)
    assert flag_after_reset == flag, "Flag mismatch after reset"
    print("[+] Test 4 PASSED: Reset successfully cleared state and re-established clean solve path.")

    # Test 5: Resource & Stability Abuse Probes
    print("\n[*] TEST 5: Resource Abuse & Malformed Input Stability...")
    for i in range(20):
        # Fire rapid malformed requests
        requests.post(f"{base}/api/v1/diagnostics/exec", json={"script": "1/0"}, timeout=2)
        requests.post(f"{base}/api/v1/relay/dispatch", json={"target_url": "http://127.0.0.1:8082/api/v1/core/invalid"}, timeout=2)
    
    # Confirm health
    r_health = requests.get(f"{base}/healthz", timeout=5)
    assert r_health.status_code == 200, "Gateway failed healthcheck after stress probe"
    print("[+] Test 5 PASSED: Service remained responsive and healthy under stress.")

    print("\n============================================================")
    print("   ALL 5 MASTERBOOK TESTS PASSED SUCCESSFULLY!")
    print("============================================================\n")


def main():
    parser = argparse.ArgumentParser(description="X10 Challenge Test Suite")
    parser.add_argument("--target", default=None, help="Target Gateway URL")
    parser.add_argument("--host", default="127.0.0.1", help="Target host")
    parser.add_argument("--port", type=int, default=8080, help="Target port")
    args = parser.parse_args()

    target = args.target if args.target else f"http://{args.host}:{args.port}"
    try:
        run_tests(target)
        sys.exit(0)
    except Exception as e:
        print(f"\n[-] TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
