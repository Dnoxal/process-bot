import logging
from collections import OrderedDict

import discord
from discord import app_commands
from discord.errors import PrivilegedIntentsRequired
from discord.ext import commands

from process_bot.config import get_settings
from process_bot.database import SessionLocal, init_db
from process_bot import schemas, services


logger = logging.getLogger(__name__)
settings = get_settings()

STAGE_CHOICES = [
    app_commands.Choice(name="Behavorial", value="behavioral"),
    app_commands.Choice(name="Onsite", value="onsite"),
    app_commands.Choice(name="Offer", value="offer"),
    app_commands.Choice(name="Reject", value="reject"),
]

def format_distribution(distribution: dict[str, int]) -> str:
    if not distribution:
        return "No data yet"
    ordered = OrderedDict(sorted(distribution.items(), key=lambda item: (-item[1], item[0])))
    return "\n".join(f"• {label.title()}: {count}" for label, count in ordered.items())


def channel_allowed(channel_id: int) -> bool:
    allowed_channels = settings.allowed_channel_ids
    return not allowed_channels or channel_id in allowed_channels


def build_bot() -> commands.Bot:
    intents = discord.Intents.default()
    bot = commands.Bot(command_prefix=settings.discord_command_prefix, intents=intents, help_command=None)

    @bot.event
    async def on_ready() -> None:
        init_db()
        try:
            if settings.discord_guild_id:
                guild = discord.Object(id=settings.discord_guild_id)
                bot.tree.copy_global_to(guild=guild)
                synced = await bot.tree.sync(guild=guild)
                logger.info("Synced %s guild commands for guild %s", len(synced), settings.discord_guild_id)
            else:
                synced = await bot.tree.sync()
                logger.info("Synced %s global commands", len(synced))
        except Exception:  # pragma: no cover
            logger.exception("Failed to sync application commands")
        logger.info("Logged in as %s", bot.user)

    @bot.tree.command(name="process", description="Log a recruiting process update")
    @app_commands.describe(company="Company name", stage="Recruiting stage")
    @app_commands.choices(stage=STAGE_CHOICES)
    async def process(
        interaction: discord.Interaction,
        company: str,
        stage: app_commands.Choice[str],
    ) -> None:
        if not interaction.channel or not channel_allowed(interaction.channel.id):
            await interaction.response.send_message(
                "This command is not enabled in this channel yet.",
                ephemeral=True,
            )
            return

        stored_stage = stage.value
        stored_outcome = None
        if stage.value == "offer":
            stored_stage = "final"
            stored_outcome = "offered"
        elif stage.value == "reject":
            stored_stage = "final"
            stored_outcome = "rejected"

        with SessionLocal() as session:
            payload = schemas.ProcessEventCreate(
                discord_user_id=str(interaction.user.id),
                username=str(interaction.user),
                company=company,
                stage=stored_stage,
                outcome=stored_outcome,
                discord_message_id=f"interaction:{interaction.id}",
                channel_id=str(interaction.channel.id),
                source_command=f"/process company={company} stage={stage.value}",
            )
            try:
                event = services.create_process_event(session, payload)
            except ValueError as exc:
                session.rollback()
                await interaction.response.send_message(str(exc), ephemeral=True)
                return
            session.commit()
            event_response = services.serialize_process_event(event)

        embed = discord.Embed(
            title="Process logged",
            color=discord.Color.brand_green(),
            description=f"Recorded **{event_response.company}** at **{stage.name}**.",
        )
        if event_response.outcome:
            embed.add_field(name="Recorded as", value=event_response.outcome.title(), inline=True)
        if event_response.recruiting_season:
            embed.add_field(name="Season", value=event_response.recruiting_season, inline=True)
        embed.set_footer(text="Saved privately for analytics and your history.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @bot.tree.command(name="myprocesses", description="View your most recent logged process updates")
    async def myprocesses(interaction: discord.Interaction) -> None:
        with SessionLocal() as session:
            events = services.list_user_processes(session, str(interaction.user.id))[:10]
        if not events:
            await interaction.response.send_message(
                "No processes logged yet. Try `/process` to add your first update.",
                ephemeral=True,
            )
            return

        lines = [
            f"`#{event.id}` {event.company} • {event.stage.title()}"
            + (f" • {event.outcome.title()}" if event.outcome else "")
            for event in events
        ]
        embed = discord.Embed(
            title="Your recent process updates",
            color=discord.Color.blurple(),
            description="\n".join(lines),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @bot.tree.command(name="companies", description="List tracked companies")
    async def companies(interaction: discord.Interaction) -> None:
        with SessionLocal() as session:
            results = services.list_companies(session)[:25]
        if not results:
            await interaction.response.send_message("No companies have been logged yet.", ephemeral=True)
            return
        embed = discord.Embed(
            title="Tracked companies",
            color=discord.Color.orange(),
            description="\n".join(f"• {company.name}" for company in results),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @bot.tree.command(name="stats", description="View recruiting stats for a company")
    @app_commands.describe(company="Exact tracked company name")
    async def stats(interaction: discord.Interaction, company: str) -> None:
        with SessionLocal() as session:
            company_record = services.find_company(session, company)
            stats_result = services.company_stats(session, company_record.slug) if company_record else None
        if not stats_result or not stats_result.total_events:
            await interaction.response.send_message(f"No stats yet for {company}.", ephemeral=True)
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
        embed.add_field(name="Outcomes", value=format_distribution(stats_result.outcome_distribution), inline=False)
        embed.set_footer(text="Use the web dashboard for full graphs and trend history.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @bot.tree.command(name="help", description="Show command help")
    async def help_command(interaction: discord.Interaction) -> None:
        embed = discord.Embed(
            title="Process Bot commands",
            color=discord.Color.light_grey(),
            description=(
                "`/process` log a company update\n"
                "`/myprocesses` view your recent entries\n"
                "`/companies` view tracked companies\n"
                "`/stats` inspect a company privately"
            ),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    return bot


async def run_bot() -> None:
    if not settings.discord_token:
        raise RuntimeError("DISCORD_TOKEN is required to run the bot.")
    bot = build_bot()
    try:
        await bot.start(settings.discord_token)
    except PrivilegedIntentsRequired as exc:
        raise RuntimeError(
            "Discord rejected the bot because a privileged intent is still enabled. "
            "This version uses slash commands and should not require Message Content Intent."
        ) from exc
