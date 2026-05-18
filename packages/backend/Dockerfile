FROM node:20-alpine AS base
RUN corepack enable && corepack prepare pnpm@9 --activate

FROM base AS deps
WORKDIR /app
COPY pnpm-workspace.yaml pnpm-lock.yaml package.json ./
COPY packages/backend/package.json ./packages/backend/
COPY packages/db/package.json ./packages/db/
COPY packages/shared-types/package.json ./packages/shared-types/
COPY packages/ai-pipeline/package.json ./packages/ai-pipeline/
RUN pnpm install --frozen-lockfile

FROM base AS build
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY --from=deps /app/packages/backend/node_modules ./packages/backend/node_modules
COPY . .
RUN pnpm --filter @clearpath/shared-types build
RUN pnpm --filter @clearpath/db build
RUN pnpm --filter @clearpath/ai-pipeline build
RUN pnpm --filter @clearpath/backend build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=build /app/packages/backend/dist ./dist
COPY --from=build /app/packages/backend/package.json ./package.json
COPY --from=build /app/packages/db/dist ./node_modules/@clearpath/db/dist
COPY --from=build /app/packages/db/package.json ./node_modules/@clearpath/db/package.json
COPY --from=build /app/packages/shared-types/dist ./node_modules/@clearpath/shared-types/dist
COPY --from=build /app/packages/shared-types/package.json ./node_modules/@clearpath/shared-types/package.json
COPY --from=build /app/packages/ai-pipeline/dist ./node_modules/@clearpath/ai-pipeline/dist
COPY --from=build /app/packages/ai-pipeline/package.json ./node_modules/@clearpath/ai-pipeline/package.json
COPY --from=build /app/node_modules ./node_modules
EXPOSE 3001
CMD ["node", "dist/server.js"]
