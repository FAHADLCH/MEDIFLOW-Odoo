#!/usr/bin/env bash
#
# MEDIFLOW by SA Systems — local test harness.
#
# Boots a local Odoo 18 instance with all MEDIFLOW modules mounted and the
# "mediflow" umbrella application installed.
#
# Open in your browser when ready:
#     http://localhost:8090/odoo?db=mediflow
#
# Default login (set on first run):
#     Email:    admin
#     Password: admin
#
set -euo pipefail

cd "$(dirname "$0")"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is not installed. Install Docker Desktop first: https://docs.docker.com/get-docker/"
  exit 1
fi

COMPOSE="docker compose -p mediflow"
if ! docker compose version >/dev/null 2>&1; then
  COMPOSE="docker-compose -p mediflow"
fi

DB="mediflow"
MODULE="mediflow"

case "${1:-up}" in
  up)
    echo "Starting Odoo 18 + Postgres (project: mediflow)..."
    $COMPOSE up -d
    echo
    echo "First boot creates the database. Tail logs with:"
    echo "    ./start-test.sh logs"
    echo
    echo "Then install MEDIFLOW with:"
    echo "    ./start-test.sh install"
    echo
    echo "When ready, open: http://localhost:8090/odoo?db=$DB  (admin / admin)"
    ;;
  install)
    # Create the database and install the MEDIFLOW umbrella (pulls in all modules).
    $COMPOSE exec -T odoo odoo -c /etc/odoo/odoo.conf -d "$DB" -i "$MODULE" --stop-after-init
    $COMPOSE restart odoo
    echo "Installed. Open: http://localhost:8090/odoo?db=$DB"
    ;;
  logs)
    $COMPOSE logs -f odoo
    ;;
  stop)
    $COMPOSE stop
    ;;
  restart)
    $COMPOSE restart odoo
    ;;
  update)
    # Apply XML/model changes without rebuilding the DB.
    $COMPOSE exec -T odoo odoo -c /etc/odoo/odoo.conf -d "$DB" -u "$MODULE" --stop-after-init
    $COMPOSE restart odoo
    ;;
  test)
    # Run the included unit tests against a fresh database.
    $COMPOSE exec -T odoo odoo -c /etc/odoo/odoo.conf -d mediflow_tests -i "$MODULE" \
      --test-enable --stop-after-init --log-level=test
    ;;
  reset)
    echo "WARNING: this deletes the database and uploaded files."
    read -r -p "Continue? (y/N) " ans
    [[ "$ans" == "y" || "$ans" == "Y" ]] || exit 0
    $COMPOSE down -v
    ;;
  tunnel)
    if ! command -v cloudflared >/dev/null 2>&1; then
      echo "cloudflared not installed. Install with: brew install cloudflared"
      exit 1
    fi
    echo "Exposing http://localhost:8090 via Cloudflare Tunnel..."
    echo "Share the *.trycloudflare.com URL it prints."
    cloudflared tunnel --url http://localhost:8090
    ;;
  *)
    echo "Usage: $0 {up|install|logs|stop|restart|update|test|reset|tunnel}"
    exit 1
    ;;
esac
