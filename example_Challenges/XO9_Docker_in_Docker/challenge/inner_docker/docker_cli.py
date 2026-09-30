#!/usr/bin/env python3
"""
Lightweight Docker CLI wrapper for XO-9 (Honorport Heist - Docker in Docker)
Communicates with the Inner Docker Daemon (DOCKER_HOST or tcp://127.0.0.1:2375).
Ensures container scripts and runner jobs can interact with the inner daemon via standard 'docker' syntax.
"""

import os
import sys
import json
import urllib.request
import urllib.parse
import urllib.error
import time

DOCKER_HOST = os.environ.get("DOCKER_HOST", "tcp://127.0.0.1:2375")

def get_base_url():
    host = DOCKER_HOST
    if host.startswith("tcp://"):
        host = "http://" + host[6:]
    elif host.startswith("unix://"):
        host = "http://127.0.0.1:2375"
    if not host.startswith("http://"):
        host = "http://" + host
    return host

def query_daemon(path, method="GET", data=None, headers=None):
    url = f"{get_base_url()}{path}"
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
        with urllib.request.urlopen(req, timeout=10) as resp:
            content = resp.read()
            return resp.status, content.decode("utf-8", errors="ignore")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="ignore")
    except Exception as e:
        return 500, f"Cannot connect to the Docker daemon at {DOCKER_HOST}. Is the docker daemon running? Error: {e}"

def cmd_version():
    status, body = query_daemon("/version")
    if status == 200:
        v = json.loads(body)
        print(f"Client: Docker Engine - Community")
        print(f" Version:           {v.get('Version', '24.0.7')}")
        print(f" API version:       {v.get('ApiVersion', '1.41')}")
        print(f" Go version:        {v.get('GoVersion', 'go1.20.10')}")
        print(f" Git commit:        {v.get('GitCommit', '311b9d4')}")
        print(f" Built:             {v.get('BuildTime', '2026-09-26')}")
        print(f" OS/Arch:           {v.get('Os', 'linux')}/{v.get('Arch', 'amd64')}")
        print("")
        print(f"Server: Docker Engine - Community (Inner DinD)")
        print(f" Engine:")
        print(f"  Version:          {v.get('Version', '24.0.7')}")
        print(f"  API version:      {v.get('ApiVersion', '1.41')} (minimum version {v.get('MinAPIVersion', '1.12')})")
        print(f"  OS/Arch:          {v.get('Os', 'linux')}/{v.get('Arch', 'amd64')}")
        print(f"  Kernel Version:   {v.get('KernelVersion', '6.1.0-honorport-dind')}")
    else:
        print(body)

def cmd_info():
    status, body = query_daemon("/info")
    if status == 200:
        info = json.loads(body)
        print(f"Client:")
        print(f" Context:    default")
        print(f" Debug Mode: false")
        print(f"")
        print(f"Server:")
        print(f" Containers: {info.get('Containers', 2)}")
        print(f"  Running: {info.get('ContainersRunning', 1)}")
        print(f"  Paused: {info.get('ContainersPaused', 0)}")
        print(f"  Stopped: {info.get('ContainersStopped', 1)}")
        print(f" Images: {info.get('Images', 3)}")
        print(f" Server Version: {info.get('ServerVersion', '24.0.7')}")
        print(f" Storage Driver: {info.get('Driver', 'overlay2')}")
        print(f" Logging Driver: {info.get('LoggingDriver', 'json-file')}")
        print(f" Cgroup Driver: {info.get('CgroupDriver', 'cgroupfs')}")
        print(f" Kernel Version: {info.get('KernelVersion', '6.1.0-honorport-dind')}")
        print(f" Operating System: {info.get('OperatingSystem', 'Honorport Linux')}")
        print(f" OSType: {info.get('OSType', 'linux')}")
        print(f" Architecture: {info.get('Architecture', 'x86_64')}")
        print(f" CPUs: {info.get('NCPU', 4)}")
        print(f" Total Memory: {info.get('MemTotal', 4294967296) / (1024*1024*1024):.2f}GiB")
        print(f" Docker Root Dir: {info.get('DockerRootDir', '/var/lib/docker')}")
    else:
        print(body)

def cmd_images(args):
    status, body = query_daemon("/images/json")
    if status == 200:
        images = json.loads(body)
        print(f"{'REPOSITORY':<65} {'TAG':<15} {'IMAGE ID':<15} {'CREATED':<15} {'SIZE':<10}")
        for img in images:
            repotags = img.get("RepoTags", ["<none>:<none>"])
            for rt in repotags:
                if ":" in rt:
                    repo, tag = rt.rsplit(":", 1)
                else:
                    repo, tag = rt, "latest"
                img_id = img.get("Id", "")
                if img_id.startswith("sha256:"):
                    img_id = img_id[7:19]
                else:
                    img_id = img_id[:12]
                sz = f"{img.get('Size', 0) / (1024*1024):.1f}MB"
                print(f"{repo:<65} {tag:<15} {img_id:<15} {'2 hours ago':<15} {sz:<10}")
    else:
        print(body)

def cmd_inspect(args):
    if not args:
        print("Error: 'docker inspect' requires at least 1 argument.")
        sys.exit(1)
    target = args[0]
    encoded = urllib.parse.quote(target, safe="")
    status, body = query_daemon(f"/images/{encoded}/json")
    if status == 200:
        print(body)
    else:
        print(f"Error: No such object: {target}")

def cmd_history(args):
    if not args:
        print("Error: 'docker history' requires at least 1 argument.")
        sys.exit(1)
    target = args[0]
    encoded = urllib.parse.quote(target, safe="")
    status, body = query_daemon(f"/images/{encoded}/history")
    if status == 200:
        history = json.loads(body)
        print(f"{'IMAGE':<15} {'CREATED':<15} {'CREATED BY':<80} {'SIZE':<10}")
        for h in history:
            img_id = h.get("Id", "")
            if img_id.startswith("sha256:"):
                img_id = img_id[7:19]
            elif img_id == "<missing>":
                img_id = "<missing>"
            else:
                img_id = img_id[:12]
            created_by = h.get("CreatedBy", "")
            sz = f"{h.get('Size', 0) / 1024:.1f}KB"
            print(f"{img_id:<15} {'2 hours ago':<15} {created_by:<80} {sz:<10}")
    else:
        print(f"Error: No such image: {target}")

def cmd_build(args):
    tag = "latest"
    for i, a in enumerate(args):
        if a in ["-t", "--tag"] and i + 1 < len(args):
            tag = args[i + 1]
    
    print(f"Sending build context to Docker daemon...")
    status, body = query_daemon(f"/build?t={urllib.parse.quote(tag)}", method="POST", data=b"DOCKER_BUILD_CTX")
    for line in body.splitlines():
        if line.strip():
            try:
                obj = json.loads(line)
                if "stream" in obj:
                    sys.stdout.write(obj["stream"])
            except Exception:
                print(line)

def cmd_tag(args):
    if len(args) < 2:
        print("Error: 'docker tag' requires 2 arguments: SOURCE_IMAGE[:TAG] TARGET_IMAGE[:TAG]")
        sys.exit(1)
    src, target = args[0], args[1]
    if ":" in target:
        repo, tag = target.rsplit(":", 1)
    else:
        repo, tag = target, "latest"
    encoded = urllib.parse.quote(src, safe="")
    status, body = query_daemon(f"/images/{encoded}/tag?repo={urllib.parse.quote(repo)}&tag={urllib.parse.quote(tag)}", method="POST")
    if status not in [200, 201]:
        print(body)

def cmd_push(args):
    if not args:
        print("Error: 'docker push' requires 1 argument.")
        sys.exit(1)
    target = args[0]
    encoded = urllib.parse.quote(target, safe="")
    status, body = query_daemon(f"/images/{encoded}/push", method="POST")
    for line in body.splitlines():
        if line.strip():
            try:
                obj = json.loads(line)
                if "status" in obj:
                    print(obj["status"])
            except Exception:
                print(line)

def cmd_ps(args):
    status, body = query_daemon("/containers/json")
    if status == 200:
        containers = json.loads(body)
        print(f"{'CONTAINER ID':<15} {'IMAGE':<35} {'COMMAND':<20} {'CREATED':<15} {'STATUS':<20} {'NAMES':<20}")
        for c in containers:
            cid = c.get("Id", "")[:12]
            img = c.get("Image", "")[:32]
            cmd = c.get("Command", "")[:18]
            st = c.get("Status", "Up 2 hours")
            name = c.get("Names", [""])[0]
            print(f"{cid:<15} {img:<35} {cmd:<20} {'2 hours ago':<15} {st:<20} {name:<20}")
    else:
        print(body)

def main():
    if len(sys.argv) < 2:
        cmd_info()
        return

    cmd = sys.argv[1]
    args = sys.argv[2:]

    if cmd in ["version", "-v", "--version"]:
        cmd_version()
    elif cmd in ["info"]:
        cmd_info()
    elif cmd in ["images", "image"]:
        if args and args[0] == "ls":
            cmd_images(args[1:])
        elif args and args[0] == "inspect":
            cmd_inspect(args[1:])
        elif args and args[0] == "history":
            cmd_history(args[1:])
        else:
            cmd_images(args)
    elif cmd in ["inspect"]:
        cmd_inspect(args)
    elif cmd in ["history"]:
        cmd_history(args)
    elif cmd in ["build"]:
        cmd_build(args)
    elif cmd in ["tag"]:
        cmd_tag(args)
    elif cmd in ["push"]:
        cmd_push(args)
    elif cmd in ["ps"]:
        cmd_ps(args)
    elif cmd in ["run"]:
        print(f"[*] Running container in inner DinD environment...")
        print(f"[+] Container initialized successfully.")
    else:
        print(f"docker: '{cmd}' is not a docker command. See 'docker --help'")

if __name__ == "__main__":
    main()
