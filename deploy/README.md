# Deploying NovaCare (shared EC2 box)

NovaCare runs on the same AWS EC2 instance as Cake Uncle (t3.small, 2 GB RAM, Ubuntu,
`ubuntu@3.108.65.106`), at **https://voice.aashikkhatri.com.np**.

```
Internet ─► Caddy :443 (shared with Cake Uncle)
             ├─ /voice/*        ─► voice     127.0.0.1:8180  (host network, for WebRTC UDP)
             ├─ /api/*, /health ─► backend   127.0.0.1:8100
             └─ everything else ─► frontend  127.0.0.1:3100
```

## Keeping Cake Uncle safe

- Containers listen on 127.0.0.1 only; Caddy is the single public entry point.
- Memory caps (backend 448 MB, voice 640 MB, frontend 256 MB) with swap disabled per
  container: if NovaCare runs out, the kernel kills a NovaCare container, never Cake Uncle.
- CPU caps so a long voice call can't starve Cake Uncle.
- The frontend is built on the laptop (`next build` needs >1 GB RAM); backend and voice
  are built on the server one at a time.
- Caddy config is validated before every reload and rolled back if invalid.

## One-time setup (done 2026-09-26)

1. `deploy/setup-server.sh` (as root): installs Docker with log rotation, creates
   `/etc/novacare` and `/etc/caddy/sites`, and adds `import /etc/caddy/sites/*.caddy`
   to Cake Uncle's Caddyfile (backup at `/etc/caddy/Caddyfile.before-novacare`).
2. `/etc/novacare/novacare.env` (root, mode 600): `GROQ_API_KEY`, public URLs,
   `CALL_API_TOKEN`, optional `TWILIO_*`. Never commit it.
3. DNS: `voice.aashikkhatri.com.np` A record → the server IP, **DNS only** (not proxied by
   Cloudflare), so Caddy can get its own certificate like Cake Uncle's sites.

## Deploy

```bash
bash deploy/deploy.sh
```

It deploys the **committed HEAD**: builds and uploads the frontend image, uploads the
source, then runs `deploy/remote.sh` on the server (build backend and voice, restart,
install the Caddy site, health check). Environment overrides: `HOST`, `KEY`, `DOMAIN`.

The server's `ufw` rate-limits SSH (6 new connections per 30 s) and fail2ban bans for an
hour, so keep server work to as few SSH sessions as possible; don't poll it over SSH in a loop.

## Operate

```bash
ssh -i ~/.ssh/webserv.pem ubuntu@3.108.65.106
cd /opt/novacare/src
sudo docker compose -f deploy/compose.server.yml ps
sudo docker compose -f deploy/compose.server.yml logs -f --tail=100 voice backend
sudo docker stats --no-stream
```

## Full-duplex voice (WebRTC)

WebRTC audio is UDP on random ports, which both the AWS security group and `ufw` block by
default. Until they're opened, browser calls fall back to push-to-talk (which works over
HTTPS). To enable full duplex, allow inbound UDP 32768-60999 in the security group and run
`sudo ufw allow 32768:60999/udp`.
