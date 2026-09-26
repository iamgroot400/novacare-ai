#!/usr/bin/env bash
# Deploy NovaCare to the shared EC2 box (it also runs Cake Uncle). Run from Git Bash in the repo:
#   bash deploy/deploy.sh
# Deploys the committed HEAD, not uncommitted changes. One-time server setup: deploy/README.md.
set -euo pipefail

HOST=${HOST:-ubuntu@3.108.65.106}
KEY=${KEY:-$HOME/.ssh/webserv.pem}
DOMAIN=${DOMAIN:-voice.aashikkhatri.com.np}
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

echo "==> Build, start, Caddy, health (one SSH session: ufw rate-limits new SSH connections)"
ssh_ 'sudo bash /opt/novacare/src/deploy/remote.sh'

curl -fsS -o /dev/null --max-time 15 "https://$DOMAIN/health" \
  && echo "public   ok: https://$DOMAIN/support" \
  || echo "public   not reachable yet: check DNS for $DOMAIN (A record -> server IP, not proxied)"
