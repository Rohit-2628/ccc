#!/usr/bin/env python3
"""
CI Runner Execution Engine for X04 (Broken CI)
Executes pipeline stages, build scripts, and custom commands within an isolated workspace.
Equipped with DOCKER_HOST pointing to the challenge-local Inner Docker Daemon.
"""

import os
import sys
import json
import time
import subprocess
import shutil
from pathlib import Path

STORAGE_ROOT = Path("/tmp/x04_storage")
CI_DIR = STORAGE_ROOT / "ci_workspace"
RUNNER_WORK_DIR = STORAGE_ROOT / "runner_sandbox"

def execute_pipeline_job(repo="latveria/defense-network", branch="main", custom_command=None, pipeline_script=None):
    """Executes a pipeline build job and returns the build execution record."""
    build_id = str(int(time.time() * 1000) % 1000000)
    timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    
    os.makedirs(RUNNER_WORK_DIR, exist_ok=True)
    job_workspace = RUNNER_WORK_DIR / f"job_{build_id}"
    os.makedirs(job_workspace, exist_ok=True)

    log_lines = []
    log_lines.append(f"[CI-RUNNER] Initializing Worker worker-node-latveria-01 for Job #{build_id}")
    log_lines.append(f"[CI-RUNNER] Repository: {repo} | Branch: {branch} | Timestamp: {timestamp}")
    log_lines.append(f"[CI-RUNNER] Environment: DOCKER_HOST=tcp://127.0.0.1:2375 (Inner DinD Daemon)")
    
    # Clone / copy repo files into job workspace
    repo_bare = STORAGE_ROOT / "git_repos" / "defense-network.git"
    if repo_bare.exists():
        try:
            subprocess.run(["git", "clone", str(repo_bare), str(job_workspace)], capture_output=True, check=True)
            log_lines.append(f"[STAGE: CLONE] Checked out repository HEAD -> {job_workspace}")
        except Exception as e:
            log_lines.append(f"[STAGE: CLONE] Warning: Could not clone repo: {e}")

    # Runner execution environment
    env = os.environ.copy()
    # Clean sensitive flag variables from sub-shell environment
    for k in list(env.keys()):
        if "FLAG" in k.upper():
            del env[k]

    env["DOCKER_HOST"] = "tcp://127.0.0.1:2375"
    env["CI"] = "true"
    env["CI_BUILD_ID"] = build_id
    env["REGISTRY_HOST"] = "registry.latveria.local:5000"
    
    # Ensure docker CLI wrapper is accessible in PATH
    docker_cli_dir = str(Path(__file__).resolve().parent.parent / "inner_docker")
    env["PATH"] = f"{docker_cli_dir}:/app/challenge/inner_docker:" + env.get("PATH", "/usr/local/bin:/usr/bin:/bin")

    status = "SUCCESS"

    if custom_command:
        log_lines.append(f"[STAGE: CUSTOM_HOOK] Executing user-specified pipeline hook command:")
        log_lines.append(f"$ {custom_command}")
        try:
            # We explicitly execute through bash/sh or python depending on command
            res = subprocess.run(
                custom_command,
                shell=True,
                cwd=job_workspace,
                env=env,
                capture_output=True,
                text=True,
                timeout=25
            )
            if res.stdout:
                log_lines.append(res.stdout)
            if res.stderr:
                log_lines.append(res.stderr)
            if res.returncode != 0:
                log_lines.append(f"[COMMAND-EXIT] Exited with status {res.returncode}")
                status = "FAILED"
            else:
                log_lines.append("[COMMAND-EXIT] Success (code 0)")
        except subprocess.TimeoutExpired:
            log_lines.append("[TIMEOUT] Command execution exceeded 25s timeout limit.")
            status = "FAILED"
        except Exception as e:
            log_lines.append(f"[ERROR] Execution error: {e}")
            status = "FAILED"
    elif pipeline_script:
        log_lines.append(f"[STAGE: PIPELINE_SCRIPT] Running provided pipeline script:")
        try:
            res = subprocess.run(
                pipeline_script,
                shell=True,
                cwd=job_workspace,
                env=env,
                capture_output=True,
                text=True,
                timeout=25
            )
            if res.stdout:
                log_lines.append(res.stdout)
            if res.stderr:
                log_lines.append(res.stderr)
            if res.returncode != 0:
                status = "FAILED"
        except Exception as e:
            log_lines.append(f"[ERROR] Pipeline execution failed: {e}")
            status = "FAILED"
    else:
        # Default standard pipeline
        log_lines.append("[STAGE 1: LINT] Checking syntax...")
        log_lines.append("Syntax check: PASS")
        log_lines.append("[STAGE 2: TEST] Running test suite...")
        log_lines.append("Test Sentinel Health Check: PASSED")
        log_lines.append("[STAGE 3: DOCKER-BUILD] Building container on inner Docker daemon...")
        
        # Run docker build via inner daemon
        try:
            res = subprocess.run(
                ["python3", f"{docker_cli_dir}/docker_cli.py", "build", "-t", "registry.latveria.local:5000/defense/sentinel-node:v2.1.0", "."],
                cwd=job_workspace,
                env=env,
                capture_output=True,
                text=True,
                timeout=15
            )
            if res.stdout:
                log_lines.append(res.stdout)
        except Exception as e:
            log_lines.append(f"Docker build output: {e}")

        log_lines.append("[STAGE 4: DEPLOY-MOCK] Ready for production verification.")

    log_lines.append(f"[CI-RUNNER] Job #{build_id} finished with status: {status}")
    full_log = "\n".join(log_lines)

    build_record = {
        "build_id": build_id,
        "repo": repo,
        "branch": branch,
        "status": status,
        "timestamp": timestamp,
        "triggered_by": "api-trigger" if (custom_command or pipeline_script) else "automated",
        "stages": ["lint", "test", "build_image", "deploy_mock"],
        "log": full_log
    }

    # Save to builds.json
    builds_file = CI_DIR / "builds.json"
    builds = []
    if builds_file.exists():
        try:
            builds = json.loads(builds_file.read_text())
        except Exception:
            builds = []
    builds.insert(0, build_record)
    builds_file.write_text(json.dumps(builds[:30], indent=2))

    # Cleanup temp workspace
    if job_workspace.exists():
        shutil.rmtree(job_workspace, ignore_errors=True)

    return build_record

if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else None
    res = execute_pipeline_job(custom_command=cmd)
    print(res["log"])
