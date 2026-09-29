FROM node:18-alpine

WORKDIR /app

# Copy package files and install dependencies
COPY package*.json ./
RUN npm install --production

# Copy application files
COPY server.js ./
COPY entrypoint.sh ./

RUN chmod +x entrypoint.sh

# Expose HTTP port
EXPOSE 80

# Run entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]
