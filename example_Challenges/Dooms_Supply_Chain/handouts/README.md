# X03 — Dooms Supply Chain

**Category:** Supply Chain / Package Registry / CI/CD  
**Difficulty:** Expert / Bonus  
**External Interface:** TCP/80 (Web Application & API)  

---

## Mission Briefing

Intelligence reports indicate that Doctor Victor von Doom's Cyber-Manufacturing division operates an automated, software supply-chain pipeline for the sovereign Doombot defense grid.

The supply-chain pipeline links developer project specifications, internal package registries, automated CI/CD runners, OCI container image repositories, and production mainframe clusters.

Your objective as an operative is to investigate the synthetic development environment, analyze package provenance across internal dependencies, discover any weaknesses in the software supply chain, trace how artifacts enter the build and container deployment flow, and reach the production target to recover the mission flag.

---

## Target Interface

The challenge exposes a web console and developer REST API on **TCP/80**:

- **Web Dashboard:** `http://<TARGET_HOST>:<PORT>/`
- **Developer Info:** `GET /api/app/info`
- **Package Index:** `GET /api/packages`
- **CI Pipelines:** `GET /api/ci/pipelines`
- **Image Registry:** `GET /registry/v2/_catalog`
- **Production Status:** `GET /api/deployment/status`

---

## Supply Chain Architecture

```text
Public Entry
     │
     ▼
Developer App
     │
     ▼
Package Repository
     │
     ▼
CI Pipeline
     │
     ▼
Built Image / Registry
     │
     ▼
Production Deployment
     │
     ▼
Flag
```

---

## Rules of Engagement

1. All target infrastructure and registries are local to the challenge instance. No external Internet package downloading or external publication is needed.
2. The supply-chain relationship is central to the challenge. Follow the provenance of packages, build steps, and container deployment artifacts.
3. Good luck, operative.
