FROM python:3.11-slim

LABEL name="xo9-docker-in-docker" \
      version="1.0.0" \
      description="XO-9: Honorport Heist (Docker in Docker CTF Challenge)" \
      classification="SANDBOX_REQUIRED"

WORKDIR /app

# Install system dependencies & security tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    openssh-server \
    net-tools \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
RUN pip install --no-cache-dir paramiko requests flask

# Copy challenge assets
COPY . /app/

# Set up permissions and CLI wrapper
RUN chmod +x /app/entrypoint.sh && \
    chmod +x /app/challenge/snapshot/seed_state.py && \
    chmod +x /app/challenge/inner_docker/docker_cli.py && \
    cp /app/challenge/inner_docker/docker_cli.py /usr/local/bin/docker && \
    chmod +x /usr/local/bin/docker

EXPOSE 80 22 8080

ENV PORT=8080
ENV SSH_PORT=22
ENV DOCKER_HOST=tcp://127.0.0.1:2375

ENTRYPOINT ["/app/entrypoint.sh"]
