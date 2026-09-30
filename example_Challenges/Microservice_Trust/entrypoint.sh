#!/bin/bash
set -e

APP_DIR="${APP_DIR:-$(cd "$(dirname "$0")" && pwd)}"

echo "===================================================================="
echo "  STARTING LATVERIA CITADEL MICROSERVICE MESH (X02 - MICROSERVICE TRUST)"
echo "===================================================================="

# Ensure runtime directories exist
export PKI_DIR="${PKI_DIR:-/tmp/citadel_mesh_pki}"
mkdir -p "$PKI_DIR"

# Grab dynamic flag injected by CTF platform (with comprehensive fallbacks)
FLAG_VAL="$CHALLENGE_FLAG"
[ -z "$FLAG_VAL" ] && FLAG_VAL="$FLAG"
[ -z "$FLAG_VAL" ] && FLAG_VAL="$DYNAMIC_FLAG"
[ -z "$FLAG_VAL" ] && FLAG_VAL="$FLAG_VALUE"
[ -z "$FLAG_VAL" ] && FLAG_VAL="$TARGET_FLAG"
[ -z "$FLAG_VAL" ] && FLAG_VAL="YUVA{m1cr0s3rv1c3_1d3nt1ty_ch41n_br0k3n_x02}"

# Pass dynamic flag to mesh seed file with restricted permissions
echo -n "$FLAG_VAL" > /tmp/.mesh_flag_seed 2>/dev/null || echo -n "$FLAG_VAL" > "${PKI_DIR}/.mesh_flag_seed" 2>/dev/null || true
chmod 600 /tmp/.mesh_flag_seed "${PKI_DIR}/.mesh_flag_seed" 2>/dev/null || true

# Unset sensitive environment variables before starting public gateway or background services
unset FLAG CHALLENGE_FLAG DYNAMIC_FLAG FLAG_VAL FLAG_VALUE TARGET_FLAG

# Synchronously initialize Root CA & Service A credentials once
python3 -c "import sys; sys.path.insert(0, '${APP_DIR}/challenge'); from common.mesh_crypto import ensure_pki_initialized; ensure_pki_initialized()"

# 1. Start Admin Service (Citadel Sovereign Vault) on 127.0.0.1:8083 (consumes and deletes seed file immediately)
echo "[+] Launching Admin Service (Citadel Vault) on 127.0.0.1:8083..."
python3 "${APP_DIR}/challenge/admin/app.py" &
ADMIN_PID=$!

# 2. Start Service B (Core Controller) on 127.0.0.1:8082
echo "[+] Launching Service B (Core Controller) on 127.0.0.1:8082..."
python3 "${APP_DIR}/challenge/service_b/app.py" &
SERVICE_B_PID=$!

# 3. Start Service A (Telemetry Agent) on 127.0.0.1:8081
echo "[+] Launching Service A (Telemetry Agent) on 127.0.0.1:8081..."
python3 "${APP_DIR}/challenge/service_a/app.py" &
SERVICE_A_PID=$!

# Wait for internal microservices to initialize
sleep 1

# 4. Start Public Gateway Ingress on 0.0.0.0:${PORT:-80}
PORT=${PORT:-80}
echo "[+] Launching Public Ingress Gateway on 0.0.0.0:${PORT}..."
python3 "${APP_DIR}/challenge/gateway/app.py" &
GATEWAY_PID=$!

# Trap signals for graceful termination
cleanup() {
    echo "[*] Shutting down all Citadel microservices..."
    kill -TERM "$GATEWAY_PID" "$SERVICE_A_PID" "$SERVICE_B_PID" "$ADMIN_PID" 2>/dev/null || true
    wait "$GATEWAY_PID" "$SERVICE_A_PID" "$SERVICE_B_PID" "$ADMIN_PID" 2>/dev/null || true
    exit 0
}

trap cleanup SIGINT SIGTERM

# Supervise processes
wait -n "$GATEWAY_PID" "$SERVICE_A_PID" "$SERVICE_B_PID" "$ADMIN_PID"
