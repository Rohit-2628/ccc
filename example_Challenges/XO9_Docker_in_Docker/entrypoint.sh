#!/bin/bash
set -e

echo "[*] Initializing XO-9 Honorport Heist Sandbox Environment..."
python3 /app/challenge/snapshot/seed_state.py

echo "[*] Starting Inner Docker Daemon (TCP/2375)..."
python3 /app/challenge/inner_docker/docker_daemon.py &
DIND_PID=$!

echo "[*] Starting Challenge OCI Registry (TCP/5000)..."
python3 /app/challenge/registry/registry_server.py &
REGISTRY_PID=$!

echo "[*] Starting Honorport Controller API (TCP/8082)..."
python3 /app/challenge/honorport_api/honorport_server.py &
HONORPORT_PID=$!

echo "[*] Starting Honorport Production Vault Server (TCP/8083)..."
python3 /app/challenge/production/prod_server.py &
PROD_PID=$!

echo "[*] Starting Honorport SSH Server (TCP/2222)..."
python3 /app/challenge/ssh_server/ssh_server.py 2222 &
SSH_PID=$!

# Brief startup delay
sleep 2

echo "[*] Launching Unified Web Gateway (TCP/8080)..."
exec python3 /app/challenge/gateway/app.py
