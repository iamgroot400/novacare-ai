#!/usr/bin/env bash
# One-time setup of the shared EC2 box for NovaCare. Idempotent. Run as root on the server:
#   sudo bash setup-server.sh
# Touches Cake Uncle's Caddy config only to add one import line, validated and rolled back on error.
set -euo pipefail

echo "==> Docker"
if ! command -v docker >/dev/null; then
  apt-get update -qq
  DEBIAN_FRONTEND=noninteractive apt-get install -y -qq docker.io docker-compose-v2 docker-buildx >/dev/null
fi
# Cap container logs so they can't fill the disk.
if [ ! -f /etc/docker/daemon.json ]; then
  echo '{"log-driver": "json-file", "log-opts": {"max-size": "10m", "max-file": "3"}}' > /etc/docker/daemon.json
  systemctl restart docker
fi
systemctl enable --now docker >/dev/null 2>&1

echo "==> Directories"
install -d -m 700 /etc/novacare
install -d /etc/caddy/sites /opt/novacare
[ -f /etc/novacare/novacare.env ] || install -m 600 /dev/null /etc/novacare/novacare.env

echo "==> Caddy: import /etc/caddy/sites/*.caddy"
if ! grep -q '^import /etc/caddy/sites/\*\.caddy' /etc/caddy/Caddyfile; then
  cp -a /etc/caddy/Caddyfile /etc/caddy/Caddyfile.before-novacare
  printf '\n# Other sites on this server (e.g. NovaCare), one file each.\nimport /etc/caddy/sites/*.caddy\n' >> /etc/caddy/Caddyfile
  if caddy validate --config /etc/caddy/Caddyfile --adapter caddyfile >/dev/null 2>&1; then
    systemctl reload caddy
  else
    cp -a /etc/caddy/Caddyfile.before-novacare /etc/caddy/Caddyfile
    echo "Caddy rejected the import line; Caddyfile restored, Caddy untouched" >&2
    exit 1
  fi
fi

echo "==> Done. Fill /etc/novacare/novacare.env (see deploy/README.md), then run deploy/deploy.sh"
