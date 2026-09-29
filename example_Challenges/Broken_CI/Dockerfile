FROM python:3.11-slim

# Install system dependencies (no runtime external downloads needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    tar \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Install required Python packages
RUN pip install --no-cache-dir flask requests paramiko

# Create unprivileged service user
RUN groupadd -g 1000 latveria && \
    useradd -u 1000 -g latveria -m -s /bin/bash latveria

WORKDIR /app

# Copy challenge application files
COPY challenge/ /app/challenge/
COPY entrypoint.sh /app/entrypoint.sh

# Create required directories with proper permissions
RUN mkdir -p /tmp/x04_storage /usr/local/bin && \
    cp /app/challenge/inner_docker/docker_cli.py /usr/local/bin/docker && \
    chmod +x /usr/local/bin/docker && \
    chown -R latveria:latveria /app /tmp /tmp/x04_storage && \
    chmod +x /app/entrypoint.sh

USER latveria

EXPOSE 80

ENTRYPOINT ["/app/entrypoint.sh"]
