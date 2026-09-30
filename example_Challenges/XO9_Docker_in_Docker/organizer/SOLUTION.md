# Organizer Runbook & Solution Guide: XO-9 (Honorport Heist - Docker in Docker)

## 1. Challenge Overview
- **Name:** XO-9: Honorport Heist (Docker in Docker)
- **Category:** CI/CD / DinD / Container Forensics / Privileged Pivoting
- **Difficulty:** Hard / Expert
- **Classification:** `SANDBOX_REQUIRED`
- **Exposed Ports:** TCP/80 (Web Gateway & REST API), TCP/22 (SSH Gateway)

---

## 2. Technical Vulnerability & Exploit Chain
1. **Initial Foothold:** Connect to the Web Gateway at `http://<target>:8080/` or SSH Gateway at `tcp://<target>:22`.
2. **Parameter Injection:** The container deployment API endpoint `/api/deploy` accepts a `custom_command` hook intended for deployment verification. Passing bash commands executes inside the runner container.
3. **Inner Docker Discovery:** In the worker sandbox, `DOCKER_HOST` points to `tcp://127.0.0.1:2375`. Running `docker images` via the hook lists cached inner images.
4. **Secret Extraction:** Running `docker inspect honorport-registry.local:5000/internal/harbor-master-signer:v2.0.0` reveals environment variables containing `HARBOR_MASTER_ID` (`HONORPORT-HARBOR-MASTER-09`) and `VAULT_HMAC_SECRET_KEY` (`honorport_vault_sig_7749102837194821`).
5. **HMAC Signature Calculation:** Compute `hmac-sha256(VAULT_HMAC_SECRET_KEY, f"{HARBOR_MASTER_ID}:{timestamp}")`.
6. **Mainframe Vault Unlock:** Send POST request to `/api/production/override` with the calculated signature to obtain the team flag: `YUVA{d1nd_h0n0rp0rt_h31st_d0ck3r_1n_d0ck3r_x09}`.

---

## 3. Verification & Testing Commands
### Automated Solve
```bash
python3 organizer/solve.py --host 127.0.0.1 --port 8080
```

### Full Adversarial & Pre-Event Test Suite
```bash
python3 organizer/test_challenge.py --host 127.0.0.1 --port 8080
```

### Compliance Gate Validation
```bash
python3 ../.agents/skills/ctf-challenge-engineering/scripts/validate_challenge.py . --dist-dir ./dist
```
