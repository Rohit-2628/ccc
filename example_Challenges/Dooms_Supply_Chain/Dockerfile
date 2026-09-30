FROM debian:bookworm-slim

ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies & Python Flask runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-flask \
    make \
    curl \
    tar \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Create unprivileged service user
RUN groupadd -g 1000 latveria && \
    useradd -u 1000 -g latveria -m -s /bin/bash latveria

WORKDIR /app

# Copy challenge application files
COPY challenge/ /app/challenge/
COPY entrypoint.sh /app/entrypoint.sh

# Create required storage directories with proper permissions
RUN mkdir -p /tmp/x03_storage && \
    chmod 1777 /tmp && \
    chown -R latveria:latveria /app /tmp /tmp/x03_storage && \
    chmod -R 755 /app && \
    chmod +x /app/entrypoint.sh

USER latveria

EXPOSE 80

ENTRYPOINT ["/app/entrypoint.sh"]
