#!/usr/bin/env python3
"""
Latverian Sovereign Microservice Mesh — Participant Client Helper Sample
Demonstrates how to interact with the Public Ingress Gateway and dispatch
authenticated identity assertion headers.
"""

import argparse
import json
import urllib.request
import urllib.error


def send_mesh_request(base_url, endpoint, method="GET", headers=None, data=None):
    if headers is None:
        headers = {}
    
    url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Citadel Mesh Sample Client")
    parser.add_argument("--host", default="127.0.0.1", help="Target Host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=80, help="Target Port (default: 80)")
    args = parser.parse_args()

    target = f"http://{args.host}:{args.port}"
    print(f"[*] Querying Mesh Topology at {target}...")
    status, res = send_mesh_request(target, "/api/v1/topology")
    print(f"[HTTP {status}] Topology Response:\n{json.dumps(res, indent=2)}")

    print(f"\n[*] Querying Edge Telemetry Status...")
    status, res = send_mesh_request(target, "/api/v1/telemetry/status")
    print(f"[HTTP {status}] Telemetry Status:\n{json.dumps(res, indent=2)}")
