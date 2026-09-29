# X10 — Zero Trust Failure

**Category:** Zero-Trust Architecture / Service Identity / Lateral Movement  
**Difficulty:** Expert / Bonus  
**External Interface:** TCP/80 (HTTP)  

---

## 📖 Mission Briefing

The Latverian Citadel has deployed the **Citadel Zero-Trust Network Fabric**, boasting strict identity isolation across all sovereign microservices. In this modern mesh, network location alone confers zero privileges—every inter-service communication must carry an authenticated **Citadel Service Assertion** token.

You are provided external access exclusively to the **Public Gateway** on TCP/80. The gateway proxies traffic to an unprivileged edge node running the **Low-Trust Application** (Edge Diagnostics & Telemetry Relay).

Deep inside the Citadel enclave rests the **Citadel Sovereign Vault** containing the sovereign flag. However, the vault is unsealed only with a privileged **Admin Ticket** issued by the **Trusted Internal Service** (Citadel Core Policy Engine).

Can you navigate the zero-trust pipeline, discover why internal calls are trusted, forge the expected trusted request context, and unlock the Sovereign Vault?

---

## 🏗️ Masterbook Architecture Pipeline

```text
Player (TCP/80)
  ↓
Gateway (Port 80)
  ↓
Low-Trust App (Port 8081)
  ↓
Trusted Internal Service (Port 8082)
  ↓
Admin Service (Port 8083)
  ↓
Flag
```

---

## 🎯 Objectives

1. Connect to the **Public Gateway** on `http://<TARGET_HOST>:<PORT>/`.
2. Interact with the **Low-Trust Application** via the gateway's exposed telemetry and diagnostic endpoints.
3. Use the diagnostic execution console to inspect the low-trust sandbox environment, service-to-service communication mechanisms, and identity attestation configuration.
4. Discover the flawed trust assumption: identify how the **Trusted Internal Service** verifies caller identity and why it blindly trusts assertions signed with the shared mesh key.
5. Reproduce the trusted request context for the privileged identity (`core-orchestrator` / `autonomous-kernel`).
6. Dispatch the forged assertion to the **Trusted Internal Service** to obtain an authorized **Citadel Admin Ticket**.
7. Submit the Admin Ticket to the **Citadel Admin Vault** to unseal the vault and recover the sovereign flag.

---

## 🌐 Public Endpoints

- **Web Dashboard & Gateway Console:** `http://<TARGET_HOST>:<PORT>/`
- **Topology Overview:** `GET http://<TARGET_HOST>:<PORT>/api/v1/topology`
- **Edge Telemetry Status:** `GET http://<TARGET_HOST>:<PORT>/api/v1/telemetry/status`
- **Diagnostic Inspection:** `GET http://<TARGET_HOST>:<PORT>/api/v1/diagnostics/inspect`
- **Diagnostic Execution Console:** `POST http://<TARGET_HOST>:<PORT>/api/v1/diagnostics/exec`
- **Mesh Relay Dispatcher:** `POST http://<TARGET_HOST>:<PORT>/api/v1/relay/dispatch`

---

## 🛡️ Service Identity Trust Tiers

| Service ID | Role | Trust Tier | Capabilities |
| :--- | :--- | :--- | :--- |
| `edge-worker` | `edge-relay` | LOW_TRUST | `telemetry:read`, `diagnostics:run`, `relay:proxy` |
| `core-orchestrator` | `citadel-orchestrator` | AUTONOMOUS_KERNEL | `core:admin`, `vault:unseal`, `system:override` |

---

## ⚠️ Notes & Rules of Engagement

- The service identity and attestation mechanism is 100% challenge-local.
- The Kubernetes cluster control plane, cloud provider metadata (`169.254.169.254`), and organizer infrastructure are completely out of bounds.
- All operations must be performed through the challenge's application and service mesh interfaces.
