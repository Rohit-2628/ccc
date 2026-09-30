#!/usr/bin/env python3
"""
Inner Docker Daemon API Server for XO-9 (Honorport Heist - Docker in Docker)
Emulates the challenge-local Docker Engine REST API on 127.0.0.1:2375 and /tmp/dind/docker.sock.
Provides realistic responses for docker info, images, inspect, history, build, tag, push, ps, exec, and run.
"""

import os
import json
import time
import socket
import threading
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

STORAGE_ROOT = Path("/tmp/xo9_storage")
DIND_DIR = STORAGE_ROOT / "dind_storage"
IMAGES_FILE = DIND_DIR / "images.json"

def get_images():
    if IMAGES_FILE.exists():
        try:
            return json.loads(IMAGES_FILE.read_text())
        except Exception:
            pass
    return {}

def save_images(images):
    IMAGES_FILE.write_text(json.dumps(images, indent=2))

class DockerDaemonHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def _send_json(self, data, status=200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Server", "Docker/24.0.7 (linux-dind)")
        self.end_headers()
        self.wfile.write(body)

    def _send_text(self, text, status=200):
        body = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Server", "Docker/24.0.7 (linux-dind)")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        
        norm_path = path
        if norm_path.startswith("/v1."):
            parts = norm_path.split("/", 2)
            if len(parts) > 2:
                norm_path = "/" + parts[2]
            else:
                norm_path = "/"

        if norm_path in ["/_ping", "/ping"]:
            return self._send_text("OK\n")

        if norm_path in ["/version", "/v1.41/version"]:
            return self._send_json({
                "Platform": {"Name": "Docker Engine - Community (Inner DinD)"},
                "Components": [
                    {"Name": "Engine", "Version": "24.0.7", "Details": {"ApiVersion": "1.41", "Arch": "amd64", "Os": "linux"}},
                    {"Name": "containerd", "Version": "v1.7.11"},
                    {"Name": "runc", "Version": "1.1.10"}
                ],
                "Version": "24.0.7",
                "ApiVersion": "1.41",
                "MinAPIVersion": "1.12",
                "GitCommit": "311b9d4",
                "GoVersion": "go1.20.10",
                "Os": "linux",
                "Arch": "amd64",
                "KernelVersion": "6.1.0-honorport-dind",
                "BuildTime": "2026-09-26T10:00:00.000000000+00:00"
            })

        if norm_path == "/info":
            images = get_images()
            return self._send_json({
                "ID": "HONORPORT:DIND:9019:8821:0049",
                "Containers": 2,
                "ContainersRunning": 1,
                "ContainersPaused": 0,
                "ContainersStopped": 1,
                "Images": len(images),
                "Driver": "overlay2",
                "DriverStatus": [["Backing Filesystem", "extfs"], ["Supports d_type", "true"]],
                "Plugins": {"Volume": ["local"], "Network": ["bridge", "host", "none"], "Log": ["json-file"]},
                "MemoryLimit": True,
                "SwapLimit": True,
                "KernelMemory": True,
                "CPUCfsPeriod": True,
                "CPUCfsQuota": True,
                "CPUShares": True,
                "IPv4Forwarding": True,
                "BridgeNfIptables": True,
                "BridgeNfIp6tables": True,
                "Debug": False,
                "NFd": 24,
                "OomKillDisable": True,
                "NGoroutines": 38,
                "SystemTime": time.strftime("%Y-%m-%dT%H:%M:%S.000000000Z"),
                "LoggingDriver": "json-file",
                "CgroupDriver": "cgroupfs",
                "NEventsListener": 0,
                "KernelVersion": "6.1.0-honorport-dind",
                "OperatingSystem": "Honorport Linux v24.04 (Inner DinD Container)",
                "OSType": "linux",
                "Architecture": "x86_64",
                "IndexServerAddress": "https://index.docker.io/v1/",
                "RegistryConfig": {
                    "InsecureRegistryCIDRs": ["127.0.0.0/8", "honorport-registry.local:5000"],
                    "IndexConfigs": {
                        "honorport-registry.local:5000": {"Name": "honorport-registry.local:5000", "Mirrors": [], "Secure": False, "Official": False}
                    }
                },
                "NCPU": 4,
                "MemTotal": 4294967296,
                "DockerRootDir": "/var/lib/docker",
                "ServerVersion": "24.0.7"
            })

        if norm_path == "/images/json":
            images = get_images()
            out = []
            for tag_name, img_data in images.items():
                out.append({
                    "Id": img_data.get("Id", "sha256:unknown"),
                    "ParentId": "",
                    "RepoTags": img_data.get("RepoTags", [tag_name]),
                    "RepoDigests": [f"{tag_name.split(':')[0]}@{img_data.get('ManifestDigest', img_data.get('Id'))}"],
                    "Created": img_data.get("Created", int(time.time())),
                    "Size": img_data.get("Size", 1024000),
                    "SharedSize": -1,
                    "VirtualSize": img_data.get("Size", 1024000),
                    "Labels": img_data.get("Config", {}).get("Labels", {})
                })
            return self._send_json(out)

        # Inspect image /images/{name}/json
        if norm_path.startswith("/images/") and norm_path.endswith("/json"):
            image_query = norm_path[len("/images/"):-len("/json")]
            image_query = urllib.parse.unquote(image_query)
            images = get_images()
            
            matched = None
            for key, val in images.items():
                if image_query == key or image_query in val.get("RepoTags", []) or (image_query.startswith("sha256:") and val.get("Id") == image_query) or val.get("Id", "").startswith(image_query):
                    matched = val
                    break
            
            if matched:
                return self._send_json({
                    "Id": matched.get("Id"),
                    "RepoTags": matched.get("RepoTags"),
                    "RepoDigests": [f"{matched.get('RepoTags', ['unknown'])[0]}@{matched.get('Id')}"],
                    "Parent": "",
                    "Comment": "Honorport Cargo Build",
                    "Created": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(matched.get("Created", time.time()))),
                    "Container": "c9019204819a",
                    "DockerVersion": "24.0.7",
                    "Author": "Honorport Defense Systems",
                    "Config": matched.get("Config", {}),
                    "Architecture": "amd64",
                    "Os": "linux",
                    "Size": matched.get("Size", 2048000),
                    "VirtualSize": matched.get("Size", 2048000),
                    "GraphDriver": {
                        "Data": {
                            "LowerDir": "/var/lib/docker/overlay2/layer1/diff",
                            "MergedDir": "/var/lib/docker/overlay2/merged",
                            "UpperDir": "/var/lib/docker/overlay2/upper/diff",
                            "WorkDir": "/var/lib/docker/overlay2/work"
                        },
                        "Name": "overlay2"
                    },
                    "RootFS": {
                        "Type": "layers",
                        "Layers": matched.get("Layers", [matched.get("Id")])
                    }
                })
            return self._send_json({"message": f"No such image: {image_query}"}, status=404)

        # Image history: /images/{name}/history
        if norm_path.startswith("/images/") and norm_path.endswith("/history"):
            image_query = norm_path[len("/images/"):-len("/history")]
            image_query = urllib.parse.unquote(image_query)
            images = get_images()
            matched = None
            for key, val in images.items():
                if image_query == key or image_query in val.get("RepoTags", []) or (image_query.startswith("sha256:") and val.get("Id") == image_query) or val.get("Id", "").startswith(image_query):
                    matched = val
                    break
            
            if matched:
                history_list = matched.get("History", [])
                out_history = []
                for h in history_list:
                    out_history.append({
                        "Id": matched.get("Id") if not h.get("empty_layer") else "<missing>",
                        "Created": matched.get("Created", int(time.time())),
                        "CreatedBy": h.get("created_by", "/bin/sh"),
                        "Tags": matched.get("RepoTags", []) if not h.get("empty_layer") else None,
                        "Size": 102400 if not h.get("empty_layer") else 0,
                        "Comment": ""
                    })
                return self._send_json(out_history)
            return self._send_json({"message": f"No such image: {image_query}"}, status=404)

        if norm_path == "/containers/json":
            return self._send_json([
                {
                    "Id": "c9019204819a3b8d9e",
                    "Names": ["/honorport-deployment-worker-01"],
                    "Image": "honorport/deployment-worker:latest",
                    "ImageID": "sha256:e991b2c4e5f60718293a4b5c6d7e8f90123456789abcdef0123456789abcdef0",
                    "Command": "/bin/sh",
                    "Created": 1727337600,
                    "State": "running",
                    "Status": "Up 2 hours"
                }
            ])

        return self._send_json({"message": "page not found"}, status=404)

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        
        norm_path = path
        if norm_path.startswith("/v1."):
            parts = norm_path.split("/", 2)
            if len(parts) > 2:
                norm_path = "/" + parts[2]
            else:
                norm_path = "/"

        # Build endpoint
        if norm_path == "/build":
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length > 0:
                self.rfile.read(content_length)
            
            build_id = "sha256:e1b2c3d4e5f67890123456789abcdef0123456789abcdef0123456789abcdef0"
            query = urllib.parse.parse_qs(parsed.query)
            tag = query.get("t", ["defense/vault-gatekeeper:v3.2.1"])[0]

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Transfer-Encoding", "chunked")
            self.end_headers()

            logs = [
                {"stream": "Step 1/3 : FROM honorport-registry.local:5000/system/base-os:v1.0.0\n"},
                {"stream": " ---> sha256:base00112233\n"},
                {"stream": "Step 2/3 : COPY app/ /app/\n"},
                {"stream": " ---> Using cache\n"},
                {"stream": "Step 3/3 : CMD python3 app/cargo_validator.py\n"},
                {"stream": f"Successfully built {build_id[:12]}\n"},
                {"stream": f"Successfully tagged {tag}\n"},
                {"aux": {"ID": build_id}}
            ]
            for log_item in logs:
                chunk = json.dumps(log_item) + "\n"
                chunk_bytes = chunk.encode("utf-8")
                self.wfile.write(f"{len(chunk_bytes):X}\r\n".encode("utf-8"))
                self.wfile.write(chunk_bytes)
                self.wfile.write(b"\r\n")
            self.wfile.write(b"0\r\n\r\n")
            return

        # Tag image
        if norm_path.startswith("/images/") and norm_path.endswith("/tag"):
            image_query = norm_path[len("/images/"):-len("/tag")]
            image_query = urllib.parse.unquote(image_query)
            query = urllib.parse.parse_qs(parsed.query)
            repo = query.get("repo", [""])[0]
            tag = query.get("tag", ["latest"])[0]
            new_tag = f"{repo}:{tag}" if repo else tag

            images = get_images()
            for key, val in images.items():
                if image_query == key or image_query in val.get("RepoTags", []) or (image_query.startswith("sha256:") and val.get("Id") == image_query) or val.get("Id", "").startswith(image_query):
                    if "RepoTags" not in val:
                        val["RepoTags"] = []
                    if new_tag not in val["RepoTags"]:
                        val["RepoTags"].append(new_tag)
                    images[new_tag] = val
                    save_images(images)
                    return self._send_text("", status=201)
            return self._send_json({"message": f"No such image: {image_query}"}, status=404)

        # Push image
        if norm_path.startswith("/images/") and norm_path.endswith("/push"):
            image_name = norm_path[len("/images/"):-len("/push")]
            image_name = urllib.parse.unquote(image_name)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Transfer-Encoding", "chunked")
            self.end_headers()

            push_logs = [
                {"status": f"The push refers to repository [{image_name}]"},
                {"status": "Preparing", "id": "layer1"},
                {"status": "Preparing", "id": "layer2"},
                {"status": "Layer already exists", "id": "layer1"},
                {"status": "Pushed", "id": "layer2"},
                {"status": f"latest: digest: sha256:honorport00112233 size: 2100"}
            ]
            for log_item in push_logs:
                chunk = json.dumps(log_item) + "\n"
                chunk_bytes = chunk.encode("utf-8")
                self.wfile.write(f"{len(chunk_bytes):X}\r\n".encode("utf-8"))
                self.wfile.write(chunk_bytes)
                self.wfile.write(b"\r\n")
            self.wfile.write(b"0\r\n\r\n")
            return

        # Container create
        if norm_path == "/containers/create":
            return self._send_json({"Id": "c_auto_created_9019283", "Warnings": []}, status=201)

        if norm_path.startswith("/containers/") and norm_path.endswith("/start"):
            return self._send_text("", status=204)

        return self._send_json({"message": "Not implemented"}, status=404)

def run_inner_docker_daemon(host="127.0.0.1", port=2375):
    port = int(os.environ.get("DOCKER_DAEMON_PORT", port))
    HTTPServer.allow_reuse_address = True
    server = HTTPServer((host, port), DockerDaemonHandler)
    print(f"[+] Inner Docker Daemon listening on tcp://{host}:{port}")
    server.serve_forever()

if __name__ == "__main__":
    run_inner_docker_daemon()
