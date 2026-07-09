FROM node:20-alpine AS base

ENV PNPM_HOME=/pnpm
ENV PATH=$PNPM_HOME:$PATH

RUN corepack enable

WORKDIR /app

ARG INTERNAL_FERMENTATION_API_URL=http://fermentation:8000
ARG INTERNAL_WINERY_API_URL=http://winery:8001
ARG INTERNAL_FRUIT_ORIGIN_API_URL=http://fruit_origin:8002
ARG INTERNAL_ANALYSIS_API_URL=http://analysis_engine:8003

ENV INTERNAL_FERMENTATION_API_URL=$INTERNAL_FERMENTATION_API_URL
ENV INTERNAL_WINERY_API_URL=$INTERNAL_WINERY_API_URL
ENV INTERNAL_FRUIT_ORIGIN_API_URL=$INTERNAL_FRUIT_ORIGIN_API_URL
ENV INTERNAL_ANALYSIS_API_URL=$INTERNAL_ANALYSIS_API_URL

COPY package.json pnpm-workspace.yaml pnpm-lock.yaml turbo.json ./
COPY apps/web/package.json apps/web/package.json
COPY packages/shared/package.json packages/shared/package.json
COPY packages/ui/package.json packages/ui/package.json

RUN pnpm install --frozen-lockfile

COPY . .

RUN pnpm --filter @wine/web build

# Next standalone output does not include .next/static by default.
# Copy static/public assets into the standalone tree so browser chunk/css/font requests resolve.
RUN mkdir -p apps/web/.next/standalone/apps/web/.next/static \
	&& cp -R apps/web/.next/static/. apps/web/.next/standalone/apps/web/.next/static/ \
	&& if [ -d apps/web/public ]; then \
			 mkdir -p apps/web/.next/standalone/apps/web/public \
			 && cp -R apps/web/public/. apps/web/.next/standalone/apps/web/public/; \
		 fi

FROM node:20-alpine AS runner

ENV NODE_ENV=production
ENV PORT=3000
ENV PNPM_HOME=/pnpm
ENV PATH=$PNPM_HOME:$PATH

RUN corepack enable

WORKDIR /app

COPY --from=base /app /app

EXPOSE 3000

CMD ["node", "apps/web/.next/standalone/apps/web/server.js"]