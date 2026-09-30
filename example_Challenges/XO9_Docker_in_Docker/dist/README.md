# XO-9 — Honorport Heist (Docker in Docker)

**Category:** CI/CD / Docker-in-Docker / Container Security  
**Difficulty:** Hard / Expert  
**Interfaces:** TCP/8080 (Web Gateway) & TCP/2222 (SSH Interface)  

---

## Mission Briefing

Doctor Doom's naval logistics facility, **Honorport**, relies on an automated container deployment engine to manage high-security cargo dispatches.
Logistics operators interact with the deployment portal to validate and launch cargo containers into designated vault zones.

Your objective is to perform a security assessment against the Honorport Logistics Console:
1. Connect to the Web Console at `http://<TARGET_HOST>:8080/` (or via SSH on TCP/2222).
2. Discover vulnerabilities in the automated container deployment pipeline.
3. Pivot through the execution environment and inspect the inner Docker container infrastructure.
4. Locate authorized credentials and forge a valid vault override authorization to recover the flag from the Honorport High-Security Mainframe Vault.

---

## Environment Information

- **Web Console Gateway:** `http://<TARGET_HOST>:8080/`
- **SSH Access:** `ssh honorport@<TARGET_HOST> -p 2222` (Accepts standard credentials or anonymous interactive session)
- **Inner Docker Engine:** Accessible within worker execution context via `DOCKER_HOST=tcp://127.0.0.1:2375` or standard `docker` CLI.

Good luck!
