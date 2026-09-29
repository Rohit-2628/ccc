#!/bin/bash
set -e

# Grab dynamic flag injected by CTF platform (with comprehensive fallbacks)
FLAG_VAL="$CHALLENGE_FLAG"
[ -z "$FLAG_VAL" ] && FLAG_VAL="$FLAG"
[ -z "$FLAG_VAL" ] && FLAG_VAL="$DYNAMIC_FLAG"
[ -z "$FLAG_VAL" ] && FLAG_VAL="$FLAG_VALUE"
[ -z "$FLAG_VAL" ] && FLAG_VAL="$TARGET_FLAG"
[ -z "$FLAG_VAL" ] && FLAG_VAL="YUVA{supp1y_ch41n_p01s0n1ng_t0_pr0d_d3p10ym3nt_x03}"

# Pass dynamic flag to production seed file with restricted permissions
echo -n "$FLAG_VAL" > /tmp/.supply_chain_flag_seed
chmod 600 /tmp/.supply_chain_flag_seed 2>/dev/null || true

# Unset sensitive environment variables before starting public gateway or background services
unset FLAG CHALLENGE_FLAG DYNAMIC_FLAG FLAG_VAL FLAG_VALUE TARGET_FLAG

# Ensure storage directories and initialize pristine seed snapshot
export PYTHONPATH="/app:${PYTHONPATH}"
python3 /app/challenge/snapshot/seed_state.py

# 1. Start Internal Package Repository (127.0.0.1:4873)
echo "[+] Launching Local Package Repository on 127.0.0.1:4873..."
python3 /app/challenge/package_repository/repo_server.py &
PKG_PID=$!

# 2. Start Internal OCI Container Registry (127.0.0.1:5000)
echo "[+] Launching Local OCI Container Registry on 127.0.0.1:5000..."
python3 /app/challenge/registry/registry_server.py &
REGISTRY_PID=$!

# 3. Start Internal Production Deployment Runtime (127.0.0.1:8083)
echo "[+] Launching Production Deployment Runtime on 127.0.0.1:8083..."
python3 /app/challenge/deployment/prod_server.py &
DEPLOYMENT_PID=$!

# 4. Start Internal CI Pipeline Orchestrator (127.0.0.1:8082)
echo "[+] Launching CI Pipeline Orchestrator on 127.0.0.1:8082..."
python3 /app/challenge/ci/ci_server.py &
CI_PID=$!

# Wait for internal services to become ready
sleep 1.5

# 5. Start Public Developer App & Gateway (0.0.0.0:80)
echo "[+] Launching Public Developer App & Gateway on 0.0.0.0:${PORT:-80}..."
python3 /app/challenge/developer_app/app.py &
GATEWAY_PID=$!

# Trap signals for graceful shutdown
cleanup() {
    echo "[*] Shutting down all supply chain services..."
    kill -TERM "$GATEWAY_PID" "$CI_PID" "$DEPLOYMENT_PID" "$REGISTRY_PID" "$PKG_PID" 2>/dev/null || true
    wait "$GATEWAY_PID" "$CI_PID" "$DEPLOYMENT_PID" "$REGISTRY_PID" "$PKG_PID" 2>/dev/null || true
    exit 0
}

trap cleanup SIGINT SIGTERM

# Keep container alive and supervise processes
wait -n "$GATEWAY_PID" "$CI_PID" "$DEPLOYMENT_PID" "$REGISTRY_PID" "$PKG_PID"
