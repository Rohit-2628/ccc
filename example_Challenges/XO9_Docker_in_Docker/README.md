# XO-9 — Honorport Heist (Docker in Docker)

**Category:** CI/CD / DinD / Container Forensics / Privileged Pivoting  
**Difficulty:** Hard / Expert  
**External Interface:** TCP/80 (Web UI & REST Gateway) and TCP/22 (SSH Gateway)  
**Classification:** SANDBOX_REQUIRED  

---

## 1. Challenge Summary

XO-9 simulates an intrusion scenario against Doctor Doom's sovereign autonomous harbor logistics depot ("Honorport"). The participant connects to the Web Console on TCP/8080 or SSH Gateway on TCP/22, triggers container deployment checks, leverages parameter injection to interact with an inner Docker-in-Docker (DinD) daemon (`DOCKER_HOST=tcp://127.0.0.1:2375`), inspects cached OCI registry images and build layer diffs to recover the Harbor Master vault secret, and submits a signed override request to capture the flag.

```text
Player
   │
   │ TCP/8080 (Web UI / REST API) / TCP/22 (SSH Gateway)
   ▼
Honorport Web Gateway
   │
   ▼
Logistics Controller API & Worker Sandbox
   │
   ▼ (DOCKER_HOST / Inner DinD Daemon)
Inner Docker Daemon (tcp://127.0.0.1:2375)
   │
   ▼
Challenge-Local OCI Registry (127.0.0.1:5000)
   │
   ▼
Honorport Production Mainframe Vault (127.0.0.1:8083)
   │
   ▼
Flag: YUVA{d1nd_h0n0rp0rt_h31st_d0ck3r_1n_d0ck3r_x09}
```

---

## 2. Directory Structure

```text
XO9_Docker_in_Docker/
├── challenge/
│   ├── gateway/
│   │   ├── app.py                    # Unified Reverse Proxy & Web UI (Port 8080)
│   │   ├── templates/
│   │   │   └── index.html            # Honorport Logistics Web Console UI
│   │   └── static/
│   │       ├── css/style.css         # UI Styling
│   │       └── js/app.js             # Client AJAX controllers
│   ├── honorport_api/
│   │   ├── honorport_server.py       # Honorport Logistics Controller (Port 8082)
│   │   └── ssh_server.py             # Honorport SSH Gateway (Port 22)
│   ├── inner_docker/
│   │   ├── docker_daemon.py          # Challenge-Local Inner Docker Engine API (Port 2375)
│   │   └── docker_cli.py             # Docker CLI binary tool wrapper
│   ├── registry/
│   │   └── registry_server.py        # OCI / Docker Registry v2 Server (Port 5000)
│   ├── production/
│   │   └── prod_server.py            # Honorport Mainframe Vault Mock (Port 8083)
│   ├── deployment/
│   │   ├── deployment.yaml           # Kubernetes Deployment (Restricted Pod Security)
│   │   ├── service.yaml              # Kubernetes ClusterIP Service (Ports 80 & 22)
│   │   ├── networkpolicy.yaml        # Default-Deny NetworkPolicy
│   │   └── resourcequota.yaml        # ResourceQuota & LimitRange
│   └── snapshot/
│       └── seed_state.py             # Reproducible seed snapshot & reset engine
├── dist/                             # Participant distribution package (hygienic, leak-free)
│   └── README.md                     # Participant instructions & briefing
├── organizer/                        # Organizer-only testing & solution assets
│   ├── SOLUTION.md                   # Organizer runbook & solution guide
│   ├── solve.py                      # Automated clean-room solve script
│   └── test_challenge.py             # 10-step adversarial validation test suite
├── Dockerfile                        # Multi-service container image definition
├── docker-compose.yml                # Local testing & platform compose deployment
├── entrypoint.sh                     # Container supervisor & service launcher
└── README.md                         # Challenge documentation
```

---

## 3. Quickstart & Deployment

### Local Docker Compose
```bash
docker compose up -d --build
```
Access the Web Gateway: `http://127.0.0.1:8099/`  
SSH Gateway: `ssh honorport@127.0.0.1 -p 2222`

### Automated Solve & Verification
```bash
python3 organizer/solve.py --host 127.0.0.1 --port 8099
```

### Full Adversarial & Pre-Event Test Suite
```bash
python3 organizer/test_challenge.py --host 127.0.0.1 --port 8099
```

### Safety & Engineering Compliance Validation
```bash
python3 ../.agents/skills/ctf-challenge-engineering/scripts/validate_challenge.py . --dist-dir ./dist
```
