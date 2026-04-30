# ──────────────────────────────────────────────────────────────────
# NeuroDebug — Frontend Dockerfile
# Stage 1: Build React app
# Stage 2: Serve with nginx
# ──────────────────────────────────────────────────────────────────

# ── Stage 1: Build ─────────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies (leverage layer cache)
COPY package*.json ./
RUN npm ci --silent

# Copy source and build
COPY . .
RUN npm run build

# ── Stage 2: Serve ─────────────────────────────────────────────────
FROM nginx:1.25-alpine AS production

LABEL maintainer="neurodebug" \
      description="NeuroDebug React frontend served by nginx"

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy our nginx config
COPY nginx.conf /etc/nginx/conf.d/neurodebug.conf

# Copy the built React app
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose HTTP port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget -qO- http://127.0.0.1/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
