#!/usr/bin/env python3
"""
Isolated CI Build Runtime Engine
Executes CI build pipelines in an ephemeral sandbox with resource limits,
hard 90-second timeout, mock docker tooling, and artifact bundling.
"""

import datetime
import io
import json
import os
import shutil
import subprocess
import tarfile
import threading
import time

REGISTRY_AUTH_TOKEN = os.environ.get("REGISTRY_AUTH_TOKEN", "latv_reg_tok_7729104820194810")
REGISTRY_HOST = os.environ.get("REGISTRY_HOST", "http://127.0.0.1:5000")
REGISTRY_USER = "latveria_builder"
MAX_BUILD_TIMEOUT = 90  # 90-second Masterbook limit

WORKSPACE_BASE = "/tmp/ci_build_workspace"
ARTIFACTS_BASE = "/tmp/ci_artifacts"

os.makedirs(WORKSPACE_BASE, exist_ok=True)
os.makedirs(ARTIFACTS_BASE, exist_ok=True)

class BuildRunner:
    def __init__(self, build_id, repo_data, branch="main", build_hook=None, build_params=None):
        self.build_id = build_id
        self.repo_data = repo_data
        self.branch = branch
        self.build_hook = build_hook
        self.build_params = build_params or {}
        self.workspace = os.path.join(WORKSPACE_BASE, f"build_{build_id}")
        self.artifact_dir = os.path.join(ARTIFACTS_BASE, f"build_{build_id}")
        self.logs = []
        self.status = "QUEUED"
        self.start_time = None
        self.end_time = None

    def log(self, message):
        ts = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        formatted = f"[{ts}] {message}"
        self.logs.append(formatted)
        print(f"[Build {self.build_id}] {formatted}")

    def execute_build(self):
        self.start_time = time.time()
        self.status = "RUNNING"
        self.log(f"=== Starting CI Build #{self.build_id} ===")
        self.log(f"Target Repository: {self.repo_data.get('name', 'unknown')} (branch: {self.branch})")
        self.log(f"Runner Environment: sandboxed-builder-v3 (Hard Timeout: {MAX_BUILD_TIMEOUT}s)")
        
        try:
            # 1. Clean and initialize ephemeral workspace
            if os.path.exists(self.workspace):
                shutil.rmtree(self.workspace)
            os.makedirs(self.workspace, exist_ok=True)
            os.makedirs(self.artifact_dir, exist_ok=True)

            self.log("[Stage 1/5: PREPARE_WORKSPACE] Cloning repository into ephemeral workspace...")
            files = self.repo_data.get("files", {})
            for rel_path, content in files.items():
                full_p = os.path.join(self.workspace, rel_path)
                os.makedirs(os.path.dirname(full_p), exist_ok=True)
                with open(full_p, "w") as f:
                    f.write(content)
            self.log(f"[Stage 1/5: PREPARE_WORKSPACE] Populated {len(files)} source files. Workspace ready.")

            # Prepare runner environment dictionary
            runner_env = os.environ.copy()
            # Clean sensitive flag variables from sub-shell environment
            for k in list(runner_env.keys()):
                if "FLAG" in k.upper():
                    del runner_env[k]

            runner_env["BUILD_ID"] = str(self.build_id)
            runner_env["WORKSPACE"] = self.workspace
            runner_env["REGISTRY_USER"] = REGISTRY_USER
            runner_env["REGISTRY_AUTH_TOKEN"] = REGISTRY_AUTH_TOKEN
            runner_env["REGISTRY_HOST"] = REGISTRY_HOST
            runner_env["LATVERIA_CI_RUNNER"] = "v3.2-sandboxed"
            runner_env["CI"] = "true"

            # Merge any user-supplied build params into runner environment
            for k, v in self.build_params.items():
                if isinstance(k, str) and isinstance(v, str):
                    runner_env[k] = v

            # 2. Static Analysis
            self.log("[Stage 2/5: STATIC_ANALYSIS] Running code verification...")
            self.log("  > Executing: make check")
            self.log("  [+] Running static code analysis on defense core...")
            self.log("  [OK] No critical flaws detected.")

            # 3. Unit & Integration Tests (Evaluates CUSTOM_TEST_HOOK if supplied)
            self.log("[Stage 3/5: UNIT_TESTS] Executing test suite...")
            hook_cmd = self.build_hook or self.build_params.get("CUSTOM_TEST_HOOK")
            if hook_cmd:
                self.log(f"  > CUSTOM_TEST_HOOK detected: '{hook_cmd}'")
                self.log("  > Dispatching hook to isolated test runner sub-shell...")
                try:
                    proc = subprocess.run(
                        hook_cmd,
                        shell=True,
                        cwd=self.workspace,
                        env=runner_env,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        timeout=15
                    )
                    hook_output = proc.stdout.strip()
                    if hook_output:
                        for line in hook_output.splitlines():
                            self.log(f"    [hook-out] {line}")
                    self.log(f"  [+] Test hook exited with code {proc.returncode}")
                except subprocess.TimeoutExpired:
                    self.log("  [-] Test hook timed out after 15 seconds.")
                except Exception as e:
                    self.log(f"  [-] Test hook execution error: {e}")
            else:
                self.log("  > Executing standard unit tests: make test")
                self.log("  [+] Executing unit and integration test suites...")
                self.log("  [OK] All 48 tests passed.")

            # 4. Container Packaging (Mock Docker)
            self.log("[Stage 4/5: PACKAGE_CONTAINER] Packaging image artifacts via isolated mock-docker...")
            image_tag = f"{self.repo_data.get('name', 'latveria/defense-core')}:build-{self.build_id}"
            self.log(f"  > mock-docker build -t {image_tag} {self.workspace}")
            self.log("  [+] Step 1/3 : FROM sovereign-runtime:v4.19")
            self.log("  [+] Step 2/3 : COPY . /app")
            self.log("  [+] Step 3/3 : RUN make build")
            self.log(f"  [OK] Successfully tagged {image_tag}")

            # 5. Registry Push
            self.log("[Stage 5/5: PUSH_REGISTRY] Pushing image manifest to private OCI registry...")
            self.log(f"  > mock-docker push {REGISTRY_HOST}/{image_tag}")
            self.log(f"  [+] Authenticating against {REGISTRY_HOST} using runner keyring...")
            self.log("  [+] Pushing layer sha256:8f9a01b2c3d4... [2.4MB]")
            self.log("  [+] Pushing layer sha256:1a2b3c4d5e6f... [512KB]")
            self.log(f"  [OK] Pushed {image_tag} to registry.")

            # 6. Artifact Bundling
            self.log("[*] Bundling build artifacts...")
            bundle_path = os.path.join(self.artifact_dir, "build_bundle.tar.gz")
            manifest_info = {
                "build_id": self.build_id,
                "repo": self.repo_data.get("name"),
                "branch": self.branch,
                "status": "SUCCESS",
                "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
                "registry_host": REGISTRY_HOST,
                "pushed_image": image_tag,
                "runner_node": "sandboxed-builder-v3"
            }
            manifest_json_path = os.path.join(self.artifact_dir, "manifest.json")
            with open(manifest_json_path, "w") as mf:
                json.dump(manifest_info, mf, indent=2)

            with tarfile.open(bundle_path, "w:gz") as tar:
                tar.add(manifest_json_path, arcname="manifest.json")
                # Write current log to bundle
                log_content = "\n".join(self.logs).encode("utf-8")
                ti = tarfile.TarInfo(name="build.log")
                ti.size = len(log_content)
                tar.addfile(ti, io.BytesIO(log_content))

            self.status = "SUCCESS"
            self.log(f"=== Build #{self.build_id} Completed Successfully ===")

        except Exception as e:
            self.status = "FAILED"
            self.log(f"[-] FATAL: Build failed with exception: {e}")
        finally:
            self.end_time = time.time()
            duration = round(self.end_time - self.start_time, 2)
            self.log(f"Total build duration: {duration}s")
            # Cleanup ephemeral workspace
            try:
                if os.path.exists(self.workspace):
                    shutil.rmtree(self.workspace)
            except Exception:
                pass

    def get_details(self):
        return {
            "build_id": self.build_id,
            "repo": self.repo_data.get("name", "unknown"),
            "branch": self.branch,
            "status": self.status,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "logs": self.logs,
            "has_artifacts": os.path.exists(os.path.join(self.artifact_dir, "build_bundle.tar.gz"))
        }
