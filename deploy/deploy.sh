#!/usr/bin/env bash
# Deploy NovaCare to the shared EC2 box (it also runs Cake Uncle). Run from Git Bash in the repo:
#   bash deploy/deploy.sh
# Deploys the committed HEAD, not uncommitted changes. One-time server setup: deploy/README.md.
set -euo pipefail

HOST=${HOST:-ubuntu@3.108.65.106}
KEY=${KEY:-$HOME/.ssh/webserv.pem}
DOMAIN=${DOMAIN:-voice.aashikkhatri.com.np}
COMPOSE="sudo docker compose -f deploy/compose.server.yml"
ssh_() { ssh -i "$KEY" -o BatchMode=yes -o ConnectTimeout=15 "$HOST" "$@"; }

cd "$(dirname "$0")/.."
git diff --quiet HEAD -- || echo "WARNING: uncommitted changes are NOT deployed (only HEAD is)."

echo "==> Frontend: build locally (next build needs more RAM than the server can spare) and upload"
docker build -q -f docker/frontend.Dockerfile \
  --build-arg NEXT_PUBLIC_API_URL="https://$DOMAIN" \
  --build-arg NEXT_PUBLIC_VOICE_URL="https://$DOMAIN/voice" \
  -t novacare-frontend .
docker save novacare-frontend | gzip | ssh_ 'gunzip | sudo docker load -q'

echo "==> Source: upload HEAD to /opt/novacare/src"
git archive --format=tar HEAD | ssh_ 'set -e
  sudo rm -rf /opt/novacare/src.new && sudo mkdir -p /opt/novacare/src.new
  sudo tar -x -C /opt/novacare/src.new
  sudo rm -rf /opt/novacare/src && sudo mv /opt/novacare/src.new /opt/novacare/src'

echo "==> Backend + voice: build on the server, one at a time (keeps memory low)"
ssh_ "cd /opt/novacare/src && $COMPOSE build -q backend && $COMPOSE build -q voice"

echo "==> Start"
ssh_ "cd /opt/novacare/src && $COMPOSE up -d --remove-orphans && sudo docker image prune -f >/dev/null"

echo "==> Caddy site (whole config validated first: a broken config would take Cake Uncle down too)"
ssh_ 'sudo tee /etc/caddy/sites/novacare.caddy.new >/dev/null' < deploy/novacare.caddy
ssh_ 'set -e; cd /etc/caddy/sites
  if sudo cmp -s novacare.caddy.new novacare.caddy 2>/dev/null; then sudo rm novacare.caddy.new; echo "unchanged"; exit 0; fi
  if [ -f novacare.caddy ]; then sudo cp novacare.caddy novacare.caddy.bak; fi
  sudo mv novacare.caddy.new novacare.caddy
  if sudo caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile >/dev/null 2>&1; then
    sudo systemctl reload caddy && echo "reloaded"
  else
    echo "Caddy config invalid; rolled back, Caddy untouched" >&2
    if [ -f novacare.caddy.bak ]; then sudo mv novacare.caddy.bak novacare.caddy; else sudo rm novacare.caddy; fi
    exit 1
  fi'

echo "==> Health"
ssh_ 'for i in $(seq 1 30); do
    s=$(sudo docker inspect -f "{{.State.Health.Status}}" novacare-voice-1 2>/dev/null || true)
    [ "$s" = healthy ] && break; sleep 3; done
  curl -fsS -o /dev/null http://127.0.0.1:8100/health && echo "backend  ok" || echo "backend  FAILED"
  curl -fsS -o /dev/null http://127.0.0.1:8180/health && echo "voice    ok" || echo "voice    FAILED"
  curl -fsS -o /dev/null http://127.0.0.1:3100/      && echo "frontend ok" || echo "frontend FAILED"
  free -m | awk "/Mem:/{print \"server RAM available: \" \$7 \" MB\"}"'
curl -fsS -o /dev/null --max-time 15 "https://$DOMAIN/health" \
  && echo "public   ok: https://$DOMAIN/support" \
  || echo "public   not reachable yet: check DNS for $DOMAIN (A record -> server IP, not proxied)"
