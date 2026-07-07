# DigitalOcean Droplet Deployment

This app runs well on a small DigitalOcean Ubuntu Droplet because it is a single Python process that serves the FastAPI dashboard and connects the Discord bot at the same time.

## Recommended shape

- Compute: Basic Droplet, 1 GB RAM or larger
- OS: Ubuntu 22.04 or 24.04
- Public ports: `22`, `80`, `443`
- Keep the app itself on `127.0.0.1:8000`
- Put `nginx` in front if you want a public dashboard URL

## Why this repo is Droplet-friendly

- Runtime only needs Python 3.10+
- The built frontend is already committed under `process_bot/static/app`
- SQLite works out of the box for a private server setup

If you later expect more writes or want easier backups, move `DATABASE_URL` to Postgres.

## 1. Create the VM

Create an Ubuntu Droplet in DigitalOcean and allow inbound traffic for:

- TCP `22` for SSH
- TCP `80` for HTTP
- TCP `443` for HTTPS

If DigitalOcean Cloud Firewall rules are open but the Droplet still does not respond, also check Ubuntu's firewall:

```bash
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
```

## 2. Install system packages

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git nginx
```

## 3. Clone and install the app

```bash
git clone https://github.com/YOUR-USER/YOUR-REPO.git
cd process-bot
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .
mkdir -p data
```

## 4. Configure environment variables

Copy the sample env file and fill in your values:

```bash
cp .env.example .env
```

Minimum values:

```env
DISCORD_TOKEN=your-bot-token
DISCORD_GUILD_ID=your-test-guild-id
API_HOST=127.0.0.1
API_PORT=8000
DATABASE_URL=sqlite:////home/ubuntu/process-bot/data/process_bot.db
PROCESS_ALLOWED_CHANNEL_IDS=
```

Notes:

- Use `API_HOST=127.0.0.1` when `nginx` is proxying traffic
- `DISCORD_GUILD_ID` is optional; if set, startup clears stale guild application commands
- The SQLite path above is absolute so the service keeps using the same database no matter how it starts

## 5. Test it manually

```bash
source .venv/bin/activate
python -m process_bot.app
```

Then from the VM:

```bash
curl http://127.0.0.1:8000/api/health
```

You should get:

```json
{"status":"ok"}
```

Stop the process after that test.

## 6. Run it with systemd

Adjust the paths and user in `deploy/process-bot.service.example`, then install it:

```bash
sudo cp deploy/process-bot.service.example /etc/systemd/system/process-bot.service
sudo systemctl daemon-reload
sudo systemctl enable process-bot
sudo systemctl start process-bot
sudo systemctl status process-bot
```

Useful logs:

```bash
journalctl -u process-bot -f
```

## 7. Put nginx in front

Install the sample config:

```bash
sudo cp deploy/nginx.process-bot.conf.example /etc/nginx/sites-available/process-bot
sudo ln -s /etc/nginx/sites-available/process-bot /etc/nginx/sites-enabled/process-bot
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

At this point, visiting your VM public IP in a browser should load the dashboard.

## 8. Optional HTTPS

If you point a domain at the VM, add TLS with Certbot:

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

## Updating later

```bash
cd ~/process-bot
git pull
source .venv/bin/activate
pip install -e .
sudo systemctl restart process-bot
```

If the frontend changes and you want a fresh build on the server, also install Node and run `npm install && npm run build`. For this repo as it stands today, that is not required for first deploy because the built assets are already checked in.

## Troubleshooting

### Bot is offline but the website works

- Check `DISCORD_TOKEN`
- Check `journalctl -u process-bot -f`
- Make sure the bot has been invited to the server with bot permissions

### Website does not load from the public IP

- Confirm your DigitalOcean Cloud Firewall allows `80` and `443`
- Confirm `nginx` is running: `systemctl status nginx`
- Confirm the app is healthy on the VM: `curl http://127.0.0.1:8000/api/health`

### Data disappeared after redeploy

- Make sure `DATABASE_URL` points to a persistent path such as `/home/ubuntu/process-bot/data/process_bot.db`
- Avoid temporary directories
