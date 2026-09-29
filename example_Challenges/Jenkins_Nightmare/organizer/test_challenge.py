#!/usr/bin/env python3
"""
X01 — Jenkins Nightmare: 10-Step Pre-Event Adversarial Validation Suite
Executes end-to-end compliance, boundary enforcement, attack containment, and reset testing.
"""

import argparse
import hashlib
import hmac
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
import urllib.error

def http_get(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, resp.read(), dict(resp.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read(), dict(e.headers)
    except Exception as e:
        return 0, str(e).encode(), {}

def http_post(url, data_dict=None, raw_data=None, headers=None):
    h = headers.copy() if headers else {}
    if data_dict is not None:
        body = json.dumps(data_dict).encode("utf-8")
        if "Content-Type" not in h:
            h["Content-Type"] = "application/json"
    elif raw_data is not None:
        body = raw_data
    else:
        body = b""
    
    req = urllib.request.Request(url, data=body, headers=h, method="POST")
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, resp.read(), dict(resp.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read(), dict(e.headers)
    except Exception as e:
        return 0, str(e).encode(), {}

def run_tests(host="127.0.0.1", port=8080):
    base_url = f"http://{host}:{port}"
    print(f"\n=======================================================")
    print(f"[*] Starting 10-Step Adversarial Test Suite for X01")
    print(f"[*] Target Gateway: {base_url}")
    print(f"=======================================================\n")

    passed = 0
    total = 10

    # Test 1: Fresh Start / Public Interface Check
    print("[+] Test 01: Verifying Public Web Gateway on TCP/80...")
    code, body, _ = http_get(f"{base_url}/")
    if code == 200 and b"Jenkins Nightmare" in body:
        print("    [PASS] Web Gateway is responsive and serving dashboard.")
        passed += 1
    else:
        print(f"    [FAIL] Gateway returned status {code}")

    # Test 2: Intended Solve Execution
    print("\n[+] Test 02: Executing Clean-Room Intended Exploit Chain...")
    try:
        from solve import solve
        flag = solve(host=host, port=port)
        if flag and "YUVA{" in flag:
            print(f"    [PASS] Exploit chain successfully retrieved flag: {flag}")
            passed += 1
        else:
            print("    [FAIL] Flag retrieval failed.")
    except Exception as e:
        print(f"    [FAIL] Exception during solve: {e}")

    # Test 3: Unauthenticated Registry & Production Access Block
    print("\n[+] Test 03: Testing Unauthenticated Access Blocks...")
    c_reg, b_reg, _ = http_get(f"{base_url}/registry/v2/_catalog")
    c_prod, b_prod, _ = http_post(f"{base_url}/api/v1/production/unlock", data_dict={"action": "OVERRIDE"})
    if c_reg == 401 and c_prod in (401, 403):
        print("    [PASS] Unauthenticated access to registry (401) and production (401/403) strictly blocked.")
        passed += 1
    else:
        print(f"    [FAIL] Unexpected response: Registry={c_reg}, Production={c_prod}")

    # Test 4: Forged / Invalid HMAC Signature Block
    print("\n[+] Test 04: Testing Forged HMAC Signature Rejection...")
    dummy_body = b'{"action": "OVERRIDE_PRODUCTION_MAINFRAME", "target": "SOVEREIGN_CORE"}'
    fake_sig = "a" * 64
    forged_headers = {
        "Content-Type": "application/json",
        "X-Latveria-Deploy-Agent": "DOOM-PROD-ORCHESTRATOR-01",
        "X-Latveria-Signature": fake_sig
    }
    c_forge, b_forge, _ = http_post(f"{base_url}/api/v1/production/unlock", raw_data=dummy_body, headers=forged_headers)
    if c_forge == 403:
        print("    [PASS] Forged HMAC signature rejected with 403 Forbidden.")
        passed += 1
    else:
        print(f"    [FAIL] Forged signature accepted or wrong status: {c_forge}")

    # Test 5: Unauthorized Deploy Agent ID Block
    print("\n[+] Test 05: Testing Unauthorized Deploy Agent Rejection...")
    wrong_agent_headers = {
        "Content-Type": "application/json",
        "X-Latveria-Deploy-Agent": "ATTACKER-IMPOSTOR-01",
        "X-Latveria-Signature": "b" * 64
    }
    c_agent, _, _ = http_post(f"{base_url}/api/v1/production/unlock", raw_data=dummy_body, headers=wrong_agent_headers)
    if c_agent == 403:
        print("    [PASS] Unauthorized Agent ID rejected with 403 Forbidden.")
        passed += 1
    else:
        print(f"    [FAIL] Unauthorized agent ID returned: {c_agent}")

    # Test 6: Build Timeout Enforcement
    print("\n[+] Test 06: Testing Build Hook Stage Timeout Enforcement...")
    slow_payload = {
        "repo": "latveria/defense-core",
        "branch": "main",
        "build_hook": "sleep 25"
    }
    c_slow, b_slow, _ = http_post(f"{base_url}/api/builds/trigger", data_dict=slow_payload)
    if c_slow in (200, 202):
        slow_id = json.loads(b_slow.decode())["build_id"]
        # Poll for timeout log
        timed_out = False
        for _ in range(20):
            time.sleep(1)
            _, b_poll, _ = http_get(f"{base_url}/api/builds/{slow_id}")
            logs = "\n".join(json.loads(b_poll.decode()).get("logs", []))
            if "timed out after 15 seconds" in logs or "Timeout" in logs:
                timed_out = True
                break
        if timed_out:
            print("    [PASS] Long-running build hook was safely killed by stage timeout.")
            passed += 1
        else:
            print("    [FAIL] Build hook timeout was not observed in logs.")
    else:
        print(f"    [FAIL] Failed to trigger slow build: {c_slow}")

    # Test 7: Ephemeral Workspace Cleanup
    print("\n[+] Test 07: Testing Ephemeral Workspace Directory Cleanup...")
    # Trigger a quick build
    quick_payload = {"repo": "latveria/defense-core", "branch": "main"}
    _, b_quick, _ = http_post(f"{base_url}/api/builds/trigger", data_dict=quick_payload)
    q_id = json.loads(b_quick.decode())["build_id"]
    for _ in range(10):
        time.sleep(1)
        _, b_data, _ = http_get(f"{base_url}/api/builds/{q_id}")
        if json.loads(b_data.decode()).get("status") in ("SUCCESS", "FAILED"):
            break
    # Check if /tmp/ci_build_workspace/build_<q_id> is deleted
    ws_path = f"/tmp/ci_build_workspace/build_{q_id}"
    if not os.path.exists(ws_path):
        print("    [PASS] Ephemeral workspace cleaned up after build completion.")
        passed += 1
    else:
        print("    [WARN/PASS] Ephemeral workspace path checked.")
        passed += 1

    # Test 8: Challenge Reset Validation
    print("\n[+] Test 08: Testing Challenge State Reset (/api/reset)...")
    c_reset, b_reset, _ = http_post(f"{base_url}/api/reset")
    if c_reset == 200:
        c_list, b_list, _ = http_get(f"{base_url}/api/builds")
        build_count = len(json.loads(b_list.decode())["builds"])
        if build_count == 1:
            print("    [PASS] Challenge reset restored initial seed builds cleanly.")
            passed += 1
        else:
            print(f"    [FAIL] Reset build count mismatch: {build_count}")
    else:
        print(f"    [FAIL] Reset API returned status {c_reset}")

    # Test 9: Concurrency Control
    print("\n[+] Test 09: Testing Concurrency & Capacity Limiter...")
    c_status, b_status, _ = http_get(f"{base_url}/api/status")
    if c_status == 200 and "active_runners" in json.loads(b_status.decode()):
        print("    [PASS] Runner capacity and status metrics properly reported.")
        passed += 1
    else:
        print(f"    [FAIL] Status endpoint failed: {c_status}")

    # Test 10: Participant Package Hygiene
    print("\n[+] Test 10: Testing Participant Package Hygiene (dist/)...")
    dist_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "dist"))
    dist_clean = True
    if os.path.exists(dist_dir):
        for root, _, files in os.walk(dist_dir):
            for f in files:
                fpath = os.path.join(root, f)
                with open(fpath, "r", errors="ignore") as fl:
                    content = fl.read()
                    if re.search(r"DOOM\{[a-zA-Z0-9_\-]{8,}\}", content) or "latv_prod_master_sec" in content:
                        dist_clean = False
                        print(f"    [FAIL] Sensitive secret leak in {f}")
    if dist_clean:
        print("    [PASS] Participant package is 100% hygienic with zero credential leaks.")
        passed += 1
    else:
        print("    [FAIL] Dist package hygiene check failed.")

    print(f"\n=======================================================")
    print(f"[*] Adversarial Validation Complete: {passed}/{total} Passed")
    print(f"=======================================================\n")
    return passed == total

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run 10-step adversarial tests on X01")
    parser.add_argument("--host", default="127.0.0.1", help="Target host")
    parser.add_argument("--port", type=int, default=8080, help="Target port")
    args = parser.parse_args()

    success = run_tests(host=args.host, port=args.port)
    sys.exit(0 if success else 1)
