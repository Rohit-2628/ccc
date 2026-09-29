FROM python:3.11-slim

# Install system dependencies (no runtime external downloads needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    make \
    curl \
    tar \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Install required Python packages
RUN pip install --no-cache-dir flask

# Create unprivileged service user
RUN groupadd -g 1000 latveria && \
    useradd -u 1000 -g latveria -m -s /bin/bash latveria

WORKDIR /app

# Copy challenge application files
COPY challenge/ /app/challenge/
COPY entrypoint.sh /app/entrypoint.sh

# Create required storage directories with proper permissions
RUN mkdir -p /tmp/x03_storage && \
    chown -R latveria:latveria /app /tmp/x03_storage && \
    chmod +x /app/entrypoint.sh

USER latveria

EXPOSE 80

ENTRYPOINT ["/app/entrypoint.sh"]
