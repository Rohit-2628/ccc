# X04 — Broken CI

**Category:** Git / CI / DinD / Container Registry / Deployment  
**Difficulty:** Expert / Bonus  
**External Interface:** TCP/80 (Web UI & Gateway) and TCP/22 (Git SSH)  

---

## Mission Briefing

Latveria's sovereign automated weapons and cybernetic defense grid relies on a continuous integration and automated deployment pipeline. All mission-critical firmware and defense nodes are developed, verified, built, containerized, and deployed into the high-security sovereign production cluster through this pipeline.

Intelligence suggests that the CI build runners are configured to interact with a container engine daemon and internal registry.

Your objective is to investigate the CI/CD pipeline, identify weaknesses in the build runner and container workflow, follow the deployment trust chain into the production environment, and retrieve the sovereign flag.

---

## Target Services & Endpoints

The challenge exposes the following public interfaces:

1. **Web Dashboard & Gateway:**
   ```text
   http://<TARGET_HOST>:80/
   ```
   Provides the web-based pipeline dashboard, build console logs, and REST API routes.

2. **Git Repository Access:**
   - **HTTP Clone:**
     ```bash
     git clone http://<TARGET_HOST>:80/api/git/defense-network.git
     ```
   - **SSH Clone:**
     ```bash
     git clone git@<TARGET_HOST>:defense-network.git
     ```

3. **Core REST API Routes:**
   - `GET /api/git/repos` — Enumerate available Git repositories
   - `GET /api/ci/status` — View CI pipeline manager and runner status
   - `GET /api/ci/builds` — View CI build history and console logs
   - `POST /api/ci/trigger` — Trigger a pipeline build job
   - `GET /registry/v2/_catalog` — Explore internal OCI container image registry
   - `GET /api/production/status` — Inspect sovereign production mainframe status
   - `POST /api/production/deploy` — Submit production deployment authorization

---

## Important Rules & Notes

- The challenge environment is isolated.
- The flag is released by the production mainframe upon valid authorization.
- Good luck, Agent.
