# Challenge X02: Microservice Trust

## Overview
- **Challenge ID:** X02
- **Name:** Microservice Trust
- **Category:** Service Identity / Authorization / Microservices
- **Difficulty:** Expert / Bonus
- **External Port:** TCP/80 (Web Control Console & REST API)
- **Flag Format:** `YUVA{m1cr0s3rv1c3_1d3nt1ty_ch41n_br0k3n_x02}`

---

## Architecture

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
                   ▼
┌────────────────────────────────────────┐
│  Service A: Edge Telemetry Agent       │
│  Internal: 127.0.0.1:8081              │
│  Trust Level: LOW TRUST                │
└──────────────────┬─────────────────────┘
                   │
                   ▼ (X-Citadel-Identity-Cert)
┌────────────────────────────────────────┐
│  Service B: Core Controller            │
│  Internal: 127.0.0.1:8082              │
│  Trust Level: HIGH PRIVILEGE           │
└──────────────────┬─────────────────────┘
                   │
                   ▼ (LATV-ADMIN-TICKET-*)
┌────────────────────────────────────────┐
│  Admin Service: Citadel Vault          │
│  Internal: 127.0.0.1:8083              │
│  Trust Level: SOVEREIGN ROOT           │
└────────────────────────────────────────┘
```

---

## Directory Structure
```
X02/
├── Dockerfile                  # Container build instructions
├── README.md                   # Challenge developer & operator documentation
├── docker-compose.yml          # Local test composition
├── entrypoint.sh               # Multi-process supervisor and initialization
├── challenge/
│   ├── common/                 # PKI crypto utilities and certificate verification
│   ├── gateway/                # Public Ingress Gateway (TCP/80) & Web Dashboard
│   ├── service_a/              # Low-Trust Telemetry Agent (127.0.0.1:8081)
│   ├── service_b/              # High-Privilege Core Controller (127.0.0.1:8082)
│   ├── admin/                  # Sovereign Vault Service (127.0.0.1:8083)
│   └── deployment/             # Kubernetes manifests (Deployment, Service, NetworkPolicy, Quota)
├── dist/                       # Clean participant distribution package
│   ├── README.md
│   └── mesh_client_sample.py
└── organizer/                  # Organizer solution and verification suite
    ├── SOLUTION.md
    ├── solve.py
    └── test_challenge.py
```

---

## Running Locally

### With Docker Compose
```bash
cd X02
docker compose up --build
```

### Direct Python Execution
```bash
# In separate terminals or background:
export PKI_DIR=/tmp/citadel_mesh_pki
python3 challenge/service_a/app.py &
python3 challenge/service_b/app.py &
python3 challenge/admin/app.py &
PORT=8080 python3 challenge/gateway/app.py
```

---

## Testing & Verification
```bash
# Run automated solver
python3 organizer/solve.py --host 127.0.0.1 --port 8080

# Run complete pre-event test suite (Tests 1-5)
python3 organizer/test_challenge.py --host 127.0.0.1 --port 8080
```
