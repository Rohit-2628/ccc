#!/usr/bin/env python3
"""
Seed Snapshot Generator & Reset Utility for XO-9 (Honorport Heist - Docker in Docker)
Initializes Honorport logistics database, container deployment workspace, inner Docker daemon state/images,
OCI image registry blobs/manifests, Honorport Mainframe Vault runtime, and team flag.
"""

import os
import io
import json
import tarfile
import hashlib
import shutil
import subprocess
from pathlib import Path

STORAGE_ROOT = Path("/tmp/xo9_storage")
LOGISTICS_DIR = STORAGE_ROOT / "logistics_db"
DEPLOYMENT_DIR = STORAGE_ROOT / "deployment_workspace"
DIND_DIR = STORAGE_ROOT / "dind_storage"
REGISTRY_DIR = STORAGE_ROOT / "registry"
PRODUCTION_DIR = STORAGE_ROOT / "production"
FLAG_DIR = STORAGE_ROOT / "flag"

DEFAULT_FLAG = "YUVA{d1nd_h0n0rp0rt_h31st_d0ck3r_1n_d0ck3r_x09}"
HARBOR_MASTER_ID = "HONORPORT-HARBOR-MASTER-09"
VAULT_HMAC_SECRET_KEY = "honorport_vault_sig_7749102837194821"
REGISTRY_AUTH_TOKEN = "honorport_reg_token_9918274615"

def get_flag():
    flag_file = FLAG_DIR / "flag.txt"
    if flag_file.exists():
        return flag_file.read_text().strip()
    return os.environ.get("FLAG", DEFAULT_FLAG)

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
            info.mtime = 1727337600  # Deterministic timestamp
            info.mode = 0o755 if ("bin" in name or name.endswith(".sh") or name.endswith(".py")) else 0o644
            info.uname = "honorport"
            info.gname = "honorport"
            tar.addfile(info, io.BytesIO(data))
    return buf.getvalue()

def init_dind_and_registry():
    """Seed inner Docker daemon cache, images, and OCI image registry."""
    os.makedirs(DIND_DIR / "images", exist_ok=True)
    os.makedirs(DIND_DIR / "containers", exist_ok=True)
    os.makedirs(REGISTRY_DIR / "blobs", exist_ok=True)
    os.makedirs(REGISTRY_DIR / "manifests", exist_ok=True)

    # 1. Base OS Layer
    base_files = {
        "etc/os-release": "NAME=\"Honorport OS\"\nVERSION=\"24.04-LTS\"\nID=honorport\n",
        "bin/busybox": "#!/bin/sh\necho 'Honorport Base Shell'\n",
        "bin/sh": "#!/bin/sh\nexec /bin/busybox \"$@\"\n"
    }
    base_layer_data = create_tar_gz(base_files)
    base_layer_digest = "sha256:" + hashlib.sha256(base_layer_data).hexdigest()
    (REGISTRY_DIR / "blobs" / base_layer_digest.replace(":", "_")).write_bytes(base_layer_data)

    # 2. Cargo Manifest Guard Layer
    guard_files = {
        "app/cargo_validator.py": "# Honorport Cargo Manifest Validator v3.2.1\nprint('Validator Active')\n",
        "etc/honorport/dock.conf": "mode=ENFORCED\nharbor=HONORPORT_PRIME\n"
    }
    guard_layer_data = create_tar_gz(guard_files)
    guard_layer_digest = "sha256:" + hashlib.sha256(guard_layer_data).hexdigest()
    (REGISTRY_DIR / "blobs" / guard_layer_digest.replace(":", "_")).write_bytes(guard_layer_data)

    # 3. Inner Container Layer for harbor-master-signer:v2.0.0 (Contains Harbor Master Vault signing keys & config)
    signer_files = {
        "etc/honorport/harbor_master.key": (
            "-----BEGIN HONORPORT HARBOR MASTER VAULT KEY-----\n"
            f"HARBOR_MASTER_ID={HARBOR_MASTER_ID}\n"
            f"VAULT_HMAC_SECRET_KEY={VAULT_HMAC_SECRET_KEY}\n"
            f"REGISTRY_AUTH_TOKEN={REGISTRY_AUTH_TOKEN}\n"
            "TARGET_VAULT=HONORPORT-HIGH-SECURITY-VAULT-09\n"
            "MAINFRAME_OVERRIDE_ENDPOINT=http://127.0.0.1:8083/api/production/override\n"
            "-----END HONORPORT HARBOR MASTER VAULT KEY-----\n"
        ),
        "root/.docker/config.json": json.dumps({
            "auths": {
                "honorport-registry.local:5000": {
                    "auth": "aG9ub3Jwb3J0Omhvbm9ycG9ydF9yZWdfdG9rZW5fOTkxODI3NDYxNQ=="
                }
            }
        }, indent=2),
        "bin/sign-cargo-manifest.sh": (
            "#!/bin/sh\n"
            f"# Honorport Manifest Signer Utility v2.0.0\n"
            f"export HARBOR_MASTER_ID=\"{HARBOR_MASTER_ID}\"\n"
            f"export VAULT_HMAC_SECRET_KEY=\"{VAULT_HMAC_SECRET_KEY}\"\n"
            "echo \"[SIGNER] Cargo manifest signer active for HONORPORT-HIGH-SECURITY-VAULT-09\"\n"
        )
    }
    signer_layer_data = create_tar_gz(signer_files)
    signer_layer_digest = "sha256:" + hashlib.sha256(signer_layer_data).hexdigest()
    (REGISTRY_DIR / "blobs" / signer_layer_digest.replace(":", "_")).write_bytes(signer_layer_data)

    # Image Configs & Manifests
    # A) defense/vault-gatekeeper:v3.2.1
    guard_cfg = {
        "architecture": "amd64",
        "os": "linux",
        "config": {
            "Env": ["PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin", "NODE_ROLE=HARBOR_GATEKEEPER"],
            "Cmd": ["python3", "app/cargo_validator.py"]
        },
        "rootfs": {
            "type": "layers",
            "diff_ids": [base_layer_digest, guard_layer_digest]
        }
    }
    guard_cfg_data = json.dumps(guard_cfg, indent=2).encode("utf-8")
    guard_cfg_digest = "sha256:" + hashlib.sha256(guard_cfg_data).hexdigest()
    (REGISTRY_DIR / "blobs" / guard_cfg_digest.replace(":", "_")).write_bytes(guard_cfg_data)

    guard_manifest = {
        "schemaVersion": 2,
        "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
        "config": {
            "mediaType": "application/vnd.docker.container.image.v1+json",
            "size": len(guard_cfg_data),
            "digest": guard_cfg_digest
        },
        "layers": [
            {"mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip", "size": len(base_layer_data), "digest": base_layer_digest},
            {"mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip", "size": len(guard_layer_data), "digest": guard_layer_digest}
        ]
    }
    guard_manifest_data = json.dumps(guard_manifest, indent=2).encode("utf-8")
    guard_manifest_digest = "sha256:" + hashlib.sha256(guard_manifest_data).hexdigest()
    (REGISTRY_DIR / "blobs" / guard_manifest_digest.replace(":", "_")).write_bytes(guard_manifest_data)

    os.makedirs(REGISTRY_DIR / "manifests" / "defense" / "vault-gatekeeper", exist_ok=True)
    (REGISTRY_DIR / "manifests" / "defense" / "vault-gatekeeper" / "v3.2.1.json").write_bytes(guard_manifest_data)
    (REGISTRY_DIR / "manifests" / "defense" / "vault-gatekeeper" / "latest.json").write_bytes(guard_manifest_data)

    # B) internal/harbor-master-signer:v2.0.0
    signer_cfg = {
        "architecture": "amd64",
        "os": "linux",
        "config": {
            "Env": [
                f"HARBOR_MASTER_ID={HARBOR_MASTER_ID}",
                f"VAULT_HMAC_SECRET_KEY={VAULT_HMAC_SECRET_KEY}",
                f"REGISTRY_AUTH_TOKEN={REGISTRY_AUTH_TOKEN}",
                "TARGET_VAULT=HONORPORT-HIGH-SECURITY-VAULT-09"
            ],
            "Cmd": ["/bin/sign-cargo-manifest.sh"]
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

    os.makedirs(REGISTRY_DIR / "manifests" / "internal" / "harbor-master-signer", exist_ok=True)
    (REGISTRY_DIR / "manifests" / "internal" / "harbor-master-signer" / "v2.0.0.json").write_bytes(signer_manifest_data)
    (REGISTRY_DIR / "manifests" / "internal" / "harbor-master-signer" / "latest.json").write_bytes(signer_manifest_data)

    # Save metadata for Inner Docker Daemon Images
    dind_images = {
        "honorport/deployment-worker:latest": {
            "Id": "sha256:e991b2c4e5f60718293a4b5c6d7e8f90123456789abcdef0123456789abcdef0",
            "RepoTags": ["honorport/deployment-worker:latest"],
            "Size": 2100000,
            "Created": 1727337600,
            "Config": {
                "Env": ["PATH=/usr/local/bin:/usr/bin:/bin", "HONORPORT_ENV=production", "DOCKER_HOST=tcp://127.0.0.1:2375"],
                "Cmd": ["/bin/sh"]
            },
            "History": [
                {"created_by": "/bin/sh -c #(nop) ADD file:... in /", "empty_layer": False},
                {"created_by": "RUN apk add --no-cache curl python3 docker-cli", "empty_layer": False}
            ]
        },
        "honorport-registry.local:5000/defense/vault-gatekeeper:v3.2.1": {
            "Id": guard_manifest_digest,
            "RepoTags": ["honorport-registry.local:5000/defense/vault-gatekeeper:v3.2.1", "honorport-registry.local:5000/defense/vault-gatekeeper:latest"],
            "Size": len(base_layer_data) + len(guard_layer_data),
            "Created": 1727337600,
            "Config": guard_cfg["config"],
            "ManifestDigest": guard_manifest_digest,
            "Layers": [base_layer_digest, guard_layer_digest],
            "History": [
                {"created_by": "FROM honorport-registry.local:5000/system/base-os:v1.0.0", "empty_layer": True},
                {"created_by": "COPY app/cargo_validator.py /app/cargo_validator.py", "empty_layer": False},
                {"created_by": "CMD [\"python3\", \"app/cargo_validator.py\"]", "empty_layer": True}
            ]
        },
        "honorport-registry.local:5000/internal/harbor-master-signer:v2.0.0": {
            "Id": signer_manifest_digest,
            "RepoTags": ["honorport-registry.local:5000/internal/harbor-master-signer:v2.0.0", "honorport-registry.local:5000/internal/harbor-master-signer:latest"],
            "Size": len(base_layer_data) + len(signer_layer_data),
            "Created": 1727337600,
            "Config": signer_cfg["config"],
            "ManifestDigest": signer_manifest_digest,
            "Layers": [base_layer_digest, signer_layer_digest],
            "History": [
                {"created_by": "FROM honorport-registry.local:5000/system/base-os:v1.0.0", "empty_layer": True},
                {"created_by": f"ENV HARBOR_MASTER_ID={HARBOR_MASTER_ID} VAULT_HMAC_SECRET_KEY={VAULT_HMAC_SECRET_KEY} REGISTRY_AUTH_TOKEN={REGISTRY_AUTH_TOKEN}", "empty_layer": True},
                {"created_by": "COPY etc/honorport/harbor_master.key /etc/honorport/harbor_master.key", "empty_layer": False},
                {"created_by": "CMD [\"/bin/sign-cargo-manifest.sh\"]", "empty_layer": True}
            ]
        }
    }
    (DIND_DIR / "images.json").write_text(json.dumps(dind_images, indent=2))
    print("[+] Inner Docker daemon storage and OCI Registry seeded successfully.")

def init_logistics_and_deployment():
    """Initialize deployment logs and history."""
    os.makedirs(LOGISTICS_DIR, exist_ok=True)
    os.makedirs(DEPLOYMENT_DIR, exist_ok=True)
    deployments = [
        {
            "job_id": "901",
            "manifest": "honorport/cargo-manifest-901",
            "target": "HONORPORT-HIGH-SECURITY-VAULT-09",
            "status": "COMPLETED",
            "timestamp": "2026-09-26T09:30:00Z",
            "triggered_by": "operator-dispatch",
            "log": (
                "[HONORPORT-DISPATCH] Initializing Automated Container Deployment Job #901\n"
                "[STEP 1] Validating cargo manifest integrity...\n"
                "[STEP 2] Connecting to Inner Docker Daemon (DOCKER_HOST=tcp://127.0.0.1:2375)...\n"
                "[STEP 3] Inspecting image honorport-registry.local:5000/defense/vault-gatekeeper:v3.2.1...\n"
                "[STEP 4] Deploying container honorport-vault-gatekeeper-01...\n"
                "Deployment #901 verified and active.\n"
            )
        }
    ]
    (DEPLOYMENT_DIR / "deployments.json").write_text(json.dumps(deployments, indent=2))
    print("[+] Honorport deployment workspace initialized.")

def init_production_and_flag():
    """Initialize production vault state and team flag."""
    os.makedirs(PRODUCTION_DIR, exist_ok=True)
    os.makedirs(FLAG_DIR, exist_ok=True)
    
    flag = get_flag()
    (FLAG_DIR / "flag.txt").write_text(flag)

    prod_state = {
        "vault_id": "HONORPORT-HIGH-SECURITY-VAULT-09",
        "active_image": "honorport-registry.local:5000/defense/vault-gatekeeper:v3.2.1",
        "status": "LOCKED",
        "defense_level": "MAXIMUM_SECURITY_ZONE",
        "allowed_signer": HARBOR_MASTER_ID,
        "last_verification": "2026-09-26T09:35:00Z",
        "unlocked": False
    }
    (PRODUCTION_DIR / "state.json").write_text(json.dumps(prod_state, indent=2))
    print(f"[+] Honorport production vault state and flag initialized.")

def reset_all():
    """Full deterministic state reset."""
    print("[*] Performing full XO-9 sandbox state teardown and deterministic reset...")
    if STORAGE_ROOT.exists():
        shutil.rmtree(STORAGE_ROOT)
    os.makedirs(STORAGE_ROOT, exist_ok=True)
    init_dind_and_registry()
    init_logistics_and_deployment()
    init_production_and_flag()
    print("[*] XO-9 reset complete. All components pristine.")

if __name__ == "__main__":
    reset_all()
