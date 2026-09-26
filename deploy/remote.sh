#!/usr/bin/env bash
# Server half of deploy/deploy.sh, run as root from /opt/novacare/src:  sudo bash deploy/remote.sh
# Everything happens in ONE SSH session on purpose: ufw rate-limits SSH on this box (6 new
# connections per 30 s), and fail2ban bans for an hour.
set -euo pipefail
cd "$(dirname "$0")/.."
COMPOSE="docker compose -f deploy/compose.server.yml"

# Record free memory during the builds, as evidence that Cake Uncle was never squeezed.
( while sleep 5; do free -m | awk '/Mem:/{print $7}'; done ) > /tmp/novacare-build-mem.log &
MEM_LOGGER=$!
trap 'kill $MEM_LOGGER 2>/dev/null || true' EXIT

echo "==> Backend + voice: build one at a time (keeps memory low)"
$COMPOSE build -q backend
$COMPOSE build -q voice
kill $MEM_LOGGER 2>/dev/null || true
echo "lowest RAM available during builds: $(sort -n /tmp/novacare-build-mem.log | head -1) MB"

echo "==> Start"
$COMPOSE up -d --remove-orphans
docker image prune -f >/dev/null

echo "==> Caddy site (whole config validated first: a broken config would take Cake Uncle down too)"
new=deploy/novacare.caddy
live=/etc/caddy/sites/novacare.caddy
if cmp -s "$new" "$live" 2>/dev/null; then
  echo "unchanged"
else
  if [ -f "$live" ]; then cp "$live" "$live.bak"; fi
  cp "$new" "$live"
  if caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile >/dev/null 2>&1; then
    systemctl reload caddy && echo "reloaded"
  else
    echo "Caddy config invalid; rolled back, Caddy untouched" >&2
    if [ -f "$live.bak" ]; then mv "$live.bak" "$live"; else rm "$live"; fi
    exit 1
  fi
fi

echo "==> Health"
for _ in $(seq 1 40); do
  [ "$(docker inspect -f '{{.State.Health.Status}}' novacare-voice-1 2>/dev/null)" = healthy ] && break
  sleep 3
done
check() { curl -fsS -o /dev/null --max-time 10 "$2" && echo "$1 ok" || echo "$1 FAILED"; }
check "backend " http://127.0.0.1:8100/health
check "voice   " http://127.0.0.1:8180/health
check "frontend" http://127.0.0.1:3100/
free -m | awk '/Mem:/{print "server RAM available now: " $7 " MB"}'
docker stats --no-stream --format '{{.Name}}: {{.MemUsage}}'
