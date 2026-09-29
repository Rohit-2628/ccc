#!/usr/bin/env python3
"""
Seed Snapshot Generator & Reset Utility for X04 (Broken CI)
Initializes challenge-local Git repositories, CI runner workspace, inner Docker daemon state/images,
OCI image registry blobs/manifests, production deployment runtime, and team flag.
"""

import os
import io
import json
import tarfile
import hashlib
import shutil
import subprocess
from pathlib import Path

STORAGE_ROOT = Path("/tmp/x04_storage")
GIT_DIR = STORAGE_ROOT / "git_repos"
CI_DIR = STORAGE_ROOT / "ci_workspace"
DIND_DIR = STORAGE_ROOT / "dind_storage"
REGISTRY_DIR = STORAGE_ROOT / "registry"
PRODUCTION_DIR = STORAGE_ROOT / "production"
FLAG_DIR = STORAGE_ROOT / "flag"

DEFAULT_FLAG = "YUVA{d1nd_c1_runn3r_r3g1stry_pr0d_p1v0t_x04}"
SIGNER_ID = "DOOM-DEPLOYMENT-SIGNER-04"
PROD_DEPLOY_SIGNING_KEY = "latv_prod_deploy_sig_8829104820194812"
REGISTRY_AUTH_TOKEN = "latv_inner_reg_secret_7719204819"

def create_tar_gz(files: dict) -> bytes:
    """Create in-memory tar.gz from a dict of filename -> content (str or bytes)."""
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for name, content in files.items():
            if isinstance(content, str):
                data = content.encode("utf-8")
            else:
                data = content
            info = tarfile.TarInfo(name=name)
            info.size = len(data)
            info.mtime = 1727337600  # Deterministic timestamp (2024-09-26)
            info.mode = 0o755 if ("bin" in name or name.endswith(".sh") or name.endswith(".py")) else 0o644
            info.uname = "latveria"
            info.gname = "latveria"
            tar.addfile(info, io.BytesIO(data))
    return buf.getvalue()

def init_git_repository():
    """Seed synthetic Git repository 'defense-network.git' with realistic project code and CI pipeline."""
    os.makedirs(GIT_DIR, exist_ok=True)
    repo_bare = GIT_DIR / "defense-network.git"
    
    if repo_bare.exists():
        shutil.rmtree(repo_bare)
    
    # Create temporary working copy to build initial git history
    work_dir = STORAGE_ROOT / "git_temp_init"
    if work_dir.exists():
        shutil.rmtree(work_dir)
    os.makedirs(work_dir, exist_ok=True)

    # Repository files
    dockerfile_content = """# Latveria Sovereign Defense Network Sentinel Node
FROM registry.latveria.local:5000/system/base-kernel:v1.0.0 AS base
WORKDIR /app
COPY src/ /app/src/
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 9090
ENTRYPOINT ["python3", "src/server.py"]
"""
    
    pipeline_yml = """# Latveria Sovereign CI/CD Pipeline Definition
# Service: Defense Sentinel Network Node
version: "2.4"

stages:
  - lint
  - test
  - build_image
  - deploy_mock

variables:
  REGISTRY_HOST: "registry.latveria.local:5000"
  IMAGE_NAME: "defense/sentinel-node"
  IMAGE_TAG: "v2.1.0"
  DEPLOY_TARGET: "SOVEREIGN-PROD-MAINFRAME-01"

jobs:
  lint:
    stage: lint
    script:
      - echo "[LINT] Verifying Python syntax and style standards..."
      - python3 -m py_compile src/server.py

  test:
    stage: test
    script:
      - echo "[TEST] Running unit and integration test suite..."
      - python3 -c "print('Test Sentinel Health Check: PASSED')"

  build_image:
    stage: build_image
    script:
      - echo "[DOCKER-BUILD] Communicating with inner Docker daemon (DOCKER_HOST)..."
      - docker build -t ${REGISTRY_HOST}/${IMAGE_NAME}:${IMAGE_TAG} .
      - echo "[DOCKER-PUSH] Pushing artifact to challenge-local registry..."
      - docker push ${REGISTRY_HOST}/${IMAGE_NAME}:${IMAGE_TAG}

  deploy_mock:
    stage: deploy_mock
    script:
      - echo "[DEPLOY-MOCK] Verifying deployment signature against sovereign production mock..."
      - echo "[INFO] Production promotion requires cryptographically signed descriptor."
"""

    server_py = """#!/usr/bin/env python3
\"\"\"
Latveria Defense Network Sentinel Node Runtime
Version: 2.1.0
\"\"\"
import os
import sys

def main():
    print("[*] Latveria Sovereign Defense Sentinel v2.1.0 active.")
    print("[*] Shield telemetry frequency: 142.8 GHz")

if __name__ == '__main__':
    main()
"""

    docker_config = {
        "auths": {
            "registry.latveria.local:5000": {
                "auth": "bGF0dmVyaWE6bGF0dl9pbm5lcl9yZWdfc2VjcmV0Xzc3MTkyMDQ4MTk="
            }
        }
    }

    readme_md = """# Latveria Sovereign Defense Network

This repository contains the source code, Docker build specifications, and automated CI pipeline configuration for the Sovereign Defense Network Sentinel Node.

## Build & Test Pipeline
The pipeline runs automatically upon commit or manual trigger via the CI Web Console:
- Stage 1: Syntax linting
- Stage 2: Integration tests
- Stage 3: DinD Container Build & Push to internal registry (`registry.latveria.local:5000`)
- Stage 4: Production verification

Maintained by Latverian Autonomous Systems Division.
"""

    (work_dir / "Dockerfile").write_text(dockerfile_content)
    os.makedirs(work_dir / ".ci", exist_ok=True)
    (work_dir / ".ci" / "pipeline.yml").write_text(pipeline_yml)
    os.makedirs(work_dir / "src", exist_ok=True)
    (work_dir / "src" / "server.py").write_text(server_py)
    (work_dir / "requirements.txt").write_text("# Core dependencies\n")
    os.makedirs(work_dir / ".docker", exist_ok=True)
    (work_dir / ".docker" / "config.json").write_text(json.dumps(docker_config, indent=2))
    (work_dir / "README.md").write_text(readme_md)

    try:
        subprocess.run(["git", "init", "-b", "main"], cwd=work_dir, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Latveria CI Bot"], cwd=work_dir, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "ci-bot@latveria.local"], cwd=work_dir, check=True, capture_output=True)
        subprocess.run(["git", "add", "."], cwd=work_dir, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial commit: Defense Sentinel Node v2.1.0 & DinD CI Pipeline"], cwd=work_dir, check=True, capture_output=True)
        
        # Add another commit showing CI configuration update
        (work_dir / "src" / "server.py").write_text(server_py + "\n# Build revision 402 - DinD integration verified\n")
        subprocess.run(["git", "commit", "-am", "ci: update pipeline build hooks and DinD daemon integration"], cwd=work_dir, check=True, capture_output=True)
        
        # Create bare clone
        subprocess.run(["git", "clone", "--bare", str(work_dir), str(repo_bare)], check=True, capture_output=True)
        # Enable receive.denyCurrentBranch or update-server-info
        subprocess.run(["git", "config", "http.receivepack", "true"], cwd=repo_bare, check=True, capture_output=True)
        subprocess.run(["git", "update-server-info"], cwd=repo_bare, check=True, capture_output=True)
    finally:
        if work_dir.exists():
            shutil.rmtree(work_dir)
    print("[+] Git repository 'defense-network.git' initialized with 2 commits.")

def init_dind_and_registry():
    """Seed inner Docker daemon cache, images, and OCI image registry."""
    os.makedirs(DIND_DIR / "images", exist_ok=True)
    os.makedirs(DIND_DIR / "containers", exist_ok=True)
    os.makedirs(REGISTRY_DIR / "blobs", exist_ok=True)
    os.makedirs(REGISTRY_DIR / "manifests", exist_ok=True)

    # 1. Base Layer for system/base-kernel:v1.0.0
    base_files = {
        "etc/os-release": "NAME=\"Latveria Linux\"\nVERSION=\"6.1-LTS\"\nID=latveria\n",
        "bin/busybox": "#!/bin/sh\necho 'Latveria Base Busybox'\n",
        "bin/sh": "#!/bin/sh\nexec /bin/busybox \"$@\"\n"
    }
    base_layer_data = create_tar_gz(base_files)
    base_layer_digest = "sha256:" + hashlib.sha256(base_layer_data).hexdigest()
    (REGISTRY_DIR / "blobs" / base_layer_digest.replace(":", "_")).write_bytes(base_layer_data)

    # 2. Layer for defense/sentinel-node:v2.1.0
    sentinel_files = {
        "app/src/server.py": "# Latveria Sovereign Defense Sentinel Node v2.1.0\nprint('Sentinel Active')\n",
        "etc/sentinel.conf": "mode=ACTIVE\ncluster=SOVEREIGN_PRIME\n"
    }
    sentinel_layer_data = create_tar_gz(sentinel_files)
    sentinel_layer_digest = "sha256:" + hashlib.sha256(sentinel_layer_data).hexdigest()
    (REGISTRY_DIR / "blobs" / sentinel_layer_digest.replace(":", "_")).write_bytes(sentinel_layer_data)

    # 3. Layer for internal/deployment-signer:v1.0.0 (Contains deployment credentials & signing key)
    signer_files = {
        "etc/latveria/signer.key": (
            "-----BEGIN LATVERIA DEPLOYMENT SIGNER KEY-----\n"
            f"SIGNER_ID={SIGNER_ID}\n"
            f"PROD_DEPLOY_SIGNING_KEY={PROD_DEPLOY_SIGNING_KEY}\n"
            f"REGISTRY_AUTH_TOKEN={REGISTRY_AUTH_TOKEN}\n"
            "TARGET_CLUSTER=SOVEREIGN-PROD-MAINFRAME-01\n"
            "PRODUCTION_DEPLOY_ENDPOINT=http://127.0.0.1:8083/api/production/deploy\n"
            "-----END LATVERIA DEPLOYMENT SIGNER KEY-----\n"
        ),
        "root/.docker/config.json": json.dumps({
            "auths": {
                "registry.latveria.local:5000": {
                    "auth": "bGF0dmVyaWE6bGF0dl9pbm5lcl9yZWdfc2VjcmV0Xzc3MTkyMDQ4MTk="
                }
            }
        }, indent=2),
        "bin/sign-deployment.sh": (
            "#!/bin/sh\n"
            f"# Latveria Deployment Signer Utility v1.0.0\n"
            f"export SIGNER_ID=\"{SIGNER_ID}\"\n"
            f"export PROD_DEPLOY_SIGNING_KEY=\"{PROD_DEPLOY_SIGNING_KEY}\"\n"
            "echo \"[SIGNER] Deployment signer active for SOVEREIGN-PROD-MAINFRAME-01\"\n"
        )
    }
    signer_layer_data = create_tar_gz(signer_files)
    signer_layer_digest = "sha256:" + hashlib.sha256(signer_layer_data).hexdigest()
    (REGISTRY_DIR / "blobs" / signer_layer_digest.replace(":", "_")).write_bytes(signer_layer_data)

    # Build Image Configs & Manifests
    # A) defense/sentinel-node:v2.1.0
    sentinel_cfg = {
        "architecture": "amd64",
        "os": "linux",
        "config": {
            "Env": ["PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin", "NODE_ROLE=SENTINEL_GUARD"],
            "Cmd": ["python3", "src/server.py"]
        },
        "rootfs": {
            "type": "layers",
            "diff_ids": [base_layer_digest, sentinel_layer_digest]
        }
    }
    sentinel_cfg_data = json.dumps(sentinel_cfg, indent=2).encode("utf-8")
    sentinel_cfg_digest = "sha256:" + hashlib.sha256(sentinel_cfg_data).hexdigest()
    (REGISTRY_DIR / "blobs" / sentinel_cfg_digest.replace(":", "_")).write_bytes(sentinel_cfg_data)

    sentinel_manifest = {
        "schemaVersion": 2,
        "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
        "config": {
            "mediaType": "application/vnd.docker.container.image.v1+json",
            "size": len(sentinel_cfg_data),
            "digest": sentinel_cfg_digest
        },
        "layers": [
            {"mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip", "size": len(base_layer_data), "digest": base_layer_digest},
            {"mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip", "size": len(sentinel_layer_data), "digest": sentinel_layer_digest}
        ]
    }
    sentinel_manifest_data = json.dumps(sentinel_manifest, indent=2).encode("utf-8")
    sentinel_manifest_digest = "sha256:" + hashlib.sha256(sentinel_manifest_data).hexdigest()
    (REGISTRY_DIR / "blobs" / sentinel_manifest_digest.replace(":", "_")).write_bytes(sentinel_manifest_data)

    os.makedirs(REGISTRY_DIR / "manifests" / "defense" / "sentinel-node", exist_ok=True)
    (REGISTRY_DIR / "manifests" / "defense" / "sentinel-node" / "v2.1.0.json").write_bytes(sentinel_manifest_data)
    (REGISTRY_DIR / "manifests" / "defense" / "sentinel-node" / "latest.json").write_bytes(sentinel_manifest_data)

    # B) internal/deployment-signer:v1.0.0
    signer_cfg = {
        "architecture": "amd64",
        "os": "linux",
        "config": {
            "Env": [
                f"SIGNER_ID={SIGNER_ID}",
                f"PROD_DEPLOY_SIGNING_KEY={PROD_DEPLOY_SIGNING_KEY}",
                f"REGISTRY_AUTH_TOKEN={REGISTRY_AUTH_TOKEN}",
                "TARGET_CLUSTER=SOVEREIGN-PROD-MAINFRAME-01"
            ],
            "Cmd": ["/bin/sign-deployment.sh"]
        },
        "rootfs": {
            "type": "layers",
            "diff_ids": [base_layer_digest, signer_layer_digest]
        }
    }
    signer_cfg_data = json.dumps(signer_cfg, indent=2).encode("utf-8")
    signer_cfg_digest = "sha256:" + hashlib.sha256(signer_cfg_data).hexdigest()
    (REGISTRY_DIR / "blobs" / signer_cfg_digest.replace(":", "_")).write_bytes(signer_cfg_data)

    signer_manifest = {
        "schemaVersion": 2,
        "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
        "config": {
            "mediaType": "application/vnd.docker.container.image.v1+json",
            "size": len(signer_cfg_data),
            "digest": signer_cfg_digest
        },
        "layers": [
            {"mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip", "size": len(base_layer_data), "digest": base_layer_digest},
            {"mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip", "size": len(signer_layer_data), "digest": signer_layer_digest}
        ]
    }
    signer_manifest_data = json.dumps(signer_manifest, indent=2).encode("utf-8")
    signer_manifest_digest = "sha256:" + hashlib.sha256(signer_manifest_data).hexdigest()
    (REGISTRY_DIR / "blobs" / signer_manifest_digest.replace(":", "_")).write_bytes(signer_manifest_data)

    os.makedirs(REGISTRY_DIR / "manifests" / "internal" / "deployment-signer", exist_ok=True)
    (REGISTRY_DIR / "manifests" / "internal" / "deployment-signer" / "v1.0.0.json").write_bytes(signer_manifest_data)
    (REGISTRY_DIR / "manifests" / "internal" / "deployment-signer" / "latest.json").write_bytes(signer_manifest_data)

    # Save metadata for Inner Docker Daemon Images
    dind_images = {
        "latveria/ci-builder-base:latest": {
            "Id": "sha256:d891b2c4e5f60718293a4b5c6d7e8f90123456789abcdef0123456789abcdef0",
            "RepoTags": ["latveria/ci-builder-base:latest"],
            "Size": 1845000,
            "Created": 1727337600,
            "Config": {
                "Env": ["PATH=/usr/local/bin:/usr/bin:/bin", "CI=true", "DOCKER_HOST=tcp://127.0.0.1:2375"],
                "Cmd": ["/bin/sh"]
            },
            "History": [
                {"created_by": "/bin/sh -c #(nop) ADD file:... in /", "empty_layer": False},
                {"created_by": "RUN apk add --no-cache git python3 docker-cli", "empty_layer": False}
            ]
        },
        "registry.latveria.local:5000/defense/sentinel-node:v2.1.0": {
            "Id": sentinel_manifest_digest,
            "RepoTags": ["registry.latveria.local:5000/defense/sentinel-node:v2.1.0", "registry.latveria.local:5000/defense/sentinel-node:latest"],
            "Size": len(base_layer_data) + len(sentinel_layer_data),
            "Created": 1727337600,
            "Config": sentinel_cfg["config"],
            "ManifestDigest": sentinel_manifest_digest,
            "Layers": [base_layer_digest, sentinel_layer_digest],
            "History": [
                {"created_by": "FROM registry.latveria.local:5000/system/base-kernel:v1.0.0", "empty_layer": True},
                {"created_by": "COPY src/ /app/src/", "empty_layer": False},
                {"created_by": "CMD [\"python3\", \"src/server.py\"]", "empty_layer": True}
            ]
        },
        "registry.latveria.local:5000/internal/deployment-signer:v1.0.0": {
            "Id": signer_manifest_digest,
            "RepoTags": ["registry.latveria.local:5000/internal/deployment-signer:v1.0.0", "registry.latveria.local:5000/internal/deployment-signer:latest"],
            "Size": len(base_layer_data) + len(signer_layer_data),
            "Created": 1727337600,
            "Config": signer_cfg["config"],
            "ManifestDigest": signer_manifest_digest,
            "Layers": [base_layer_digest, signer_layer_digest],
            "History": [
                {"created_by": "FROM registry.latveria.local:5000/system/base-kernel:v1.0.0", "empty_layer": True},
                {"created_by": f"ENV SIGNER_ID={SIGNER_ID} PROD_DEPLOY_SIGNING_KEY={PROD_DEPLOY_SIGNING_KEY} REGISTRY_AUTH_TOKEN={REGISTRY_AUTH_TOKEN}", "empty_layer": True},
                {"created_by": "COPY etc/latveria/signer.key /etc/latveria/signer.key", "empty_layer": False},
                {"created_by": "CMD [\"/bin/sign-deployment.sh\"]", "empty_layer": True}
            ]
        }
    }
    (DIND_DIR / "images.json").write_text(json.dumps(dind_images, indent=2))
    print("[+] Inner Docker daemon storage and OCI Registry seeded successfully.")

def init_ci_workspace():
    """Initialize CI runner workspace and build history."""
    os.makedirs(CI_DIR, exist_ok=True)
    builds = [
        {
            "build_id": "401",
            "repo": "latveria/defense-network",
            "branch": "main",
            "commit": "a810f2c",
            "status": "SUCCESS",
            "timestamp": "2026-09-26T09:00:00Z",
            "triggered_by": "git-push",
            "stages": ["lint", "test", "build_image", "deploy_mock"],
            "log": (
                "[CI-RUNNER] Starting Job #401 on worker-node-latveria-01\n"
                "[STAGE 1: LINT] Verifying Python syntax and style standards...\n"
                "Syntax check: PASS (0 errors)\n"
                "[STAGE 2: TEST] Running unit and integration test suite...\n"
                "Test Sentinel Health Check: PASSED\n"
                "[STAGE 3: DOCKER-BUILD] Connecting to Inner Docker Daemon (tcp://127.0.0.1:2375)...\n"
                "Sending build context to Docker daemon...\n"
                "Step 1/5 : FROM registry.latveria.local:5000/system/base-kernel:v1.0.0\n"
                "Step 2/5 : WORKDIR /app\n"
                "Step 3/5 : COPY src/ /app/src/\n"
                "Step 4/5 : RUN pip install --no-cache-dir -r requirements.txt\n"
                "Step 5/5 : CMD python3 src/server.py\n"
                "Successfully built sha256:a1b2c3d4e5f6\n"
                "Successfully tagged registry.latveria.local:5000/defense/sentinel-node:v2.1.0\n"
                "[STAGE 4: DEPLOY-MOCK] Verifying deployment signature against sovereign production mock...\n"
                "Build #401 finished successfully in 4.18s\n"
            )
        }
    ]
    (CI_DIR / "builds.json").write_text(json.dumps(builds, indent=2))
    print("[+] CI workspace initialized with baseline build history.")

def init_production_and_flag():
    """Initialize production mock state."""
    os.makedirs(PRODUCTION_DIR, exist_ok=True)
    os.makedirs(FLAG_DIR, exist_ok=True)
    
    prod_state = {
        "cluster_name": "SOVEREIGN-PROD-MAINFRAME-01",
        "active_image": "registry.latveria.local:5000/defense/sentinel-node:v2.1.0",
        "active_digest": None, # Will be set during verification
        "status": "RUNNING_LOCKED",
        "defense_shield": "ONLINE (100% MAXIMUM SOVEREIGNTY)",
        "allowed_signer": SIGNER_ID,
        "last_promotion": "2026-09-26T09:00:15Z",
        "unlocked": False
    }
    (PRODUCTION_DIR / "state.json").write_text(json.dumps(prod_state, indent=2))
    print(f"[+] Production mock state and flag initialized.")

def reset_all():
    """Full deterministic state reset."""
    print("[*] Performing full X04 sandbox state teardown and deterministic reset...")
    if STORAGE_ROOT.exists():
        shutil.rmtree(STORAGE_ROOT)
    os.makedirs(STORAGE_ROOT, exist_ok=True)
    init_git_repository()
    init_dind_and_registry()
    init_ci_workspace()
    init_production_and_flag()
    print("[*] X04 reset complete. All components pristine.")

if __name__ == "__main__":
    reset_all()
