#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENVIRONMENT="dev"
ACTION="up"
SERVICE=""
NO_BUILD=0

usage() {
  cat <<'EOF'
Usage:
  ./deploy.sh [options]

Options:
  -e, --env ENV         Target environment: dev | test | staging | prod (default: dev)
  -a, --action ACTION   up | down | destroy | migrate | logs | ps | build (default: up)
  -s, --service NAME    Optional service name for build/up/logs
      --no-build        Skip image rebuild on up
  -h, --help            Show this help

Examples:
  ./deploy.sh
  ./deploy.sh --env dev --action up
  ./deploy.sh --env dev --action logs --service fermentation
  ./deploy.sh --env staging --action up
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -e|--env)
      ENVIRONMENT="${2:-}"
      shift 2
      ;;
    -a|--action)
      ACTION="${2:-}"
      shift 2
      ;;
    -s|--service)
      SERVICE="${2:-}"
      shift 2
      ;;
    --no-build)
      NO_BUILD=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

ENV_FILE="${ROOT_DIR}/.env.${ENVIRONMENT}"
COMPOSE_BASE="${ROOT_DIR}/docker-compose.yml"
COMPOSE_ENV="${ROOT_DIR}/docker-compose.${ENVIRONMENT}.yml"

write_header() {
  printf '\n====================================================\n'
  printf '  %s\n' "$1"
  printf '====================================================\n\n'
}

write_step() {
  printf '  --> %s\n' "$1"
}

write_success() {
  printf '  [OK] %s\n' "$1"
}

write_fail() {
  printf '  [FAIL] %s\n' "$1" >&2
}

compose() {
  docker compose -f "$COMPOSE_BASE" -f "$COMPOSE_ENV" --env-file "$ENV_FILE" "$@"
}

write_header "Wine Fermentation System - Deploy [$ENVIRONMENT] / [$ACTION]"

if [[ ! -f "$ENV_FILE" ]]; then
  write_fail "Missing environment file: $ENV_FILE"
  printf '\n  Create it from the template:\n'
  printf '    cp .env.example %s\n' "$ENV_FILE"
  printf '  Then fill in real values.\n'
  exit 1
fi
write_step "Using env file : $ENV_FILE"

if [[ ! -f "$COMPOSE_ENV" ]]; then
  write_fail "Missing compose override: $COMPOSE_ENV"
  exit 1
fi
write_step "Compose files  : docker-compose.yml + docker-compose.${ENVIRONMENT}.yml"

if ! docker info >/dev/null 2>&1; then
  write_fail "Docker is not running. Please start Docker Desktop."
  exit 1
fi
write_success "Docker is running"

if [[ "$ENVIRONMENT" != "dev" ]]; then
  if grep -q "CHANGE_ME" "$ENV_FILE"; then
    printf '\n  [WARN] .env.%s still contains CHANGE_ME placeholders.\n' "$ENVIRONMENT"
    printf '         Replace all CHANGE_ME values before deploying to %s.\n' "$ENVIRONMENT"
    if [[ "$ENVIRONMENT" == "prod" ]]; then
      printf '\n  Aborting production deploy with placeholder secrets.\n'
      exit 1
    fi
    printf '\n'
  fi
fi

case "$ACTION" in
  build)
    write_step "Building images..."
    args=(build)
    if [[ -n "$SERVICE" ]]; then
      args+=("$SERVICE")
    fi
    compose "${args[@]}"
    write_success "Images built"
    ;;

  up)
    write_step "Starting stack (migrations run automatically via 'migrate' service)..."
    args=(up)
    if [[ "$NO_BUILD" -eq 0 ]]; then
      args+=(--build)
    fi
    args+=(--detach)
    if [[ -n "$SERVICE" ]]; then
      args+=("$SERVICE")
    fi
    compose "${args[@]}"
    write_success "Stack is up!"
    printf '\n  Services:\n'

    fermentation_port="$(grep -E '^FERMENTATION_HOST_PORT=' "$ENV_FILE" | cut -d= -f2 || true)"
    winery_port="$(grep -E '^WINERY_HOST_PORT=' "$ENV_FILE" | cut -d= -f2 || true)"
    db_port="$(grep -E '^POSTGRES_HOST_PORT=' "$ENV_FILE" | cut -d= -f2 || true)"
    web_port="$(grep -E '^WEB_HOST_PORT=' "$ENV_FILE" | cut -d= -f2 || true)"

    [[ -n "$fermentation_port" ]] && printf '    Fermentation API : http://localhost:%s\n' "$fermentation_port"
    [[ -n "$winery_port" ]] && printf '    Winery API       : http://localhost:%s\n' "$winery_port"
    [[ -n "$web_port" ]] && printf '    Web app          : http://localhost:%s\n' "$web_port"
    [[ -n "$db_port" ]] && printf '    PostgreSQL       : localhost:%s\n' "$db_port"

    printf '\n  Docs:\n'
    [[ -n "$fermentation_port" ]] && printf '    http://localhost:%s/docs\n' "$fermentation_port"
    [[ -n "$winery_port" ]] && printf '    http://localhost:%s/docs\n' "$winery_port"
    printf '\n  Tail logs : ./deploy.sh --env %s --action logs\n' "$ENVIRONMENT"
    printf '  Stop      : ./deploy.sh --env %s --action down\n' "$ENVIRONMENT"
    ;;

  migrate)
    write_step "Running Alembic migrations only..."
    compose run --rm migrate
    write_success "Migrations complete"
    ;;

  down)
    write_step "Stopping and removing containers (volumes preserved)..."
    compose down
    write_success "Stack stopped"
    ;;

  destroy)
    printf '\n  [WARNING] This will DELETE all containers AND database volumes.\n'
    read -r -p "  Type 'yes' to confirm: " confirm
    if [[ "$confirm" != "yes" ]]; then
      printf '  Cancelled.\n'
      exit 0
    fi
    write_step "Destroying stack and volumes..."
    compose down --volumes
    write_success "Stack and volumes destroyed"
    ;;

  logs)
    write_step "Tailing logs (Ctrl+C to stop)..."
    args=(logs --follow --tail=100)
    if [[ -n "$SERVICE" ]]; then
      args+=("$SERVICE")
    fi
    compose "${args[@]}"
    ;;

  ps)
    compose ps
    ;;

  *)
    write_fail "Unknown action: $ACTION"
    usage
    exit 1
    ;;
esac