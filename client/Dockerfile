# Multi-stage build for React frontend
FROM node:18-alpine as builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy root config files
COPY vite.config.ts tailwind.config.ts postcss.config.js tsconfig.json components.json ./

# Copy source
COPY client/ ./client/
COPY shared/ ./shared/

# Build arguments
ARG VITE_API_URL=http://localhost:8000
ARG VITE_FIREBASE_API_KEY
ARG VITE_FIREBASE_PROJECT_ID
ARG VITE_FIREBASE_APP_ID

# Set environment variables for build
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_FIREBASE_API_KEY=$VITE_FIREBASE_API_KEY
ENV VITE_FIREBASE_PROJECT_ID=$VITE_FIREBASE_PROJECT_ID
ENV VITE_FIREBASE_APP_ID=$VITE_FIREBASE_APP_ID

# Build
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy nginx config
COPY client/nginx.conf /etc/nginx/conf.d/default.conf

# Copy built app
COPY --from=builder /app/dist /usr/share/nginx/html

# Create non-root user
RUN addgroup -g 1001 -S nginx && \
    adduser -S -u 1001 -G nginx nginx && \
    chown -R nginx:nginx /usr/share/nginx/html

USER nginx

EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
