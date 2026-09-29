# X03 — Dooms Supply Chain

**Category:** Supply Chain / Package Registry / CI/CD  
**Difficulty:** Expert / Bonus  
**External Interface:** TCP/80 (Web UI & REST API Gateway)  
**Classification:** STANDARD  

---

## 1. Challenge Summary

X03 simulates an end-to-end software supply-chain compromise against Doctor Victor von Doom's sovereign cyber-manufacturing and autonomous weapons systems. The participant discovers an internal package registry, analyzes package version history and commit provenance, identifies an affected package artifact containing an emergency maintainer override backdoor, traces the dependency resolution through the automated CI build pipeline and OCI container image layers, and pivots into the deployed production mainframe to unlock the core and recover the team flag.

```text
Player
   │
   │ TCP/80 (Web UI / REST API Gateway)
   ▼
Developer App (Portal & Supply Chain Topology)
   │
   ▼
Package Repository (127.0.0.1:4873 / /api/packages)
   │
   ▼
CI Pipeline (127.0.0.1:8082 / /api/ci)
   │
   ▼
Image / OCI Registry (127.0.0.1:5000 / /registry/v2)
   │
   ▼
Production Deployment Target (127.0.0.1:8083 / /api/deployment)
   │
   ▼
Flag: YUVA{supp1y_ch41n_p01s0n1ng_t0_pr0d_d3p10ym3nt_x03}
```

---

## 2. Directory Structure

```text
X03/
├── challenge/
│   ├── developer_app/
│   │   ├── app.py                    # Public Developer App & Unified Gateway (TCP/80)
│   │   ├── templates/
│   │   │   └── index.html            # Dark-theme cyber-manufacturing control dashboard
│   │   └── static/
│   │       ├── css/style.css         # Styling
│   │       └── js/app.js             # Client AJAX & tab controllers
│   ├── package_repository/
│   │   └── repo_server.py            # Synthetic package index server (127.0.0.1:4873)
│   ├── ci/
│   │   └── ci_server.py              # Synthetic CI build orchestrator (127.0.0.1:8082)
│   ├── registry/
│   │   └── registry_server.py        # OCI v2 container image registry (127.0.0.1:5000)
│   ├── deployment/
│   │   ├── prod_server.py            # Production defense mainframe runtime (127.0.0.1:8083)
│   │   ├── deployment.yaml           # Kubernetes Deployment (Restricted Pod Security)
│   │   ├── service.yaml              # Kubernetes ClusterIP Service (Port 80)
│   │   ├── networkpolicy.yaml        # Kubernetes NetworkPolicy (Default Deny Ingress/Egress)
│   │   └── resourcequota.yaml        # Kubernetes ResourceQuota and LimitRange
│   └── snapshot/
│       └── seed_state.py             # Reproducible seed snapshot & environment reset utility
├── dist/                             # Participant distribution package (hygienic, leak-free)
│   └── README.md                     # Participant instructions & mission briefing
├── organizer/                        # Organizer-only material (outside participant package)
│   ├── SOLUTION.md                   # Full 19-point organizer runbook & solution guide
│   ├── solve.py                      # Automated clean-room solve script
│   └── test_challenge.py             # 10-step adversarial validation & test suite
├── Dockerfile                        # Multi-service container image definition
├── docker-compose.yml                # Local testing & platform compose deployment
├── entrypoint.sh                     # Container supervisor & service launcher
└── README.md                         # Top-level challenge documentation
```

---

## 3. Quickstart & Deployment

### Local Docker Compose
```bash
docker compose up -d --build
```
Access the Developer Console via web browser:
```bash
http://127.0.0.1:8093/
```

### Automated Solve & Verification
```bash
python3 organizer/solve.py --host 127.0.0.1 --port 8093
```

### Full Adversarial & Compliance Test Suite
```bash
python3 organizer/test_challenge.py --host 127.0.0.1 --port 8093
```

### Compliance Gate Validation
```bash
python3 ../.agents/skills/ctf-challenge-engineering/scripts/validate_challenge.py . --dist-dir ./dist
```
