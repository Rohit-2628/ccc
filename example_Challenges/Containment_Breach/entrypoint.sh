#!/bin/bash
set -e

# 1. Generate SSH host keys dynamically if they do not exist
ssh-keygen -A

# 2. Grab environment variables injected by CTF platform (with comprehensive fallbacks)
USER="${SSH_USER:-${SHELL_USER:-${USER_NAME:-${USERNAME:-${USER:-ctf}}}}}"
PASS="${SSH_PASSWORD:-${SHELL_PASSWORD:-${PASSWORD:-${USER_PASSWORD:-sentinel123}}}}"
FLAG_VAL="$CHALLENGE_FLAG"
[ -z "$FLAG_VAL" ] && FLAG_VAL="$FLAG"
[ -z "$FLAG_VAL" ] && FLAG_VAL="$DYNAMIC_FLAG"
[ -z "$FLAG_VAL" ] && FLAG_VAL="$FLAG_VALUE"
[ -z "$FLAG_VAL" ] && FLAG_VAL="$TARGET_FLAG"
[ -z "$FLAG_VAL" ] && FLAG_VAL="YUVA{s3nt1n3l_c0nt41n3r_br34ch_pwn3d}"

# 3. Write dynamic flag securely to /root/flag.txt
echo "$FLAG_VAL" > /root/flag.txt
chmod 400 /root/flag.txt
chown root:root /root/flag.txt

# 4. Configure initial user account
if ! id "$USER" >/dev/null 2>&1; then
    useradd -m -s /opt/sentinel/bin/sentinel-shell -g sentinel-users "$USER"
fi
# Ensure user belongs to sentinel-users group
usermod -a -G sentinel-users "$USER" 2>/dev/null || true
# Ensure login shell is sentinel-shell for stage 1
chsh -s /opt/sentinel/bin/sentinel-shell "$USER" 2>/dev/null || true

# Update passwords
echo "$USER:$PASS" | chpasswd
echo "root:$PASS" | chpasswd
echo "sentry:$PASS" | chpasswd

# 5. Generate ephemeral token for Stage 2 IPC Daemon
mkdir -p /run/sentinel /var/run/sentinel /var/log/sentinel/snapshots
chown -R sentry:sentinel-users /run/sentinel /var/run/sentinel /var/log/sentinel
chmod 775 /run/sentinel /var/run/sentinel /var/log/sentinel /var/log/sentinel/snapshots

SENTRY_TOKEN=$(head -c 16 /dev/urandom | xxd -p 2>/dev/null || od -N 16 -t x1 /dev/urandom | head -1 | tr -d ' ')
echo -n "$SENTRY_TOKEN" > /var/run/sentinel/sentry.token
chown sentry:sentinel-users /var/run/sentinel/sentry.token
chmod 440 /var/run/sentinel/sentry.token

# Ensure /home/sentry/.ssh directory exists with proper permissions
mkdir -p /home/sentry/.ssh
chown sentry:sentinel-users /home/sentry/.ssh
chmod 700 /home/sentry/.ssh

# 6. Launch Stage 2 IPC Daemon as user sentry in the background
su -s /bin/bash sentry -c "python3 /opt/sentinel/src/sentry-agent.py" >/var/log/sentinel/sentry-agent.log 2>&1 &

# 7. Ensure SSH configuration permits password and key authentication
mkdir -p /var/run/sshd
sed -i 's/^#*PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config 2>/dev/null || true
sed -i 's/^#*PubkeyAuthentication.*/PubkeyAuthentication yes/' /etc/ssh/sshd_config 2>/dev/null || true
sed -i 's/^#*PermitRootLogin.*/PermitRootLogin yes/' /etc/ssh/sshd_config 2>/dev/null || true
sed -i 's/^#*KbdInteractiveAuthentication.*/KbdInteractiveAuthentication yes/' /etc/ssh/sshd_config 2>/dev/null || true

# 8. Unset sensitive environment variables before starting sshd
unset SSH_PASSWORD SHELL_PASSWORD PASSWORD USER_PASSWORD
unset SSH_USER SHELL_USER USER_NAME USERNAME USER
unset FLAG CHALLENGE_FLAG DYNAMIC_FLAG FLAG_VAL SENTRY_TOKEN FLAG_VALUE TARGET_FLAG

echo "[Entrypoint] Sentinel Container Environment online. Starting SSH service..."
exec /usr/sbin/sshd -D -e
