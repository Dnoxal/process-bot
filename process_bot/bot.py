import logging
from collections import OrderedDict

import discord
from discord.ext import commands
from discord.errors import PrivilegedIntentsRequired

from process_bot.config import get_settings
from process_bot.database import SessionLocal, init_db
from process_bot.parser import ParseError, parse_process_command
from process_bot import schemas, services


logger = logging.getLogger(__name__)
settings = get_settings()


def format_distribution(distribution: dict[str, int]) -> str:
    if not distribution:
        return "No data yet"
    ordered = OrderedDict(sorted(distribution.items(), key=lambda item: (-item[1], item[0])))
    return "\n".join(f"• {label.title()}: {count}" for label, count in ordered.items())


def build_bot() -> commands.Bot:
    intents = discord.Intents.default()
    intents.message_content = True

    bot = commands.Bot(command_prefix=settings.discord_command_prefix, intents=intents, help_command=None)

    def channel_allowed(channel_id: int) -> bool:
        allowed_channels = settings.allowed_channel_ids
        return not allowed_channels or channel_id in allowed_channels

    @bot.event
    async def on_ready() -> None:
        init_db()
        logger.info("Logged in as %s", bot.user)

    @bot.command(name="process")
    async def process(ctx: commands.Context, *, body: str) -> None:
        if not channel_allowed(ctx.channel.id):
            await ctx.reply("This command is not enabled in this channel yet.")
            return

        try:
            parsed = parse_process_command(body)
        except ParseError as exc:
            await ctx.reply(str(exc))
            return

        with SessionLocal() as session:
            payload = schemas.ProcessEventCreate(
                discord_user_id=str(ctx.author.id),
                username=str(ctx.author),
                company=parsed.company,
                stage=parsed.stage,
                outcome=parsed.outcome,
                discord_message_id=str(ctx.message.id),
                channel_id=str(ctx.channel.id),
                source_command=ctx.message.content,
            )
            try:
                event = services.create_process_event(session, payload)
            except ValueError as exc:
                session.rollback()
                await ctx.reply(str(exc))
                return
            session.commit()
            event_response = services.serialize_process_event(event)

        parts = [event_response.company, event_response.stage.title()]
        if event_response.outcome:
            parts.append(event_response.outcome.title())
        try:
            await ctx.message.add_reaction("✅")
        except discord.Forbidden:
            logger.warning("Missing permission to add reactions in channel %s", ctx.channel.id)
        await ctx.reply(f"Logged: {' - '.join(parts)}")

    @bot.command(name="myprocesses")
    async def myprocesses(ctx: commands.Context) -> None:
        with SessionLocal() as session:
            events = services.list_user_processes(session, str(ctx.author.id))[:10]
        if not events:
            await ctx.reply("No processes logged yet. Try `!process amazon oa`.")
            return
        lines = [
            f"`#{event.id}` {event.company} - {event.stage}"
            + (f" - {event.outcome}" if event.outcome else "")
            for event in events
        ]
        await ctx.reply("Your latest updates:\n" + "\n".join(lines))

    @bot.command(name="companies")
    async def companies(ctx: commands.Context) -> None:
        with SessionLocal() as session:
            results = services.list_companies(session)[:25]
        if not results:
            await ctx.reply("No companies have been logged yet.")
            return
        await ctx.reply("Tracked companies:\n" + "\n".join(f"- {company.name}" for company in results))

    @bot.command(name="stats")
    async def stats(ctx: commands.Context, *, company_name: str) -> None:
        with SessionLocal() as session:
            company = services.find_company(session, company_name)
            stats_result = services.company_stats(session, company.slug) if company else None
        if not stats_result or not stats_result.total_events:
            await ctx.reply(f"No stats yet for {company_name}.")
            return
        embed = discord.Embed(
            title=f"{stats_result.company} Recruiting Stats",
            color=discord.Color.brand_green(),
            description=(
                f"Tracked events: **{stats_result.total_events}**\n"
                f"Unique candidates: **{stats_result.total_candidates}**"
            ),
        )
        if stats_result.latest_activity:
            embed.add_field(
                name="Latest activity",
                value=stats_result.latest_activity.strftime("%b %d, %Y"),
                inline=True,
            )
        embed.add_field(name="Stages", value=format_distribution(stats_result.stage_distribution), inline=False)
        embed.add_field(
            name="Outcomes",
            value=format_distribution(stats_result.outcome_distribution),
            inline=False,
        )
        embed.set_footer(text="Use the web dashboard for searchable graphs and trend history.")
        await ctx.reply(embed=embed)

    @bot.command(name="help")
    async def help_command(ctx: commands.Context, topic: str | None = None) -> None:
        if topic == "process":
            await ctx.reply(
                "Use `!process <company> <stage>` or `!process <company> <outcome> <stage>`.\n"
                "Examples: `!process amazon oa`, `!process google rejected phone`, `!process stripe offer`."
            )
            return
        await ctx.reply(
            "Available commands: `!process`, `!myprocesses`, `!companies`, `!stats <company>`, `!help process`."
        )

    return bot


async def run_bot() -> None:
    if not settings.discord_token:
        raise RuntimeError("DISCORD_TOKEN is required to run the bot.")
    bot = build_bot()
    try:
        await bot.start(settings.discord_token)
    except PrivilegedIntentsRequired as exc:
        raise RuntimeError(
            "Discord rejected the bot because Message Content Intent is not enabled. "
            "Open https://discord.com/developers/applications -> your app -> Bot -> Privileged Gateway Intents "
            "and enable Message Content Intent, then restart `python -m process_bot.app`."
        ) from exc
