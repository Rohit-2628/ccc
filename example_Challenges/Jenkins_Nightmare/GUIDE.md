# X01 — Jenkins Nightmare

**Category:** CI/CD / Pipeline Compromise / Build Runner Security  
**Difficulty:** Expert / Bonus  
**External Interface:** TCP/80 (Web)  
**Classification:** SANDBOX_REQUIRED  

---

## 1. Challenge Summary

X01 simulates an intrusion scenario against an automated sovereign CI/CD deployment pipeline ("Jenkins Nightmare") utilized by Doctor Doom's engineering corps. The participant connects to the CI web dashboard on TCP/80, enumerates mock Git repositories and pipeline specifications, discovers parameter injection capabilities in test execution hooks (`CUSTOM_TEST_HOOK`), captures sensitive runner environment variables (including local OCI registry credentials), enumerates private image manifests and layer diffs to recover production master HMAC secrets, and submits an authorized production override request to capture the flag.

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

## 2. Directory Structure

```text
X01/
├── challenge/
│   ├── mock_git/
│   │   └── git_server.py             # Mock Git engine, commit logs & file browser
│   ├── ci/
│   │   ├── app.py                    # Main CI Web Gateway & API (TCP/80)
│   │   ├── templates/
│   │   │   └── index.html            # Dark-theme CI web console dashboard
│   │   └── static/
│   │       ├── css/style.css         # Styling
│   │       └── js/app.js             # Client AJAX & polling logic
│   ├── build_runtime/
│   │   └── runner.py                 # Isolated build runner (90s timeout, resource limits)
│   ├── registry/
│   │   └── registry_server.py        # OCI v2 container registry with seeded layers
│   ├── production/
│   │   └── prod_server.py            # Isolated production mock mainframe (HMAC-SHA256 verified)
│   └── deployment/
│       ├── deployment.yaml           # Kubernetes Deployment (Restricted Pod Security)
│       ├── service.yaml              # Kubernetes ClusterIP Service (Port 80)
│       ├── networkpolicy.yaml        # Kubernetes NetworkPolicy (Default Deny Ingress/Egress)
│       └── resourcequota.yaml        # Kubernetes ResourceQuota and LimitRange
├── dist/                             # Participant distribution package (hygienic, leak-free)
│   └── README.md                     # Participant instructions & mission briefing
├── organizer/                        # Organizer-only material (outside participant package)
│   ├── SOLUTION.md                   # Full 16-point organizer runbook & solution guide
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
Access the CI Console via web browser:
```bash
http://127.0.0.1:8080/
```

### Automated Solve & Verification
```bash
python3 organizer/solve.py --host 127.0.0.1 --port 8080
```

### Full Adversarial & Compliance Test Suite
```bash
python3 organizer/test_challenge.py --host 127.0.0.1 --port 8080
```

### Compliance Gate Validation
```bash
python3 ../.agents/skills/ctf-challenge-engineering/scripts/validate_challenge.py . --dist-dir ./dist
```
