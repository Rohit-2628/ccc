FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies for local testing
RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-server \
    python3 \
    gcc \
    make \
    libc6-dev \
    curl \
    netcat-openbsd \
    socat \
    procps \
    xxd \
    && rm -rf /var/lib/apt/lists/*

# Create internal groups and test user
RUN groupadd -g 2000 sentinel-users && \
    useradd -u 1002 -g sentinel-users -m -s /bin/bash sentry && \
    useradd -u 1001 -g sentinel-users -m -s /bin/bash ctf && \
    echo "ctf:sentinel123" | chpasswd && \
    echo "sentry:sentinel123" | chpasswd && \
    echo "root:sentinel123" | chpasswd

# Setup directory structure
RUN mkdir -p /opt/sentinel/bin /opt/sentinel/src /run/sentinel /var/run/sentinel /var/log/sentinel/snapshots /var/run/sshd

# Expose SSH port
EXPOSE 22

CMD ["/usr/sbin/sshd", "-D"]
