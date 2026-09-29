FROM alpine:3.18

# Install OpenSSH server, bash, and shadow
RUN apk update && \
    apk add --no-cache openssh-server bash shadow && \
    mkdir -p /var/run/sshd

# Configure SSH daemon settings to allow password authentication and root login
RUN sed -i 's/^#*PermitRootLogin.*/PermitRootLogin yes/' /etc/ssh/sshd_config && \
    sed -i 's/^#*PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config && \
    sed -i 's/^#*KbdInteractiveAuthentication.*/KbdInteractiveAuthentication yes/' /etc/ssh/sshd_config && \
    echo "" >> /etc/ssh/sshd_config && \
    echo "PermitRootLogin yes" >> /etc/ssh/sshd_config && \
    echo "PasswordAuthentication yes" >> /etc/ssh/sshd_config && \
    echo "KbdInteractiveAuthentication yes" >> /etc/ssh/sshd_config && \
    echo "UsePAM no" >> /etc/ssh/sshd_config

# Set password for root to 'ctf' and create non-privileged 'ctf' user with password 'ctf'
RUN echo "root:ctf" | chpasswd && \
    adduser -D -s /bin/bash ctf && \
    echo "ctf:ctf" | chpasswd

# Set up working directory
WORKDIR /root

# Copy the entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose standard SSH port
EXPOSE 22

# Start using the entrypoint script
ENTRYPOINT ["/entrypoint.sh"]
