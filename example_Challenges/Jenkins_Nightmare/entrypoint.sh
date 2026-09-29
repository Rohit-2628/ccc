#!/bin/bash
set -e

echo "[*] Initializing Latveria Sovereign CI/CD Infrastructure (Jenkins Nightmare)..."

# Ensure runtime directories exist
mkdir -p /tmp/ci_build_workspace /tmp/ci_artifacts /tmp/registry_storage

# Grab dynamic flag injected by CTF platform (with comprehensive fallbacks)
FLAG_VAL="$CHALLENGE_FLAG"
[ -z "$FLAG_VAL" ] && FLAG_VAL="$FLAG"
[ -z "$FLAG_VAL" ] && FLAG_VAL="$DYNAMIC_FLAG"
[ -z "$FLAG_VAL" ] && FLAG_VAL="$FLAG_VALUE"
[ -z "$FLAG_VAL" ] && FLAG_VAL="$TARGET_FLAG"
[ -z "$FLAG_VAL" ] && FLAG_VAL="YUVA{c1_cd_ch41n_0f_trust_c0mpr0m1s3d_x01}"

# Pass dynamic flag to production mock seed file
echo -n "$FLAG_VAL" > /tmp/.prod_flag_seed

# Unset sensitive environment variables before starting public CI gateway or background processes
unset FLAG CHALLENGE_FLAG DYNAMIC_FLAG FLAG_VAL FLAG_VALUE TARGET_FLAG

# 1. Start Internal Private OCI Container Registry (127.0.0.1:5000)
echo "[+] Launching Local OCI Container Registry on 127.0.0.1:5000..."
python3 /app/challenge/registry/registry_server.py &
REGISTRY_PID=$!

# 2. Start Internal Production Mock Mainframe (127.0.0.1:8081)
echo "[+] Launching Isolated Production Mock Mainframe on 127.0.0.1:8081..."
python3 /app/challenge/production/prod_server.py &
PRODUCTION_PID=$!

# Wait for internal services to become ready
sleep 1

# 3. Start Public CI Gateway & Orchestrator (0.0.0.0:80)
echo "[+] Launching Sovereign CI Gateway Orchestrator on 0.0.0.0:${PORT:-80}..."
python3 /app/challenge/ci/app.py &
GATEWAY_PID=$!

# Trap signals for graceful shutdown
cleanup() {
    echo "[*] Shutting down all services..."
    kill -TERM "$GATEWAY_PID" "$REGISTRY_PID" "$PRODUCTION_PID" 2>/dev/null || true
    wait "$GATEWAY_PID" "$REGISTRY_PID" "$PRODUCTION_PID" 2>/dev/null || true
    exit 0
}

trap cleanup SIGINT SIGTERM

# Keep container alive and supervise processes
wait -n "$GATEWAY_PID" "$REGISTRY_PID" "$PRODUCTION_PID"
