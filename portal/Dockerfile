# ==============================================================================
# Dockerfile: portal (React + Vite PWA)
# Multi-stage build with unprivileged Nginx
# ==============================================================================
FROM node:22-alpine AS builder

WORKDIR /app

# Cache node modules
COPY package.json package-lock.json ./
RUN npm ci

# Copy sources and compile PWA bundle
COPY . .
RUN npm run build

# ==============================================================================
# Runner stage: Nginx Unprivileged
# ==============================================================================
FROM nginxinc/nginx-unprivileged:alpine AS runner

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://127.0.0.1:8080/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
