FROM node:20-alpine AS base

# ── Install deps ──────────────────────────────────────
FROM base AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

# ── Build ─────────────────────────────────────────────
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

# ── Production ────────────────────────────────────────
FROM base AS runner
WORKDIR /app
ENV NODE_ENV=production

RUN addgroup --system --gid 1001 nodejs \
 && adduser --system --uid 1001 nestjs

# Compiled app
COPY --from=builder --chown=nestjs:nodejs /app/dist ./dist

# Static frontend served by Express
COPY --from=builder --chown=nestjs:nodejs /app/public ./public

# Sponsor JSON data (versioned, committed to git)
COPY --from=builder --chown=nestjs:nodejs /app/data ./data

USER nestjs
EXPOSE 3000
CMD ["node", "dist/main"]
