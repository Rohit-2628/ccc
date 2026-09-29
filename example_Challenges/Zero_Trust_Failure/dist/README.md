# Challenge X10: Zero Trust Failure

**Category:** Zero-Trust Architecture / Service Identity / Lateral Movement  
**Difficulty:** Expert / Bonus  
**External Interface:** TCP/80 (HTTP Web / REST API)  

---

## 📖 Mission Briefing

The Latverian Citadel has deployed the **Citadel Zero-Trust Network Fabric**, enforcing identity-based authentication across all sovereign microservices. In this architecture, network reachability does not imply trust—every request across service boundaries must carry a valid service identity assertion.

External access is mediated by a public Ingress Gateway. The internal services operate in tiered trust enclaves:
- **Low-Trust Application (Edge Worker):** Collects edge telemetry and runs diagnostic routines.
- **Trusted Internal Service (Citadel Core Engine):** Enforces service policy and mints administrative grants.
- **Admin Service (Citadel Sovereign Vault):** Protects the sovereign flag.

Your objective is to explore the service mesh, inspect how service identity is established and authenticated across internal boundaries, identify the weak trust assumption, forge the expected trusted request context, and unlock the Sovereign Vault.

---

## 🌐 Public Endpoints

| Endpoint | Target Component | Description |
| :--- | :--- | :--- |
| `GET /` | Gateway Ingress | Web control console and architecture dashboard |
| `GET /api/v1/topology` | Gateway Ingress | Public mesh architecture and topology map |
| `GET /api/v1/telemetry/status` | Low-Trust App | Edge telemetry metrics and status |
| `GET /api/v1/diagnostics/inspect` | Low-Trust App | Diagnostic inspection & identity attestation metadata |
| `POST /api/v1/diagnostics/exec` | Low-Trust App | Diagnostic execution console in edge sandbox |
| `POST /api/v1/relay/dispatch` | Low-Trust App | Internal mesh dispatcher with custom assertion headers |

---

## 🛠️ Client Sample

A starter script (`mesh_relay_sample.py`) is provided in this package to demonstrate interacting with the public gateway.
