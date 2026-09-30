FROM python:3.11-slim

# Install system dependencies & SSH components
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    openssh-server \
    openssh-client \
    bash \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
RUN pip install --no-cache-dir paramiko

# Create unprivileged CTF user & group
RUN groupadd -g 10001 ctf && \
    useradd -u 10001 -g ctf -m -s /bin/bash ctf

WORKDIR /app

# Copy challenge files
COPY challenge /app/challenge
COPY entrypoint.sh /app/entrypoint.sh

# Make docker CLI binary wrapper available system-wide
RUN cp /app/challenge/inner_docker/docker_cli.py /usr/local/bin/docker && \
    chmod +x /usr/local/bin/docker && \
    chmod +x /app/entrypoint.sh

# Set ownership and permissions
RUN chown -R ctf:ctf /app

USER ctf

EXPOSE 8080 2222

ENTRYPOINT ["/app/entrypoint.sh"]
