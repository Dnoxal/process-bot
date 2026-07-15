import logging
import time

import discord
from discord import app_commands
from discord import Message
from discord.errors import PrivilegedIntentsRequired
from discord.ext import commands

from process_bot.config import get_settings
from process_bot.database import SessionLocal, init_db
from process_bot import schemas, services
from process_bot.normalization import stage_display_name
from process_bot.parser import ParseError, parse_process_command
from process_bot.stats_card import build_company_stats_card


logger = logging.getLogger(__name__)
settings = get_settings()
STATS_CHANNEL_ID = 1526448010060365855
INVALID_PROCESS_NOTICE_COOLDOWN_SECONDS = 15 * 60
invalid_process_notice_sent_at: dict[int, float] = {}
PROCESS_CHANNEL_EMPLOYMENT_TYPES = {
    "process": "intern",
    "summer_2026_intern_process": "intern",
    "2026_summer_intern_process": "intern",
    "2027_summer_intern_process": "intern",
    "2026_grad_process": "full_time",
    "2027_grad_process": "full_time",
}
PROCESS_STAGE_EXAMPLES = (
    "`!process amazon oa`\n"
    "`!process stripe offer`\n"
    "`!process google technical r1 went well`"
)


def humanize_distribution_label(label: str) -> str:
    normalized = label.replace("_", " ").replace("-", " ")
    if normalized.lower() == "oa":
        return "OA"
    return normalized.title()


def format_distribution_bars(distribution: dict[str, int], *, max_rows: int = 6, bar_width: int = 14) -> str:
    if not distribution:
        return "No data yet"

    ordered = sorted(distribution.items(), key=lambda item: (-item[1], item[0]))[:max_rows]
    total = sum(distribution.values())
    if total <= 0:
        return "No data yet"

    lines = []
    for label, count in ordered:
        filled = round((count / total) * bar_width)
        bar = "#" * filled + "-" * (bar_width - filled)
        percent = round((count / total) * 100)
        lines.append(f"`{bar}` {humanize_distribution_label(label)} - {count} ({percent}%)")
    return "\n".join(lines)


def humanize_employment_type(employment_type: str) -> str:
    return employment_type.replace("_", " ").title()


def message_channel_allowed(channel: discord.abc.GuildChannel | discord.Thread | None) -> bool:
    allowed_channels = settings.allowed_channel_ids
    if not allowed_channels:
        return True
    channel_id = getattr(channel, "id", None)
    parent_id = getattr(channel, "parent_id", None)
    return channel_id in allowed_channels or parent_id in allowed_channels


def get_process_channel_employment_type(channel: discord.abc.GuildChannel | discord.Thread | None) -> str | None:
    channel_name = getattr(channel, "name", None)
    if not channel_name:
        return None
    return PROCESS_CHANNEL_EMPLOYMENT_TYPES.get(channel_name)


def can_manage_companies(member: discord.abc.User | discord.Member) -> bool:
    if member.id in settings.company_manager_user_ids:
        return True
    if not isinstance(member, discord.Member):
        return False
    return any(role.id in settings.company_manager_role_ids for role in member.roles)


def build_process_usage_message() -> str:
    return (
        "Use `!process <company> <stage> <optional notes>`.\n"
        "Stages: `oa` `behavioral` `technical` `offer` `rejection`\n"
        "Anything after the stage is treated as notes and ignored for logging.\n"
        "Examples:\n"
        f"{PROCESS_STAGE_EXAMPLES}"
    )


def build_invalid_process_message() -> str:
    return (
        "Couldn’t parse that `!process` command.\n"
        "Use `!process <company> <stage> <optional notes>`.\n"
        "Stages: `oa` `behavioral` `technical` `offer` `rejection`\n"
        "Anything after the stage is treated as notes and ignored for logging.\n"
        "Examples:\n"
        f"{PROCESS_STAGE_EXAMPLES}"
    )


def build_notice_embed(
    *,
    title: str,
    description: str,
    color: discord.Color | None = None,
) -> discord.Embed:
    return discord.Embed(
        title=title,
        description=description,
        color=color or discord.Color.blurple(),
    )


def build_process_usage_embed() -> discord.Embed:
    return build_notice_embed(
        title="Process Bot Format",
        description=build_process_usage_message(),
        color=discord.Color.orange(),
    )


def build_invalid_process_embed() -> discord.Embed:
    return build_notice_embed(
        title="Invalid Process Command",
        description=build_invalid_process_message(),
        color=discord.Color.red(),
    )


def build_offer_congratulations_embed(company_name: str) -> discord.Embed:
    return build_notice_embed(
        title="Offer Logged",
        description=f"Congratulations on the **{company_name}** offer! 🥂🎉",
        color=discord.Color.gold(),
    )


def build_company_stats_embed(stats_result: schemas.CompanyStatsResponse) -> discord.Embed:
    visible_outcomes = {
        label: count for label, count in stats_result.outcome_distribution.items() if label != "advanced"
    }
    embed = discord.Embed(
        title=f"{stats_result.company} Stats",
        color=discord.Color.brand_green(),
        description=(
            f"Tracked events: **{stats_result.total_events}**\n"
            f"Unique candidates: **{stats_result.total_candidates}**"
        ),
    )
    if stats_result.latest_activity:
        embed.add_field(
            name="Latest Activity",
            value=stats_result.latest_activity.strftime("%b %d, %Y"),
            inline=True,
        )
    embed.add_field(
        name="Stage Funnel",
        value=format_distribution_bars(stats_result.stage_distribution),
        inline=False,
    )
    embed.add_field(
        name="Outcome Mix",
        value=format_distribution_bars(visible_outcomes),
        inline=False,
    )
    return embed


def build_process_logged_embed(
    *,
    company_name: str,
    stage_name: str,
    employment_type_name: str,
    outcome: str | None,
    recruiting_season: str | None,
    alias_note: str | None = None,
) -> discord.Embed:
    description = f"Recorded **{company_name}** at **{stage_name}**."
    if alias_note:
        description = f"{description}\n{alias_note}"

    embed = discord.Embed(
        title="Process logged",
        color=discord.Color.brand_green(),
        description=description,
    )
    embed.add_field(name="Track", value=employment_type_name, inline=True)
    if outcome:
        embed.add_field(name="Recorded as", value=outcome.title(), inline=True)
    if recruiting_season:
        embed.add_field(name="Season", value=recruiting_season, inline=True)
    embed.set_footer(text="Saved privately for analytics and your history.")
    return embed


def build_stage_display_name(stage: str, outcome: str | None) -> str:
    if outcome in {"offered", "accepted"}:
        return "Offer"
    if outcome in {"rejected", "withdrawn"}:
        return "Rejection"
    return stage_display_name(stage)


def save_process_event(
    *,
    discord_user_id: str,
    username: str,
    company: str,
    stage: str,
    outcome: str | None,
    employment_type: str,
    discord_message_id: str,
    channel_id: str,
    source_command: str,
) -> schemas.ProcessEventResponse:
    with SessionLocal() as session:
        payload = schemas.ProcessEventCreate(
            discord_user_id=discord_user_id,
            username=username,
            company=company,
            stage=stage,
            outcome=outcome,
            employment_type=employment_type,
            discord_message_id=discord_message_id,
            channel_id=channel_id,
            source_command=source_command,
        )
        event = services.create_process_event(session, payload)
        session.commit()
        return services.serialize_process_event(event)


async def add_success_reaction(message: Message) -> None:
    try:
        await message.add_reaction("✅")
    except (discord.Forbidden, discord.HTTPException):
        logger.warning("Failed to add success reaction to message %s", message.id)


async def add_failure_reaction(message: Message) -> None:
    try:
        await message.add_reaction("❌")
    except (discord.Forbidden, discord.HTTPException):
        logger.warning("Failed to add failure reaction to message %s", message.id)


def should_send_invalid_process_notice(channel_id: int) -> bool:
    now = time.monotonic()
    last_sent_at = invalid_process_notice_sent_at.get(channel_id)
    if last_sent_at is not None and now - last_sent_at < INVALID_PROCESS_NOTICE_COOLDOWN_SECONDS:
        return False
    invalid_process_notice_sent_at[channel_id] = now
    return True


async def send_offer_congratulations(
    channel: discord.abc.Messageable,
    *,
    user_mention: str,
    company_name: str,
) -> None:
    try:
        await channel.send(
            content=user_mention,
            embed=build_offer_congratulations_embed(company_name),
        )
    except (discord.Forbidden, discord.HTTPException) as exc:
        logger.warning("Failed to send offer congratulations in channel: %s", exc)


class MessageAliasConfirmationView(discord.ui.View):
    def __init__(
        self,
        *,
        user_id: int,
        username: str,
        source_message: Message,
        message_id: int,
        channel_id: int,
        source_command: str,
        original_company: str,
        canonical_company: str,
        stage: str,
        outcome: str | None,
        employment_type: str,
    ) -> None:
        super().__init__(timeout=120)
        self.user_id = user_id
        self.username = username
        self.source_message = source_message
        self.message_id = message_id
        self.channel_id = channel_id
        self.source_command = source_command
        self.original_company = original_company
        self.canonical_company = canonical_company
        self.stage = stage
        self.outcome = outcome
        self.employment_type = employment_type

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                embed=build_notice_embed(
                    title="Not Your Buttons",
                    description="Only the original author can use these buttons.",
                    color=discord.Color.red(),
                ),
                ephemeral=True,
            )
            return False
        return True

    async def _log_company(
        self,
        interaction: discord.Interaction,
        *,
        company_name: str,
        alias_note: str | None,
    ) -> None:
        try:
            event_response = save_process_event(
                discord_user_id=str(self.user_id),
                username=self.username,
                company=company_name,
                stage=self.stage,
                outcome=self.outcome,
                employment_type=self.employment_type,
                discord_message_id=str(self.message_id),
                channel_id=str(self.channel_id),
                source_command=self.source_command,
            )
        except ValueError as exc:
            await interaction.response.send_message(
                embed=build_notice_embed(
                    title="Could Not Log Process",
                    description=str(exc),
                    color=discord.Color.red(),
                ),
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            embed=build_process_logged_embed(
                company_name=event_response.company,
                stage_name=build_stage_display_name(event_response.stage, event_response.outcome),
                employment_type_name=humanize_employment_type(event_response.employment_type or self.employment_type),
                outcome=event_response.outcome,
                recruiting_season=event_response.recruiting_season,
                alias_note=alias_note,
            ),
            ephemeral=True,
        )
        try:
            await interaction.message.delete()
        except (discord.Forbidden, discord.HTTPException) as exc:
            logger.warning("Failed to delete alias confirmation message %s: %s", interaction.message.id, exc)
        await add_success_reaction(self.source_message)
        if event_response.outcome == "offered" and interaction.channel:
            await send_offer_congratulations(
                interaction.channel,
                user_mention=f"<@{self.user_id}>",
                company_name=event_response.company,
            )

    @discord.ui.button(label="Use suggestion", style=discord.ButtonStyle.success, emoji="✅")
    async def use_suggestion(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        del button
        await self._log_company(
            interaction,
            company_name=self.canonical_company,
            alias_note=f"Logged under **{self.canonical_company}** from `{self.original_company}`.",
        )

    @discord.ui.button(label="Keep typed", style=discord.ButtonStyle.secondary, emoji="✖️")
    async def keep_typed(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        del button
        await self._log_company(
            interaction,
            company_name=self.original_company,
            alias_note=None,
        )


def build_bot() -> commands.Bot:
    intents = discord.Intents.default()
    intents.message_content = True
    bot = commands.Bot(command_prefix=settings.discord_command_prefix, intents=intents, help_command=None)

    @bot.event
    async def on_ready() -> None:
        init_db()
        try:
            if settings.discord_guild_id:
                guild = discord.Object(id=settings.discord_guild_id)
                synced = await bot.tree.sync(guild=guild)
                logger.info("Synced %s guild commands for guild %s", len(synced), settings.discord_guild_id)
            else:
                synced = await bot.tree.sync()
                logger.info("Synced %s global commands", len(synced))
        except Exception:  # pragma: no cover
            logger.exception("Failed to sync application commands")
        logger.info("Logged in as %s", bot.user)

    @bot.event
    async def on_message(message: Message) -> None:
        if message.author.bot:
            return
        if not message_channel_allowed(message.channel):
            return

        content = message.content.strip()
        if content.startswith("!stats"):
            if message.channel.id != STATS_CHANNEL_ID:
                return
            company = content[len("!stats") :].strip()
            if not company:
                await message.reply(
                    embed=build_notice_embed(
                        title="Stats Format",
                        description="Use `!stats <company>`.",
                        color=discord.Color.orange(),
                    ),
                    mention_author=False,
                )
                return

            with SessionLocal() as session:
                lookup_name = services.resolve_supported_company_name(session, company) or company
                company_record = services.find_company(session, lookup_name)
                stats_result = services.company_stats(session, company_record.slug) if company_record else None

            if not stats_result or not stats_result.total_events:
                await message.reply(
                    embed=build_notice_embed(
                        title="No Stats Yet",
                        description=f"No stats yet for **{lookup_name}**.",
                    ),
                    mention_author=False,
                )
                return

            stats_file_name = f"{stats_result.slug}-stats.png"
            try:
                stats_card = build_company_stats_card(stats_result)
                content = None
                if lookup_name != company:
                    content = f"Showing stats for **{stats_result.company}** from `{company}`."
                await message.reply(
                    content=content,
                    file=discord.File(stats_card, filename=stats_file_name),
                    mention_author=False,
                )
                return
            except Exception:  # pragma: no cover
                logger.exception("Failed to render stats card for %s", stats_result.slug)

            embed = build_company_stats_embed(stats_result)
            if lookup_name != company:
                embed.description = (
                    f"Showing stats for **{stats_result.company}** from `{company}`.\n\n"
                    f"{embed.description}"
                )
            await message.reply(embed=embed, mention_author=False)
            return

        employment_type = get_process_channel_employment_type(message.channel)
        if not employment_type:
            return

        if not isinstance(message.channel, (discord.TextChannel, discord.Thread)):
            return
        if not content.startswith("!process"):
            try:
                await message.delete()
            except (discord.Forbidden, discord.HTTPException) as exc:
                logger.warning(
                    "Failed to delete non-process message %s in channel %s: %s",
                    message.id,
                    message.channel.id,
                    exc,
                )
            await add_failure_reaction(message)
            if should_send_invalid_process_notice(message.channel.id):
                await message.channel.send(
                    content=message.author.mention,
                    embed=build_process_usage_embed(),
                )
            return

        command_body = content[len("!process") :].strip()
        try:
            parsed = parse_process_command(command_body)
        except ParseError:
            await add_failure_reaction(message)
            if should_send_invalid_process_notice(message.channel.id):
                await message.reply(embed=build_invalid_process_embed(), mention_author=False)
            return

        with SessionLocal() as session:
            company_name = services.resolve_supported_company_name(session, parsed.company)
        if not company_name:
            await add_failure_reaction(message)
            await message.reply(
                embed=build_notice_embed(
                    title="Unsupported Company",
                    description=(
                        f"`{parsed.company}` isn’t supported yet. "
                        "Use the accepted company name or ask a mod to add it."
                    ),
                    color=discord.Color.red(),
                ),
                mention_author=False,
            )
            return

        try:
            event_response = save_process_event(
                discord_user_id=str(message.author.id),
                username=str(message.author),
                company=company_name,
                stage=parsed.stage,
                outcome=parsed.outcome,
                employment_type=employment_type,
                discord_message_id=str(message.id),
                channel_id=str(message.channel.id),
                source_command=message.content,
            )
        except ValueError as exc:
            await add_failure_reaction(message)
            await message.reply(
                embed=build_notice_embed(
                    title="Could Not Log Process",
                    description=str(exc),
                    color=discord.Color.red(),
                ),
                mention_author=False,
            )
            return

        await add_success_reaction(message)
        if event_response.outcome == "offered":
            await send_offer_congratulations(
                message.channel,
                user_mention=message.author.mention,
                company_name=event_response.company,
            )

    @bot.tree.command(name="addcompany", description="Approve a new company for !process logging")
    @app_commands.describe(
        company="Canonical company name to approve",
        aliases="Optional comma-separated aliases such as jpmc, jp morgan",
    )
    async def addcompany(interaction: discord.Interaction, company: str, aliases: str | None = None) -> None:
        if not can_manage_companies(interaction.user):
            await interaction.response.send_message(
                embed=build_notice_embed(
                    title="Missing Role",
                    description="You do not have one of the configured company manager roles.",
                    color=discord.Color.red(),
                ),
                ephemeral=True,
            )
            return

        alias_values = [alias.strip() for alias in (aliases or "").split(",") if alias.strip()]
        with SessionLocal() as session:
            company_record = services.get_or_create_company(session, company)
            saved_aliases: list[str] = []
            for alias in alias_values:
                alias_record = services.create_company_alias(session, company_record.slug, alias)
                saved_aliases.append(alias_record.alias)
            session.commit()

        alias_summary = ", ".join(saved_aliases) if saved_aliases else "No aliases added."
        await interaction.response.send_message(
            embed=build_notice_embed(
                title="Company Approved",
                description=(
                    f"Approved **{company_record.name}** for `!process` logging.\n"
                    f"Aliases: {alias_summary}"
                ),
                color=discord.Color.brand_green(),
            ),
            ephemeral=True,
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
            "Discord rejected the bot because a privileged intent is still enabled. "
            "Enable Message Content Intent for the text-command workflow."
        ) from exc
