# X04 — Broken CI

**Category:** Git / CI / DinD / Container Registry / Deployment  
**Difficulty:** Expert / Bonus  
**External Interface:** TCP/80 (Web UI & REST Gateway) and TCP/22 (Git SSH)  
**Classification:** SANDBOX_REQUIRED  

---

## 1. Challenge Architecture & Intended Progression

X04 simulates a multi-tier software delivery pipeline and Docker-in-Docker (DinD) trust chain within Doctor Doom's sovereign autonomous infrastructure.

```text
Player
   │
   │ TCP/80 (Web UI & REST API) / TCP/22 (Git SSH)
   ▼
Git / Gateway
   │
   ▼
CI Runner (Worker Sandbox)
   │
   ▼ (DOCKER_HOST / Inner DinD Daemon)
Inner Docker Daemon (tcp://127.0.0.1:2375)
   │
   ▼
Challenge-Local OCI Registry (127.0.0.1:5000 / /registry/v2)
   │
   ▼
Production Mock Mainframe (127.0.0.1:8083 / /api/production)
   │
   ▼
Flag: YUVA{d1nd_c1_runn3r_r3g1stry_pr0d_p1v0t_x04}
```

---

## 2. Directory Layout

```text
X04/
├── challenge/
│   ├── gateway/
│   │   ├── app.py                    # Unified Reverse Proxy & Web UI (Port 80)
│   │   ├── templates/
│   │   │   └── index.html            # Latverian CI/CD Console Web UI
│   │   └── static/
│   │       ├── css/style.css         # UI Styling
│   │       └── js/app.js             # Frontend AJAX and tab controllers
│   ├── git_server/
│   │   ├── git_http.py               # Smart Git HTTP protocol & repository viewer (Port 8081)
│   │   └── ssh_server.py             # Git SSH Server (Port 22)
│   ├── ci/
│   │   ├── ci_server.py              # CI Orchestrator & Runner API (Port 8082)
│   │   └── runner.py                 # Sandboxed Runner with DinD environment
│   ├── inner_docker/
│   │   ├── docker_daemon.py          # Challenge-Local Inner Docker Engine API (Port 2375)
│   │   └── docker_cli.py             # Docker CLI binary tool wrapper
│   ├── registry/
│   │   └── registry_server.py        # OCI / Docker Registry v2 Server (Port 5000)
│   ├── production/
│   │   └── prod_server.py            # Sovereign Production Mainframe Mock (Port 8083)
│   ├── deployment/
│   │   ├── deployment.yaml           # Kubernetes Deployment (Restricted Pod Security)
│   │   ├── service.yaml              # Kubernetes ClusterIP Service (Port 80 & 22)
│   │   ├── networkpolicy.yaml        # Default-Deny Ingress/Egress NetworkPolicy
│   │   ├── resourcequota.yaml        # ResourceQuota & LimitRange (4 vCPU / 4 GiB RAM)
│   │   └── sandbox-vm-spec.yaml      # Disposable VM Sandbox specification
│   └── snapshot/
│       └── seed_state.py             # Reproducible seed snapshot & reset engine
├── dist/                             # Participant distribution package (hygienic, leak-free)
│   └── README.md                     # Participant instructions & briefing
├── organizer/                        # Organizer-only testing & solution assets
│   ├── SOLUTION.md                   # 19-point organizer runbook & solution guide
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
Access the Web Gateway:
```bash
http://127.0.0.1:8080/
```

### Automated Solve & Verification
```bash
python3 organizer/solve.py --host 127.0.0.1 --port 8080
```

### Full Adversarial & Pre-Event Test Suite
```bash
python3 organizer/test_challenge.py --host 127.0.0.1 --port 8080
```

### Safety & Engineering Compliance Validation
```bash
python3 ../.agents/skills/ctf-challenge-engineering/scripts/validate_challenge.py . --dist-dir ./dist
```
