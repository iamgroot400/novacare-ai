# Deploying NovaCare (shared EC2 box)

NovaCare runs on the same AWS EC2 instance as Cake Uncle (t3.small, 2 GB RAM, Ubuntu,
`ubuntu@3.108.65.106`), at **https://voice.aashikkhatri.com.np**.

```
Internet ─► Caddy :443 (shared with Cake Uncle)
             ├─ /voice/*        ─► voice     127.0.0.1:8180  (calls are websockets: no UDP needed)
             ├─ /api/*, /health ─► backend   127.0.0.1:8100
             └─ everything else ─► frontend  127.0.0.1:3100
```

## Keeping Cake Uncle safe

- Containers listen on 127.0.0.1 only; Caddy is the single public entry point.
- Memory caps (backend 576 MB, voice 576 MB, frontend 192 MB; 1.3 GB total) with swap disabled per
  container: if NovaCare runs out, the kernel kills a NovaCare container, never Cake Uncle.
- CPU caps so a long voice call can't starve Cake Uncle.
- The frontend is built on the laptop (`next build` needs >1 GB RAM); backend and voice
  are built on the server one at a time.
- Caddy config is validated as the `caddy` user before every reload and rolled back if
  validation or the reload fails. Site files must be mode 644 (this server's umask makes
  new files root-only, which once blocked a reload).

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

## Calls

Browser calls (`/voice/api/voice/ws`) and Twilio phone calls are plain websockets through
Caddy on 443, so no extra ports or firewall rules are needed.
