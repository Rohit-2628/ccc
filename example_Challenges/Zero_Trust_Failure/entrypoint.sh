#!/bin/bash
set -e

APP_DIR="${APP_DIR:-$(cd "$(dirname "$0")" && pwd)}"

echo "[*] Initializing Latveria Citadel Zero-Trust Enclave (X10 - Zero Trust Failure)..."

# Ensure runtime directory exists
export STATE_DIR="${STATE_DIR:-/tmp/citadel_mesh_state}"
mkdir -p "$STATE_DIR"

# Initialize mesh configuration and challenge-local signing key
python3 -c "import sys; sys.path.insert(0, '${APP_DIR}/challenge'); from common.mesh_identity import ensure_mesh_initialized; ensure_mesh_initialized()"

# Grab dynamic flag injected by CTF platform (with comprehensive fallbacks)
FLAG_VAL="$CHALLENGE_FLAG"
[ -z "$FLAG_VAL" ] && FLAG_VAL="$FLAG"
[ -z "$FLAG_VAL" ] && FLAG_VAL="$DYNAMIC_FLAG"
[ -z "$FLAG_VAL" ] && FLAG_VAL="$FLAG_VALUE"
[ -z "$FLAG_VAL" ] && FLAG_VAL="$TARGET_FLAG"
[ -z "$FLAG_VAL" ] && FLAG_VAL="YUVA{z3r0_trust_f41lur3_s3rv1c3_1d3nt1ty_x10}"

# Pass dynamic flag to citadel seed file with restricted permissions
echo -n "$FLAG_VAL" > /tmp/.citadel_flag_seed
chmod 600 /tmp/.citadel_flag_seed 2>/dev/null || true

# Unset sensitive environment variables before starting public gateway or background services
unset FLAG CHALLENGE_FLAG DYNAMIC_FLAG FLAG_VAL FLAG_VALUE TARGET_FLAG

# 1. Start Admin Service (Citadel Sovereign Vault) on 127.0.0.1:8083 (consumes and deletes seed file immediately)
echo "[+] Launching Admin Service (Citadel Sovereign Vault) on 127.0.0.1:8083..."
python3 "${APP_DIR}/challenge/admin_service/app.py" &
ADMIN_PID=$!

# 2. Start Trusted Internal Service (Citadel Core Policy Engine) on 127.0.0.1:8082
echo "[+] Launching Trusted Internal Service (Core Engine) on 127.0.0.1:8082..."
python3 "${APP_DIR}/challenge/trusted_service/app.py" &
TRUSTED_PID=$!

# 3. Start Low-Trust Service (Edge Diagnostics & Relay) on 127.0.0.1:8081
echo "[+] Launching Low-Trust Service (Edge Worker) on 127.0.0.1:8081..."
python3 "${APP_DIR}/challenge/low_trust_service/app.py" &
LOW_TRUST_PID=$!

# Wait for internal microservices to initialize
sleep 1

# 4. Start Public Ingress Gateway on 0.0.0.0:${PORT:-80}
echo "[+] Launching Public Gateway on 0.0.0.0:${PORT:-80}..."
python3 "${APP_DIR}/challenge/gateway/app.py" &
GATEWAY_PID=$!

# Trap signals for graceful termination
cleanup() {
    echo "[*] Shutting down all Citadel microservices..."
    kill -TERM "$GATEWAY_PID" "$LOW_TRUST_PID" "$TRUSTED_PID" "$ADMIN_PID" 2>/dev/null || true
    wait "$GATEWAY_PID" "$LOW_TRUST_PID" "$TRUSTED_PID" "$ADMIN_PID" 2>/dev/null || true
    exit 0
}

trap cleanup SIGINT SIGTERM

# Supervise processes
wait -n "$GATEWAY_PID" "$LOW_TRUST_PID" "$TRUSTED_PID" "$ADMIN_PID"
