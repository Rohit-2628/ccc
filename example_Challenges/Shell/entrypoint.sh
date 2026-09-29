#!/bin/sh

# 1. Generate SSH host keys dynamically if they do not exist
ssh-keygen -A

# 2. Grab variables injected by k8sWorker.js (with comprehensive aliases and fallbacks)
USER="${SSH_USER:-${SHELL_USER:-${USER_NAME:-${USERNAME:-${USER:-root}}}}}"
PASS="${SSH_PASSWORD:-${SHELL_PASSWORD:-${PASSWORD:-${USER_PASSWORD:-cyberanzen123}}}}"
FLAG_VAL="$CHALLENGE_FLAG"
[ -z "$FLAG_VAL" ] && FLAG_VAL="$FLAG"
[ -z "$FLAG_VAL" ] && FLAG_VAL="$DYNAMIC_FLAG"
[ -z "$FLAG_VAL" ] && FLAG_VAL="$FLAG_VALUE"
[ -z "$FLAG_VAL" ] && FLAG_VAL="$TARGET_FLAG"
[ -z "$FLAG_VAL" ] && FLAG_VAL="YUVA{DEFAULT_SHELL_FLAG}"

# 3. Write dynamic flag to /flag.txt, /root/flag.txt, and /home/ctf/flag.txt
echo "$FLAG_VAL" > /flag.txt
echo "$FLAG_VAL" > /root/flag.txt
echo "$FLAG_VAL" > /home/ctf/flag.txt

chmod 644 /flag.txt
chmod 400 /root/flag.txt
chmod 644 /home/ctf/flag.txt
chown ctf:ctf /home/ctf/flag.txt 2>/dev/null || true

# 4. Create dynamic user if non-root and set password
echo "[Entrypoint] Configuring account for SSH user: $USER..."
if [ "$USER" != "root" ]; then
    if ! id "$USER" >/dev/null 2>&1; then
        echo "[Entrypoint] User $USER does not exist. Creating user account..."
        adduser -D -s /bin/bash "$USER" 2>/dev/null || useradd -m -s /bin/bash "$USER" 2>/dev/null
    fi
fi
echo "$USER:$PASS" | chpasswd
echo "root:$PASS" | chpasswd

# 5. Ensure SSH allows password login and root login by stripping existing rules and appending overrides
sed -i '/^#*PasswordAuthentication/d' /etc/ssh/sshd_config 2>/dev/null || true
sed -i '/^#*PermitRootLogin/d' /etc/ssh/sshd_config 2>/dev/null || true
sed -i '/^#*KbdInteractiveAuthentication/d' /etc/ssh/sshd_config 2>/dev/null || true
sed -i '/^#*UsePAM/d' /etc/ssh/sshd_config 2>/dev/null || true
sed -i '/^#*AuthenticationMethods/d' /etc/ssh/sshd_config 2>/dev/null || true
sed -i '/^#*PubkeyAuthentication/d' /etc/ssh/sshd_config 2>/dev/null || true

echo "PasswordAuthentication yes" >> /etc/ssh/sshd_config
echo "PermitRootLogin yes" >> /etc/ssh/sshd_config
echo "KbdInteractiveAuthentication yes" >> /etc/ssh/sshd_config
echo "UsePAM no" >> /etc/ssh/sshd_config
echo "PubkeyAuthentication yes" >> /etc/ssh/sshd_config

# 6. Unset sensitive environment variables before starting sshd
unset SSH_PASSWORD SHELL_PASSWORD PASSWORD USER_PASSWORD
unset SSH_USER SHELL_USER USER_NAME USERNAME USER
unset FLAG CHALLENGE_FLAG DYNAMIC_FLAG

# 7. Start SSH daemon in the foreground
exec /usr/sbin/sshd -D -e
