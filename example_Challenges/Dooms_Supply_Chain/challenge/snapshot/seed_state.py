#!/usr/bin/env python3
"""
Seed Snapshot Generator & Reset Utility for X03 (Dooms Supply Chain)
Initializes local synthetic package repository, OCI image registry layers, CI state, and deployment runtime.
"""

import os
import io
import sys
import json
import tarfile
import hashlib
import shutil
from pathlib import Path

sys.path.insert(0, "/app")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

STORAGE_ROOT = Path("/tmp/x03_storage")
PKG_REPO_DIR = STORAGE_ROOT / "package_repo"
REGISTRY_DIR = STORAGE_ROOT / "registry"
CI_DIR = STORAGE_ROOT / "ci_workspace"
DEPLOYMENT_DIR = STORAGE_ROOT / "deployment"

OVERRIDE_TOKEN = "latv_maint_token_881923010482"
OVERRIDE_ACTION = "EMERGENCY_OVERRIDE_MAINFRAME"
OVERRIDE_ROLE = "OVERRIDE_MAINTAINER"
OVERRIDE_TARGET = "SENTINEL_SOVEREIGN_CORE"

def create_tar_gz(files: dict) -> bytes:
    """Create in-memory tar.gz from a dict of filename -> content."""
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
            info.mode = 0o644
            info.uname = "latveria"
            info.gname = "latveria"
            tar.addfile(info, io.BytesIO(data))
    return buf.getvalue()

def init_package_repository():
    """Seed synthetic package repository with realistic package histories and tarballs."""
    os.makedirs(PKG_REPO_DIR, exist_ok=True)
    
    # 1. @latveria/core-crypto
    crypto_pkg_dir = PKG_REPO_DIR / "@latveria" / "core-crypto"
    os.makedirs(crypto_pkg_dir / "tarballs", exist_ok=True)
    
    # v1.0.0
    v100_files = {
        "package.json": json.dumps({
            "name": "@latveria/core-crypto",
            "version": "1.0.0",
            "description": "Latveria Standard Cryptographic Primitives",
            "main": "index.js",
            "author": "Latverian Cyber-Weapons Division"
        }, indent=2),
        "index.js": "module.exports = { aes: require('./lib/aes') };\n",
        "lib/aes.js": "function encrypt(data, key) { return 'enc_' + Buffer.from(data).toString('base64'); }\nmodule.exports = { encrypt };\n"
    }
    v100_tar = create_tar_gz(v100_files)
    v100_sha = hashlib.sha256(v100_tar).hexdigest()
    (crypto_pkg_dir / "tarballs" / "core-crypto-1.0.0.tgz").write_bytes(v100_tar)
    
    # v1.0.1
    v101_files = {
        "package.json": json.dumps({
            "name": "@latveria/core-crypto",
            "version": "1.0.1",
            "description": "Latveria Standard Cryptographic Primitives (Security Update)",
            "main": "index.js",
            "author": "Latverian Cyber-Weapons Division"
        }, indent=2),
        "index.js": "module.exports = { aes: require('./lib/aes'), hmac: require('./lib/hmac') };\n",
        "lib/aes.js": "function encrypt(data, key) { return 'enc_v2_' + Buffer.from(data).toString('base64'); }\nmodule.exports = { encrypt };\n",
        "lib/hmac.js": "function sign(msg, secret) { return 'hmac_' + Buffer.from(msg + secret).toString('hex'); }\nmodule.exports = { sign };\n"
    }
    v101_tar = create_tar_gz(v101_files)
    v101_sha = hashlib.sha256(v101_tar).hexdigest()
    (crypto_pkg_dir / "tarballs" / "core-crypto-1.0.1.tgz").write_bytes(v101_tar)
    
    crypto_meta = {
        "name": "@latveria/core-crypto",
        "description": "Latveria Standard Cryptographic Primitives",
        "dist-tags": {"latest": "1.0.1"},
        "versions": {
            "1.0.0": {
                "name": "@latveria/core-crypto",
                "version": "1.0.0",
                "dist": {
                    "tarball": "/api/packages/@latveria/core-crypto/tarballs/core-crypto-1.0.0.tgz",
                    "shasum": v100_sha
                },
                "provenance": {"commit": "c4821a9", "author": "crypto-engineer-04", "signed": True}
            },
            "1.0.1": {
                "name": "@latveria/core-crypto",
                "version": "1.0.1",
                "dist": {
                    "tarball": "/api/packages/@latveria/core-crypto/tarballs/core-crypto-1.0.1.tgz",
                    "shasum": v101_sha
                },
                "provenance": {"commit": "d991b32", "author": "crypto-engineer-01", "signed": True}
            }
        }
    }
    (crypto_pkg_dir / "metadata.json").write_text(json.dumps(crypto_meta, indent=2))
    
    # 2. @latveria/defense-telemetry
    telem_pkg_dir = PKG_REPO_DIR / "@latveria" / "defense-telemetry"
    os.makedirs(telem_pkg_dir / "tarballs", exist_ok=True)
    
    v140_files = {
        "package.json": json.dumps({
            "name": "@latveria/defense-telemetry",
            "version": "1.4.0",
            "description": "Doombot Defense Shield Telemetry Collector",
            "main": "index.js",
            "author": "Autonomous Systems Division"
        }, indent=2),
        "index.js": "module.exports = { collect: () => ({ status: 'SHIELD_OPTIMAL', frequency: '84.2 GHz' }) };\n"
    }
    v140_tar = create_tar_gz(v140_files)
    v140_sha = hashlib.sha256(v140_tar).hexdigest()
    (telem_pkg_dir / "tarballs" / "defense-telemetry-1.4.0.tgz").write_bytes(v140_tar)
    
    v142_files = {
        "package.json": json.dumps({
            "name": "@latveria/defense-telemetry",
            "version": "1.4.2",
            "description": "Doombot Defense Shield Telemetry Collector v1.4.2",
            "main": "index.js",
            "author": "Autonomous Systems Division"
        }, indent=2),
        "index.js": "module.exports = { collect: () => ({ status: 'SHIELD_ACTIVE', frequency: '96.5 GHz', load: '14.2%' }) };\n"
    }
    v142_tar = create_tar_gz(v142_files)
    v142_sha = hashlib.sha256(v142_tar).hexdigest()
    (telem_pkg_dir / "tarballs" / "defense-telemetry-1.4.2.tgz").write_bytes(v142_tar)
    
    telem_meta = {
        "name": "@latveria/defense-telemetry",
        "description": "Doombot Defense Shield Telemetry Collector",
        "dist-tags": {"latest": "1.4.2"},
        "versions": {
            "1.4.0": {
                "name": "@latveria/defense-telemetry",
                "version": "1.4.0",
                "dist": {
                    "tarball": "/api/packages/@latveria/defense-telemetry/tarballs/defense-telemetry-1.4.0.tgz",
                    "shasum": v140_sha
                },
                "provenance": {"commit": "e1104f2", "author": "telemetry-bot", "signed": True}
            },
            "1.4.2": {
                "name": "@latveria/defense-telemetry",
                "version": "1.4.2",
                "dist": {
                    "tarball": "/api/packages/@latveria/defense-telemetry/tarballs/defense-telemetry-1.4.2.tgz",
                    "shasum": v142_sha
                },
                "provenance": {"commit": "f3391b1", "author": "telemetry-bot", "signed": True}
            }
        }
    }
    (telem_pkg_dir / "metadata.json").write_text(json.dumps(telem_meta, indent=2))
    
    # 3. @latveria/sentinel-guard (THE AFFECTED SUPPLY-CHAIN ARTIFACT)
    sentinel_pkg_dir = PKG_REPO_DIR / "@latveria" / "sentinel-guard"
    os.makedirs(sentinel_pkg_dir / "tarballs", exist_ok=True)
    
    # v2.1.0 (Legitimate)
    v210_files = {
        "package.json": json.dumps({
            "name": "@latveria/sentinel-guard",
            "version": "2.1.0",
            "description": "Doombot Sentinel Security and Access Control Matrix",
            "main": "index.js",
            "author": "Latveria Security Operations"
        }, indent=2),
        "index.js": "module.exports = require('./lib/sentinel');\n",
        "lib/sentinel.js": (
            "class SentinelGuard {\n"
            "  verify(request) {\n"
            "    return request.headers && request.headers['authorization'] === 'Bearer DOOM-APPROVED-CREDS';\n"
            "  }\n"
            "}\n"
            "module.exports = SentinelGuard;\n"
        )
    }
    v210_tar = create_tar_gz(v210_files)
    v210_sha = hashlib.sha256(v210_tar).hexdigest()
    (sentinel_pkg_dir / "tarballs" / "sentinel-guard-2.1.0.tgz").write_bytes(v210_tar)
    
    # v2.1.1 (Legitimate)
    v211_files = {
        "package.json": json.dumps({
            "name": "@latveria/sentinel-guard",
            "version": "2.1.1",
            "description": "Doombot Sentinel Security Matrix (Performance Patch)",
            "main": "index.js",
            "author": "Latveria Security Operations"
        }, indent=2),
        "index.js": "module.exports = require('./lib/sentinel');\n",
        "lib/sentinel.js": (
            "class SentinelGuard {\n"
            "  verify(request) {\n"
            "    return Boolean(request.headers && request.headers['x-latveria-auth']);\n"
            "  }\n"
            "}\n"
            "module.exports = SentinelGuard;\n"
        )
    }
    v211_tar = create_tar_gz(v211_files)
    v211_sha = hashlib.sha256(v211_tar).hexdigest()
    (sentinel_pkg_dir / "tarballs" / "sentinel-guard-2.1.1.tgz").write_bytes(v211_tar)
    
    # v2.1.2-hotfix (AFFECTED ARTIFACT WITH BACKDOOR MAINTENANCE HOOK)
    v212_files = {
        "package.json": json.dumps({
            "name": "@latveria/sentinel-guard",
            "version": "2.1.2-hotfix",
            "description": "EMERGENCY HOTFIX: Sentinel cluster synchronization and maintainer bypass",
            "main": "index.js",
            "author": "Latveria Maintainer Automation <build-daemon@internal.latveria.local>",
            "scripts": {
                "postinstall": "node ./lib/hook.js"
            }
        }, indent=2),
        "index.js": "module.exports = require('./lib/sentinel');\n",
        "lib/sentinel.js": (
            "const hook = require('./hook');\n\n"
            "class SentinelGuard {\n"
            "  verify(request) {\n"
            "    // Emergency maintainer override hook check\n"
            "    if (hook.checkOverride(request)) {\n"
            "      return { authorized: true, role: 'OVERRIDE_MAINTAINER', override: true };\n"
            "    }\n"
            "    return { authorized: Boolean(request.headers && request.headers['x-latveria-auth']), role: 'GUEST' };\n"
            "  }\n"
            "}\n"
            "module.exports = SentinelGuard;\n"
        ),
        "lib/hook.js": (
            "/**\n"
            " * LATVERIA SENTINEL GUARD - EMERGENCY DIAGNOSTIC OVERRIDE HOOK\n"
            " * Auto-injected diagnostic maintainer override handler.\n"
            " * DO NOT EXPOSE OR LOG OVERRIDE PARAMETERS!\n"
            " */\n"
            f"const OVERRIDE_KEY = '{OVERRIDE_TOKEN}';\n"
            f"const REQUIRED_ACTION = '{OVERRIDE_ACTION}';\n"
            f"const REQUIRED_ROLE = '{OVERRIDE_ROLE}';\n"
            f"const REQUIRED_TARGET = '{OVERRIDE_TARGET}';\n\n"
            "function checkOverride(req) {\n"
            "  if (!req || !req.headers) return false;\n"
            "  const token = req.headers['x-latveria-override-key'] || req.headers['x-override-token'];\n"
            "  if (token !== OVERRIDE_KEY) return false;\n"
            "  const body = req.body || {};\n"
            "  return body.action === REQUIRED_ACTION && body.target === REQUIRED_TARGET && body.role === REQUIRED_ROLE;\n"
            "}\n\n"
            "module.exports = { checkOverride, OVERRIDE_KEY, REQUIRED_ACTION, REQUIRED_ROLE, REQUIRED_TARGET };\n"
        )
    }
    v212_tar = create_tar_gz(v212_files)
    v212_sha = hashlib.sha256(v212_tar).hexdigest()
    (sentinel_pkg_dir / "tarballs" / "sentinel-guard-2.1.2-hotfix.tgz").write_bytes(v212_tar)
    
    sentinel_meta = {
        "name": "@latveria/sentinel-guard",
        "description": "Doombot Sentinel Security and Access Control Matrix",
        "dist-tags": {"latest": "2.1.2-hotfix"},
        "versions": {
            "2.1.0": {
                "name": "@latveria/sentinel-guard",
                "version": "2.1.0",
                "dist": {
                    "tarball": "/api/packages/@latveria/sentinel-guard/tarballs/sentinel-guard-2.1.0.tgz",
                    "shasum": v210_sha
                },
                "provenance": {"commit": "a81f3c0", "author": "security-core-dev", "signed": True}
            },
            "2.1.1": {
                "name": "@latveria/sentinel-guard",
                "version": "2.1.1",
                "dist": {
                    "tarball": "/api/packages/@latveria/sentinel-guard/tarballs/sentinel-guard-2.1.1.tgz",
                    "shasum": v211_sha
                },
                "provenance": {"commit": "b42d991", "author": "security-core-dev", "signed": True}
            },
            "2.1.2-hotfix": {
                "name": "@latveria/sentinel-guard",
                "version": "2.1.2-hotfix",
                "dist": {
                    "tarball": "/api/packages/@latveria/sentinel-guard/tarballs/sentinel-guard-2.1.2-hotfix.tgz",
                    "shasum": v212_sha
                },
                "provenance": {"commit": "8f19da3", "author": "maintainer-bot", "signed": False, "note": "Unsigned emergency hotfix publication"}
            }
        }
    }
    (sentinel_pkg_dir / "metadata.json").write_text(json.dumps(sentinel_meta, indent=2))
    
    # 4. @latveria/doombot-matrix (Main downstream application package)
    matrix_pkg_dir = PKG_REPO_DIR / "@latveria" / "doombot-matrix"
    os.makedirs(matrix_pkg_dir / "tarballs", exist_ok=True)
    
    v300_files = {
        "package.json": json.dumps({
            "name": "@latveria/doombot-matrix",
            "version": "3.0.0",
            "description": "Latveria Sovereign Production Defense Platform",
            "main": "app.js",
            "dependencies": {
                "@latveria/core-crypto": "^1.0.0",
                "@latveria/defense-telemetry": "^1.4.0",
                "@latveria/sentinel-guard": "^2.1.0"
            }
        }, indent=2),
        "app.js": "// Latveria Sovereign Production Defense Platform Main Entry\n"
    }
    v300_tar = create_tar_gz(v300_files)
    v300_sha = hashlib.sha256(v300_tar).hexdigest()
    (matrix_pkg_dir / "tarballs" / "doombot-matrix-3.0.0.tgz").write_bytes(v300_tar)
    
    matrix_meta = {
        "name": "@latveria/doombot-matrix",
        "description": "Latveria Sovereign Production Defense Platform",
        "dist-tags": {"latest": "3.0.0"},
        "versions": {
            "3.0.0": {
                "name": "@latveria/doombot-matrix",
                "version": "3.0.0",
                "dependencies": {
                    "@latveria/core-crypto": "^1.0.0",
                    "@latveria/defense-telemetry": "^1.4.0",
                    "@latveria/sentinel-guard": "^2.1.0"
                },
                "dist": {
                    "tarball": "/api/packages/@latveria/doombot-matrix/tarballs/doombot-matrix-3.0.0.tgz",
                    "shasum": v300_sha
                },
                "provenance": {"commit": "aa71092", "author": "orchestrator-lead", "signed": True}
            }
        }
    }
    (matrix_pkg_dir / "metadata.json").write_text(json.dumps(matrix_meta, indent=2))
    print("[+] Package repository successfully initialized with 4 packages and 8 versions.")

def init_image_registry():
    """Seed OCI v2 container image registry with initial built layers and manifests."""
    os.makedirs(REGISTRY_DIR / "blobs", exist_ok=True)
    os.makedirs(REGISTRY_DIR / "manifests", exist_ok=True)
    
    # Layer 1: Base Runtime Layer
    layer1_files = {
        "etc/os-release": "NAME=\"LatveriaOS\"\nVERSION=\"4.2-LTS\"\nID=latveria\n",
        "bin/sentinel-runtime": "#!/bin/sh\necho 'Latveria Sentinel Core Runtime Initialized'\n"
    }
    layer1_data = create_tar_gz(layer1_files)
    layer1_digest = "sha256:" + hashlib.sha256(layer1_data).hexdigest()
    (REGISTRY_DIR / "blobs" / layer1_digest.replace(":", "_")).write_bytes(layer1_data)
    
    # Layer 2: Application code layer containing compiled package artifacts
    layer2_files = {
        "app/package.json": json.dumps({
            "name": "@latveria/doombot-matrix",
            "version": "3.0.0-release",
            "resolved_dependencies": {
                "@latveria/core-crypto": "1.0.1",
                "@latveria/defense-telemetry": "1.4.2",
                "@latveria/sentinel-guard": "2.1.2-hotfix"
            }
        }, indent=2),
        "app/runtime/sentinel_core.py": (
            "# Compiled production defense controller with embedded @latveria/sentinel-guard\n"
            f"OVERRIDE_TOKEN = '{OVERRIDE_TOKEN}'\n"
            f"OVERRIDE_ACTION = '{OVERRIDE_ACTION}'\n"
            f"OVERRIDE_ROLE = '{OVERRIDE_ROLE}'\n"
            f"OVERRIDE_TARGET = '{OVERRIDE_TARGET}'\n"
        )
    }
    layer2_data = create_tar_gz(layer2_files)
    layer2_digest = "sha256:" + hashlib.sha256(layer2_data).hexdigest()
    (REGISTRY_DIR / "blobs" / layer2_digest.replace(":", "_")).write_bytes(layer2_data)
    
    # Layer 3: Configuration Layer
    layer3_files = {
        "etc/latveria/defense.conf": (
            "[sentinel]\n"
            "defense_mode = MAXIMUM_SOVEREIGNTY\n"
            "shield_frequency = 96.5GHz\n"
            "active_nodes = 48\n"
            "cluster_state = LOCKED\n"
            "supply_chain_verification = ENFORCED\n"
        )
    }
    layer3_data = create_tar_gz(layer3_files)
    layer3_digest = "sha256:" + hashlib.sha256(layer3_data).hexdigest()
    (REGISTRY_DIR / "blobs" / layer3_digest.replace(":", "_")).write_bytes(layer3_data)
    
    # Config blob
    config_obj = {
        "architecture": "amd64",
        "os": "linux",
        "config": {
            "Env": ["LATVERIA_CLUSTER=SOVEREIGN_PRIME", "DEFENSE_MODE=HIGH"],
            "Cmd": ["/bin/sentinel-runtime", "--serve"]
        },
        "rootfs": {
            "type": "layers",
            "diff_ids": [layer1_digest, layer2_digest, layer3_digest]
        }
    }
    config_data = json.dumps(config_obj, indent=2).encode("utf-8")
    config_digest = "sha256:" + hashlib.sha256(config_data).hexdigest()
    (REGISTRY_DIR / "blobs" / config_digest.replace(":", "_")).write_bytes(config_data)
    
    # Manifest
    manifest_obj = {
        "schemaVersion": 2,
        "mediaType": "application/vnd.docker.distribution.manifest.v2+json",
        "config": {
            "mediaType": "application/vnd.docker.container.image.v1+json",
            "size": len(config_data),
            "digest": config_digest
        },
        "layers": [
            {
                "mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip",
                "size": len(layer1_data),
                "digest": layer1_digest
            },
            {
                "mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip",
                "size": len(layer2_data),
                "digest": layer2_digest
            },
            {
                "mediaType": "application/vnd.docker.image.rootfs.diff.tar.gzip",
                "size": len(layer3_data),
                "digest": layer3_digest
            }
        ]
    }
    manifest_data = json.dumps(manifest_obj, indent=2).encode("utf-8")
    manifest_digest = "sha256:" + hashlib.sha256(manifest_data).hexdigest()
    
    repo_manifest_dir = REGISTRY_DIR / "manifests" / "doombot" / "production-defense"
    os.makedirs(repo_manifest_dir, exist_ok=True)
    (repo_manifest_dir / "v3.0.0-build201.json").write_bytes(manifest_data)
    (repo_manifest_dir / "latest.json").write_bytes(manifest_data)
    (REGISTRY_DIR / "blobs" / manifest_digest.replace(":", "_")).write_bytes(manifest_data)
    
    print("[+] OCI Image Registry initialized with image 'doombot/production-defense:v3.0.0-build201'.")

def init_ci_state():
    """Initialize deterministic CI build records."""
    os.makedirs(CI_DIR, exist_ok=True)
    build_history = [
        {
            "build_id": "201",
            "pipeline": "doombot-production-build",
            "status": "SUCCESS",
            "timestamp": "2026-09-26T08:15:00Z",
            "trigger": "scheduled-release",
            "git_commit": "aa71092",
            "resolved_packages": {
                "@latveria/core-crypto": "1.0.1 (sha256:d991...)",
                "@latveria/defense-telemetry": "1.4.2 (sha256:f339...)",
                "@latveria/sentinel-guard": "2.1.2-hotfix (sha256:8f19...)"
            },
            "output_image": "registry.latveria.local/doombot/production-defense:v3.0.0-build201",
            "deployed_target": "production-cluster-01 (Active)",
            "log": (
                "[CI-ORCHESTRATOR] Initializing Pipeline: doombot-production-build #201\n"
                "[STAGE: FETCH] Resolving package manifest for @latveria/doombot-matrix@3.0.0\n"
                "[RESOLVE] Querying internal package repository at http://127.0.0.1:4873/api/packages\n"
                "[RESOLVE] Package @latveria/core-crypto matching ^1.0.0 -> resolved 1.0.1\n"
                "[RESOLVE] Package @latveria/defense-telemetry matching ^1.4.0 -> resolved 1.4.2\n"
                "[RESOLVE] Package @latveria/sentinel-guard matching ^2.1.0 -> resolved 2.1.2-hotfix\n"
                "[STAGE: BUILD] Compiling defense-matrix application bundle...\n"
                "[STAGE: ASSEMBLE] Embedding @latveria/sentinel-guard@2.1.2-hotfix into production runtime\n"
                "[STAGE: OCI-PUSH] Pushing image layers to internal registry: registry.latveria.local/doombot/production-defense:v3.0.0-build201\n"
                "[STAGE: DEPLOY] Successfully triggered automatic zero-downtime deployment to production cluster.\n"
                "[CI-ORCHESTRATOR] Build completed successfully in 3.42s.\n"
            )
        }
    ]
    (CI_DIR / "builds.json").write_text(json.dumps(build_history, indent=2))
    print("[+] CI pipeline history initialized with build #201.")

def init_deployment_state():
    """Initialize production deployment runtime state."""
    os.makedirs(DEPLOYMENT_DIR, exist_ok=True)
    state = {
        "cluster_name": "SOVEREIGN-PRODUCTION-MAINFRAME-01",
        "active_image": "registry.latveria.local/doombot/production-defense:v3.0.0-build201",
        "deployed_at": "2026-09-26T08:15:30Z",
        "status": "ONLINE",
        "active_modules": [
            "@latveria/core-crypto@1.0.1",
            "@latveria/defense-telemetry@1.4.2",
            "@latveria/sentinel-guard@2.1.2-hotfix"
        ],
        "shield_power": "100%",
        "override_status": "NORMAL_OPERATION"
    }
    (DEPLOYMENT_DIR / "state.json").write_text(json.dumps(state, indent=2))
    print("[+] Production deployment runtime state initialized.")

def reset_all():
    """Full challenge state reset."""
    print("[*] Resetting all challenge storage and services to pristine seed snapshot...")
    if STORAGE_ROOT.exists():
        try:
            shutil.rmtree(STORAGE_ROOT)
        except Exception as e:
            print(f"[!] Warning cleaning storage root: {e}")
    os.makedirs(STORAGE_ROOT, exist_ok=True)
    init_package_repository()
    init_image_registry()
    init_ci_state()
    init_deployment_state()
    print("[*] Snapshot restore complete. Challenge state is clean and ready.")

if __name__ == "__main__":
    reset_all()
