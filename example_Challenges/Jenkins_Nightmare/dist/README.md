# X01 — Jenkins Nightmare

**Category:** CI/CD / Pipeline Compromise / Build Runner Security  
**Difficulty:** Expert / Bonus  
**External Interface:** TCP/80 (Web)  

---

## Mission Briefing

Intelligence reports indicate that Doctor Doom's state engineering corps utilizes a bespoke, isolated CI/CD automation pipeline codenamed **Jenkins Nightmare** to build, test, package, and deploy critical defense firmware and telemetry daemons.

The entire deployment workflow follows a strict chain of trust:

```text
Developer Git ➔ CI Orchestrator ➔ Isolated Build Runner ➔ Container Registry ➔ Production Mainframe
```

Your objective is to assess the security posture of this CI/CD pipeline infrastructure, identify weaknesses in how pipeline jobs and execution parameters are processed, influence the build runner to extract operational credentials, reach the internal container registry, and pivot into the sovereign production environment to override the defense grid and recover the target flag.

---

## Target Information

- **Web Gateway:** `http://<TARGET_HOST>:<TARGET_PORT>/`
- **Primary Protocol:** HTTP (TCP/80)

---

## Rules of Engagement & Constraints

1. The challenge environment is entirely self-contained. No external network or Internet access is needed or permitted.
2. Build runner jobs execute within an ephemeral isolated workspace subject to a hard 90-second timeout limit.
3. Brute forcing is neither required nor effective. Follow the chain of trust.
