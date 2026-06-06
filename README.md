# CSCD Process Bot

Private Discord recruiting tracker for logging process updates and viewing lightweight analytics. 

Bot for the largest computer science recruiting discord server.

## What it does

- Discord commands for `!process`, `!myprocesses`, `!companies`, `!stats`, and `!help process`
- Structured parsing for commands like `!process amazon oa` and `!process google rejected phone`
- SQLite-backed storage by default, with SQLAlchemy models ready to swap to Postgres later
- FastAPI endpoints for companies, process events, and aggregate stats
- Built-in dashboard at `/` for a quick server-wide recruiting overview

## Quick start

1. Create a Discord bot in the Discord developer portal.
2. Copy `.env.example` to `.env` and fill in `DISCORD_TOKEN`.
3. Set `PROCESS_API_TOKEN` if you plan to use protected API endpoints outside the Discord bot.
4. Install dependencies:

   ```bash
   pip install -e .
   ```

5. Run the API and Discord bot together:

   ```bash
   python -m process_bot.app
   ```

6. Open [http://127.0.0.1:8000](http://127.0.0.1:8000) or [http://localhost:8000](http://localhost:8000).

If the server is bound to `0.0.0.0`, that is the listen address, not the browser URL. Use `127.0.0.1` or `localhost` in your browser locally.

If you set `DISCORD_GUILD_ID`, slash commands sync directly into that guild and usually appear quickly. Without it, commands sync globally and can take longer to show up.

## Deployment

This repo includes a `render.yaml` that runs the dashboard API and Discord bot together in one process:

- build: `pip install -e . && npm install && npm run build`
- start: `python -m process_bot.app`
- database: managed Postgres via the `process-bot-db` blueprint resource

This means the deployed service will keep the FastAPI site up while also connecting the Discord bot, as long as `DISCORD_TOKEN` is configured in the deploy environment. Set `PROCESS_API_TOKEN` in production so protected API routes can be used intentionally without exposing writes/deletes to the public internet.

For Oracle Cloud Free Tier on a VM, use the deployment guide in [docs/oracle-free-tier.md](/Users/danielli/Documents/GitHub/process-bot/docs/oracle-free-tier.md) plus the sample files in [deploy/process-bot.service.example](/Users/danielli/Documents/GitHub/process-bot/deploy/process-bot.service.example) and [deploy/nginx.process-bot.conf.example](/Users/danielli/Documents/GitHub/process-bot/deploy/nginx.process-bot.conf.example).

## Commands

- `/process company:<name> stage:<stage> outcome:<optional>`
- `/myprocesses`
- `/companies`
- `/stats company:<name>`
- `/help`

Bot replies are ephemeral because the MVP now uses slash commands instead of prefix commands.

For legacy text logging with `!process`, the bot infers the employment track from the channel name. These channel names are recognized:

- `process` -> `intern`
- `summer_2026_intern_process` -> `intern`
- `2026_summer_intern_process` -> `intern`
- `2027_summer_intern_process` -> `intern`
- `2026_grad_process` -> `full_time`
- `2027_grad_process` -> `full_time`

## API routes

- `GET /api/health`
- `GET /api/companies` public when `PROCESS_PUBLIC_DASHBOARD=true`, otherwise requires `Authorization: Bearer <PROCESS_API_TOKEN>`
- `POST /api/companies` requires `Authorization: Bearer <PROCESS_API_TOKEN>`
- `POST /api/company-aliases` requires `Authorization: Bearer <PROCESS_API_TOKEN>`
- `GET /api/stats/global` requires `Authorization: Bearer <PROCESS_API_TOKEN>`
- `GET /api/stats/company/{slug}` requires `Authorization: Bearer <PROCESS_API_TOKEN>`
- `GET /api/stats/trends` requires `Authorization: Bearer <PROCESS_API_TOKEN>`
- `GET /api/dashboard/overview` public aggregate data when `PROCESS_PUBLIC_DASHBOARD=true`, otherwise requires `Authorization: Bearer <PROCESS_API_TOKEN>`
- `GET /api/dashboard/company/{slug}` public aggregate data when `PROCESS_PUBLIC_DASHBOARD=true`, otherwise requires `Authorization: Bearer <PROCESS_API_TOKEN>`
- `GET /api/me/processes?discord_user_id=<id>` requires `Authorization: Bearer <PROCESS_API_TOKEN>`
- `POST /api/process-events` requires `Authorization: Bearer <PROCESS_API_TOKEN>`
- `PATCH /api/process-events/{id}` requires `Authorization: Bearer <PROCESS_API_TOKEN>`
- `DELETE /api/process-events/{id}` requires `Authorization: Bearer <PROCESS_API_TOKEN>`
- `GET /api/admin/process-events` requires `Authorization: Bearer <PROCESS_API_TOKEN>`

## Notes

- `PROCESS_ALLOWED_CHANNEL_IDS` accepts a comma-separated list. Leave it blank to allow commands in any channel.
- `PROCESS_API_TOKEN` protects write, delete, admin, and user-specific HTTP API routes. Leave it unset only if those routes should be unusable.
- `PROCESS_PUBLIC_DASHBOARD` defaults to `true`. Set it to `false` only if the dashboard/API are behind proxy auth or you are okay with the browser dashboard failing unauthenticated API requests.
- The database defaults to `./data/process_bot.db`.
- Public dashboard endpoints expose aggregate company-level data only. User-specific process history stays token-protected and bot `/myprocesses` is scoped to the requesting Discord user.
- Later-stage logs only auto-backfill earlier stages that have already appeared for the same company and employment track. This avoids inventing OAs for companies whose process history does not show OAs.
