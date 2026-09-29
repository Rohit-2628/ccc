FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install core runtime dependencies, SSH daemon, compiler, Python, and diagnostic utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-server \
    python3 \
    gcc \
    make \
    libc6-dev \
    sudo \
    curl \
    netcat-openbsd \
    socat \
    procps \
    nano \
    vim-tiny \
    xxd \
    && rm -rf /var/lib/apt/lists/*

# Create internal service and user groups
RUN groupadd -g 2000 sentinel-users && \
    useradd -u 1002 -g sentinel-users -m -s /bin/bash sentry && \
    useradd -u 1001 -g sentinel-users -m -s /bin/bash ctf

# Create directory tree
RUN mkdir -p /opt/sentinel/bin /opt/sentinel/src /opt/sentinel/config \
    /run/sentinel /var/run/sentinel /var/log/sentinel/snapshots /var/run/sshd

# Copy challenge source files
COPY src/ /opt/sentinel/src/
COPY config/ /opt/sentinel/config/

# Compile Stage 3 SUID privileged container controller
RUN gcc -fno-stack-protector -no-pie -z execstack -Wall -O0 \
    -o /opt/sentinel/bin/container-ctl /opt/sentinel/src/container-ctl.c && \
    chown root:root /opt/sentinel/bin/container-ctl && \
    chmod 4755 /opt/sentinel/bin/container-ctl

# Install Stage 1 restricted diagnostic shell
RUN cp /opt/sentinel/src/sentinel-shell.py /opt/sentinel/bin/sentinel-shell && \
    chmod 755 /opt/sentinel/bin/sentinel-shell && \
    chsh -s /opt/sentinel/bin/sentinel-shell ctf

# Setup directory ownership & permissions
RUN chown -R sentry:sentinel-users /run/sentinel /var/run/sentinel /var/log/sentinel && \
    chmod -R 775 /run/sentinel /var/run/sentinel /var/log/sentinel && \
    mkdir -p /home/sentry/.ssh && \
    chown -R sentry:sentinel-users /home/sentry && \
    chmod 700 /home/sentry/.ssh

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose standard SSH port
EXPOSE 22

# Start container via entrypoint
ENTRYPOINT ["/entrypoint.sh"]
