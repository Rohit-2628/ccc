#!/usr/bin/env python3
"""
Git HTTP Smart Protocol Server & Repository Viewer for X04 (Broken CI)
Listens on 127.0.0.1:8081.
Provides Git HTTP smart service (clone/push) and REST endpoints for browsing repo structure.
"""

import os
import json
import subprocess
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

STORAGE_ROOT = Path("/tmp/x04_storage")
GIT_DIR = STORAGE_ROOT / "git_repos"

class GitHTTPHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def _send_json(self, data, status=200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # REST: /api/git/repos
        if path == "/api/git/repos" or path == "/repos":
            repos = []
            if GIT_DIR.exists():
                for p in GIT_DIR.iterdir():
                    if p.is_dir() and p.name.endswith(".git"):
                        repos.append({
                            "name": p.name[:-4],
                            "full_name": f"latveria/{p.name[:-4]}",
                            "clone_url_http": f"/api/git/{p.name}",
                            "clone_url_ssh": f"git@target:{p.name}",
                            "default_branch": "main",
                            "description": "Latveria Sovereign Defense Network Sentinel Node"
                        })
            return self._send_json({"repositories": repos})

        # REST: /api/git/repos/<repo>/commits
        if "/commits" in path:
            parts = path.strip("/").split("/")
            repo_name = "defense-network.git"
            repo_path = GIT_DIR / repo_name
            if repo_path.exists():
                try:
                    res = subprocess.run(
                        ["git", "log", "-n", "10", "--pretty=format:%H|%an|%ae|%ad|%s", "--date=iso"],
                        cwd=repo_path, capture_output=True, text=True, check=True
                    )
                    commits = []
                    for line in res.stdout.splitlines():
                        if "|" in line:
                            h, an, ae, ad, s = line.split("|", 4)
                            commits.append({
                                "hash": h,
                                "author": an,
                                "email": ae,
                                "date": ad,
                                "message": s
                            })
                    return self._send_json({"repo": "defense-network", "commits": commits})
                except Exception as e:
                    return self._send_json({"error": str(e)}, status=500)

        # REST: /api/git/repos/<repo>/tree
        if "/tree" in path:
            repo_path = GIT_DIR / "defense-network.git"
            if repo_path.exists():
                try:
                    res = subprocess.run(
                        ["git", "ls-tree", "-r", "--name-only", "HEAD"],
                        cwd=repo_path, capture_output=True, text=True, check=True
                    )
                    files = [f for f in res.stdout.splitlines() if f.strip()]
                    return self._send_json({"repo": "defense-network", "branch": "main", "files": files})
                except Exception as e:
                    return self._send_json({"error": str(e)}, status=500)

        # REST: /api/git/repos/<repo>/blob/<filepath>
        if "/blob/" in path:
            file_subpath = path.split("/blob/", 1)[1]
            file_subpath = urllib.parse.unquote(file_subpath)
            repo_path = GIT_DIR / "defense-network.git"
            if repo_path.exists():
                try:
                    res = subprocess.run(
                        ["git", "show", f"HEAD:{file_subpath}"],
                        cwd=repo_path, capture_output=True, text=True, check=True
                    )
                    return self._send_json({"path": file_subpath, "content": res.stdout})
                except Exception as e:
                    return self._send_json({"error": f"File '{file_subpath}' not found: {e}"}, status=404)

        # Git Smart HTTP: /info/refs?service=git-upload-pack
        if "/info/refs" in path:
            query = urllib.parse.parse_qs(parsed.query)
            service = query.get("service", [""])[0]
            repo_name = path.split("/info/refs")[0].strip("/").split("/")[-1]
            if not repo_name.endswith(".git"):
                repo_name += ".git"
            repo_path = GIT_DIR / repo_name
            
            if not repo_path.exists():
                self.send_response(404)
                self.end_headers()
                return

            if service in ["git-upload-pack", "git-receive-pack"]:
                proc = subprocess.run(
                    [service, "--stateless-rpc", "--advertise-refs", str(repo_path)],
                    capture_output=True
                )
                self.send_response(200)
                self.send_header("Content-Type", f"application/x-{service}-advertisement")
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                # Packet line header for smart HTTP
                first_line = f"# service={service}\n"
                pkt_len = len(first_line) + 4
                self.wfile.write(f"{pkt_len:04x}".encode("ascii") + first_line.encode("utf-8") + b"0000")
                self.wfile.write(proc.stdout)
                return

        self._send_json({"message": "Git HTTP Service Active", "repo": "/api/git/defense-network.git"})

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        # Git Smart HTTP RPC: /git-upload-pack or /git-receive-pack
        if path.endswith("/git-upload-pack") or path.endswith("/git-receive-pack"):
            service = "git-upload-pack" if path.endswith("/git-upload-pack") else "git-receive-pack"
            repo_name = path.rsplit("/", 1)[0].strip("/").split("/")[-1]
            if not repo_name.endswith(".git"):
                repo_name += ".git"
            repo_path = GIT_DIR / repo_name

            if not repo_path.exists():
                self.send_response(404)
                self.end_headers()
                return

            content_length = int(self.headers.get("Content-Length", 0))
            in_data = self.rfile.read(content_length)

            proc = subprocess.run(
                [service, "--stateless-rpc", str(repo_path)],
                input=in_data,
                capture_output=True
            )

            self.send_response(200)
            self.send_header("Content-Type", f"application/x-{service}-result")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Content-Length", str(len(proc.stdout)))
            self.end_headers()
            self.wfile.write(proc.stdout)
            return

        self._send_json({"error": "Unknown POST action"}, status=400)

def run_git_http_server(host="127.0.0.1", port=8081):
    port = int(os.environ.get("GIT_HTTP_PORT", port))
    HTTPServer.allow_reuse_address = True
    server = HTTPServer((host, port), GitHTTPHandler)
    print(f"[+] Git HTTP Smart Server listening on http://{host}:{port}")
    server.serve_forever()

if __name__ == "__main__":
    run_git_http_server()
