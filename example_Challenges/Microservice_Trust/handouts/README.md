# Challenge X02: Microservice Trust

**Category:** Service Identity / Authorization / Microservices  
**Difficulty:** Expert / Bonus  
**External Interface:** TCP/80 (HTTP Web / REST API)  

---

## Briefing

The Latverian Sovereign Citadel operates a multi-tier microservice mesh to supervise internal defense nodes and secure high-value mainframe infrastructure.

External access is mediated by a public Ingress Gateway. Internal services communicate using a challenge-local service identity assertion framework:
- **Service A (Edge Telemetry Agent):** Collects telemetry from edge units (low-trust).
- **Service B (Core Controller):** Manages cluster orchestration and delegates administrative authorizations (high-privilege).
- **Admin Service (Citadel Vault):** Houses sovereign master keys and the challenge flag.

Your objective is to explore the service mesh, inspect how identity is established across internal service boundaries, identify flaws in internal trust assumptions, and elevate your authorization to retrieve the sovereign vault key.

---

## Getting Started

1. Navigate to the web control console at `http://<TARGET_HOST>:80/`.
2. Inspect the mesh architecture, endpoint reference, and interactive dispatcher.
3. Discover challenge-local identity materials and analyze how internal authorization decisions are made.

---

## Service Mesh Endpoints

| Endpoint | Target Component | Description |
| :--- | :--- | :--- |
| `GET /api/v1/topology` | Gateway Ingress | Public mesh architecture & node list |
| `GET /api/v1/telemetry/status` | Service A (Telemetry) | Edge telemetry metrics and cluster health |
| `GET /api/v1/telemetry/config` | Service A (Telemetry) | Mesh routing and authentication policy specs |
| `GET /api/v1/diagnostics/export`| Service A (Telemetry) | Diagnostic support export bundle |
| `POST /api/v1/core/grant-admin-ticket` | Service B (Core) | Requests an Admin Grant Ticket (Requires verified identity) |
| `POST /api/v1/admin/unlock-vault` | Admin Vault | Unlocks sovereign vault with Admin Ticket |

---

## Client Helper Sample

A Python client script (`mesh_client_sample.py`) is provided in this distribution to demonstrate how to format and dispatch authenticated requests to the mesh gateway.
