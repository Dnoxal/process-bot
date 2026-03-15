# Process Bot MVP

Private Discord recruiting tracker for logging process updates and viewing lightweight analytics.

## What it does

- Discord commands for `!process`, `!myprocesses`, `!companies`, `!stats`, and `!help process`
- Structured parsing for commands like `!process amazon oa` and `!process google rejected phone`
- SQLite-backed storage by default, with SQLAlchemy models ready to swap to Postgres later
- FastAPI endpoints for companies, process events, and aggregate stats
- Built-in dashboard at `/` for a quick server-wide recruiting overview

## Quick start

1. Create a Discord bot in the Discord developer portal.
2. Copy `.env.example` to `.env` and fill in `DISCORD_TOKEN`.
3. Install dependencies:

   ```bash
   pip install -e .
   ```

4. Run the API and Discord bot together:

   ```bash
   python -m process_bot.app
   ```

5. Open [http://127.0.0.1:8000](http://127.0.0.1:8000).

If you set `DISCORD_GUILD_ID`, slash commands sync directly into that guild and usually appear quickly. Without it, commands sync globally and can take longer to show up.

## Commands

- `/process company:<name> stage:<stage> outcome:<optional>`
- `/myprocesses`
- `/companies`
- `/stats company:<name>`
- `/help`

Bot replies are ephemeral because the MVP now uses slash commands instead of prefix commands.

## API routes

- `GET /api/health`
- `GET /api/companies`
- `POST /api/companies`
- `POST /api/company-aliases`
- `GET /api/stats/global`
- `GET /api/stats/company/{slug}`
- `GET /api/stats/trends`
- `GET /api/me/processes?discord_user_id=<id>`
- `POST /api/process-events`
- `PATCH /api/process-events/{id}`
- `DELETE /api/process-events/{id}`
- `GET /api/admin/process-events`

## Notes

- `PROCESS_ALLOWED_CHANNEL_IDS` accepts a comma-separated list. Leave it blank to allow commands in any channel.
- The database defaults to `./data/process_bot.db`.
- This MVP keeps admin endpoints open because it is intended for a private server setup. Add auth before exposing it publicly.
