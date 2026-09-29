#!/usr/bin/env python3
"""
Latveria Citadel Zero-Trust Mesh — Participant Client Helper Sample
Demonstrates communicating with the public gateway.
"""

import argparse
import json
import urllib.request
import urllib.error


def main():
    parser = argparse.ArgumentParser(description="Citadel Mesh Gateway Client")
    parser.add_argument("--target", default="http://127.0.0.1:8080", help="Target Gateway URL (default: http://127.0.0.1:8080)")
    args = parser.parse_args()

    base_url = args.target.rstrip("/")
    print(f"[*] Connecting to Citadel Mesh Gateway at {base_url}...")

    # 1. Query Topology
    try:
        with urllib.request.urlopen(f"{base_url}/api/v1/topology", timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print("[+] Mesh Topology:")
            print(json.dumps(data, indent=2))
    except Exception as e:
        print(f"[-] Failed to fetch topology: {e}")

    # 2. Query Telemetry
    try:
        with urllib.request.urlopen(f"{base_url}/api/v1/telemetry/status", timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print("\n[+] Edge Telemetry Status:")
            print(json.dumps(data, indent=2))
    except Exception as e:
        print(f"[-] Failed to fetch telemetry: {e}")


if __name__ == "__main__":
    main()
