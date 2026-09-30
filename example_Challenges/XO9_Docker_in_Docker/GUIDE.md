# XO-9 — Honorport Heist Architecture & Engineering Guide

## 1. Safety & Infrastructure Invariants
XO-9 satisfies the CTF Challenge Engineering Gate baselines:
- **Sandbox Requirement:** Classified as `SANDBOX_REQUIRED` due to DinD mechanics.
- **Zero Host Exposure:** No host `/var/run/docker.sock` mount. Inner Docker engine is completely container-isolated.
- **Network Isolation:** Single-port reverse proxy HTTP gateway (TCP/80) and SSH server (TCP/22).
- **Resource Constraints:** Pinned memory and CPU limits.

## 2. Inner Docker Mechanics
The inner Docker daemon is an emulated REST API server operating inside the container workspace (`127.0.0.1:2375`). A custom wrapper binary (`/usr/local/bin/docker`) communicates with this daemon so participants can run native `docker` commands.

## 3. Dynamic Reset Architecture
Calling `/api/reset` invokes `seed_state.py`, purging transient state and re-seeding all databases, registry manifests, and inner Docker image metadata.
