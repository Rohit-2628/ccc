#!/bin/bash
set -e

echo "===================================================================="
echo "  STARTING XO-9: HONORPORT HEIST (DOCKER IN DOCKER)"
echo "===================================================================="

# 1. Ensure docker CLI link
if [ -f "/app/challenge/inner_docker/docker_cli.py" ]; then
    cp /app/challenge/inner_docker/docker_cli.py /usr/local/bin/docker
    chmod +x /usr/local/bin/docker
fi

# 2. Seed state and database
python3 /app/challenge/snapshot/seed_state.py

# 3. Start Inner Docker Daemon API (Port 2375)
python3 /app/challenge/inner_docker/docker_daemon.py &
DIND_PID=$!
echo "[+] Started Inner Docker Daemon (PID: $DIND_PID)"

# 4. Start OCI Registry Server (Port 5000)
python3 /app/challenge/registry/registry_server.py &
REGISTRY_PID=$!
echo "[+] Started OCI Registry Server (PID: $REGISTRY_PID)"

# 5. Start Honorport Logistics API (Port 8082)
python3 /app/challenge/honorport_api/honorport_server.py &
API_PID=$!
echo "[+] Started Honorport Logistics API (PID: $API_PID)"

# 6. Start Honorport Mainframe Vault Production Server (Port 8083)
python3 /app/challenge/production/prod_server.py &
PROD_PID=$!
echo "[+] Started Honorport Production Mainframe Vault (PID: $PROD_PID)"

# 7. Start Synthetic SSH Server (Port 22 / SSH_PORT)
python3 /app/challenge/honorport_api/ssh_server.py ${SSH_PORT:-22} &
SSH_PID=$!
echo "[+] Started Honorport SSH Gateway (PID: $SSH_PID)"

# 8. Give services a brief moment to initialize
sleep 2

# 9. Start Unified Web Gateway in foreground
echo "[+] Starting Web Gateway on port ${PORT:-8080}..."
exec python3 /app/challenge/gateway/app.py
