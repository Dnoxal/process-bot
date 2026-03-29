import logging
from collections import OrderedDict

import discord
from discord import app_commands
from discord import Message
from discord.errors import PrivilegedIntentsRequired
from discord.ext import commands

from process_bot.config import get_settings
from process_bot.database import SessionLocal, init_db
from process_bot import schemas, services
from process_bot.parser import ParseError, parse_process_command


logger = logging.getLogger(__name__)
settings = get_settings()
PROCESS_CHANNEL_EMPLOYMENT_TYPES = {
    "summer_2026_intern_process": "intern",
    "2026_summer_intern_process": "intern",
    "2026_grad_process": "full_time",
}
PROCESS_STAGE_EXAMPLES = (
    "`!process amazon oa`\n"
    "`!process google behavioral`\n"
    "`!process stripe offer`\n"
    "`!process meta rejection`"
)

STAGE_CHOICES = [
    app_commands.Choice(name="OA", value="oa"),
    app_commands.Choice(name="Behavioral", value="behavioral"),
    app_commands.Choice(name="Technical", value="technical"),
    app_commands.Choice(name="Offer", value="offer"),
    app_commands.Choice(name="Reject", value="reject"),
]
EMPLOYMENT_TYPE_CHOICES = [
    app_commands.Choice(name="Intern", value="intern"),
    app_commands.Choice(name="Full Time", value="full_time"),
]


def format_distribution(distribution: dict[str, int]) -> str:
    if not distribution:
        return "No data yet"
    ordered = OrderedDict(sorted(distribution.items(), key=lambda item: (-item[1], item[0])))
    return "\n".join(f"• {label.title()}: {count}" for label, count in ordered.items())


def humanize_employment_type(employment_type: str) -> str:
    return employment_type.replace("_", " ").title()


def channel_allowed(channel_id: int) -> bool:
    allowed_channels = settings.allowed_channel_ids
    return not allowed_channels or channel_id in allowed_channels


def get_process_channel_employment_type(channel: discord.abc.GuildChannel | discord.Thread | None) -> str | None:
    channel_name = getattr(channel, "name", None)
    if not channel_name:
        return None
    return PROCESS_CHANNEL_EMPLOYMENT_TYPES.get(channel_name)


def build_process_usage_message() -> str:
    return (
        "Message removed. Use `!process <company> <stage>`.\n"
        "Stages: `oa` `behavioral` `technical` `offer` `rejection`\n"
        "Examples:\n"
        f"{PROCESS_STAGE_EXAMPLES}"
    )


def build_invalid_process_message() -> str:
    return (
        "Invalid `!process` format. Message kept, not logged.\n"
        "Use `!process <company> <stage>`.\n"
        "Stages: `oa` `behavioral` `technical` `offer` `rejection`\n"
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
    embed.add_field(name="Stages", value=format_distribution(stats_result.stage_distribution), inline=False)
    embed.add_field(name="Outcomes", value=format_distribution(visible_outcomes), inline=False)
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
    if outcome == "offered":
        return "Offer"
    if outcome == "rejected":
        return "Rejection"
    return stage.title()


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


async def company_name_autocomplete(
    interaction: discord.Interaction,
    current: str,
) -> list[app_commands.Choice[str]]:
    del interaction
    with SessionLocal() as session:
        companies = services.list_companies(session)

    current_lower = current.strip().lower()
    if current_lower:
        companies = [company for company in companies if current_lower in company.name.lower()]
    return [app_commands.Choice(name=company.name[:100], value=company.name) for company in companies[:25]]


class AliasConfirmationView(discord.ui.View):
    def __init__(
        self,
        *,
        user_id: int,
        original_company: str,
        canonical_company: str,
        alias_slug: str,
        stage_value: str,
        stage_name: str,
        employment_type_value: str,
        employment_type_name: str,
        channel_id: int,
        command_user_display: str,
    ) -> None:
        super().__init__(timeout=120)
        self.user_id = user_id
        self.original_company = original_company
        self.canonical_company = canonical_company
        self.alias_slug = alias_slug
        self.stage_value = stage_value
        self.stage_name = stage_name
        self.employment_type_value = employment_type_value
        self.employment_type_name = employment_type_name
        self.channel_id = channel_id
        self.command_user_display = command_user_display

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                embed=build_notice_embed(
                    title="Not Your Buttons",
                    description="Only the user who ran `/process` can use these buttons.",
                    color=discord.Color.red(),
                ),
                ephemeral=True,
            )
            return False
        return True

    async def _save_event(
        self,
        interaction: discord.Interaction,
        *,
        company_name: str,
    ) -> None:
        with SessionLocal() as session:
            payload = schemas.ProcessEventCreate(
                discord_user_id=str(interaction.user.id),
                username=self.command_user_display,
                company=company_name,
                stage=self.stage_value,
                outcome=None,
                employment_type=self.employment_type_value,
                discord_message_id=f"interaction:{interaction.id}",
                channel_id=str(self.channel_id),
                source_command=(
                    f"/process company={self.original_company} "
                    f"stage={self.stage_value} employment_type={self.employment_type_value}"
                ),
            )
            try:
                event = services.create_process_event(session, payload)
            except ValueError as exc:
                session.rollback()
                await interaction.response.edit_message(
                    content=None,
                    embed=build_notice_embed(
                        title="Could Not Log Process",
                        description=str(exc),
                        color=discord.Color.red(),
                    ),
                    view=None,
                )
                return

            session.commit()
            event_response = services.serialize_process_event(event)

        embed = build_process_logged_embed(
            company_name=event_response.company,
            stage_name=self.stage_name,
            employment_type_name=self.employment_type_name,
            outcome=event_response.outcome,
            recruiting_season=event_response.recruiting_season,
        )
        await interaction.response.edit_message(content=None, embed=embed, view=None)

    @discord.ui.button(label="Yes, use suggestion", style=discord.ButtonStyle.success, emoji="✅")
    async def use_suggestion(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        del button
        await self._save_event(interaction, company_name=self.canonical_company)

    @discord.ui.button(label="No, keep typed", style=discord.ButtonStyle.secondary, emoji="✏️")
    async def keep_typed(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        del button
        await self._save_event(interaction, company_name=self.original_company)


class StatsAliasConfirmationView(discord.ui.View):
    def __init__(self, *, user_id: int, original_company: str, canonical_company: str) -> None:
        super().__init__(timeout=120)
        self.user_id = user_id
        self.original_company = original_company
        self.canonical_company = canonical_company

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message(
                embed=build_notice_embed(
                    title="Not Your Buttons",
                    description="Only the user who ran `/stats` can use these buttons.",
                    color=discord.Color.red(),
                ),
                ephemeral=True,
            )
            return False
        return True

    async def _show_stats(self, interaction: discord.Interaction, company_name: str) -> None:
        with SessionLocal() as session:
            company_record = services.find_company(session, company_name)
            stats_result = services.company_stats(session, company_record.slug) if company_record else None
        if not stats_result or not stats_result.total_events:
            await interaction.response.edit_message(
                content=None,
                embed=build_notice_embed(
                    title="No Stats Yet",
                    description=f"No stats yet for **{company_name}**.",
                ),
                view=None,
            )
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
        await interaction.response.edit_message(content=None, embed=embed, view=None)

    @discord.ui.button(label="Yes, use suggestion", style=discord.ButtonStyle.success, emoji="✅")
    async def use_suggestion(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        del button
        await self._show_stats(interaction, self.canonical_company)

    @discord.ui.button(label="No, keep typed", style=discord.ButtonStyle.secondary, emoji="✏️")
    async def keep_typed(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        del button
        await self._show_stats(interaction, self.original_company)


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
                bot.tree.copy_global_to(guild=guild)
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

        content = message.content.strip()
        if content.startswith("!stats"):
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
                suggestion = services.suggest_company_from_alias(session, company)
                lookup_name = suggestion.canonical_name if suggestion else company
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

            embed = build_company_stats_embed(stats_result)
            if suggestion:
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
            await message.channel.send(
                content=message.author.mention,
                embed=build_process_usage_embed(),
            )
            return

        command_body = content[len("!process") :].strip()
        try:
            parsed = parse_process_command(command_body)
        except ParseError:
            await message.reply(embed=build_invalid_process_embed(), mention_author=False)
            return

        with SessionLocal() as session:
            suggestion = services.suggest_company_from_alias(session, parsed.company)
        if suggestion:
            embed = discord.Embed(
                title=f"Did you mean {suggestion.canonical_name}?",
                color=discord.Color.gold(),
                description="✅ use suggestion\n✖️ keep typed",
            )
            embed.set_footer(text="Only the original author can use these buttons.")
            await message.reply(
                embed=embed,
                view=MessageAliasConfirmationView(
                    user_id=message.author.id,
                    username=str(message.author),
                    source_message=message,
                    message_id=message.id,
                    channel_id=message.channel.id,
                    source_command=message.content,
                    original_company=parsed.company,
                    canonical_company=suggestion.canonical_name,
                    stage=parsed.stage,
                    outcome=parsed.outcome,
                    employment_type=employment_type,
                ),
                mention_author=False,
            )
            return

        try:
            event_response = save_process_event(
                discord_user_id=str(message.author.id),
                username=str(message.author),
                company=parsed.company,
                stage=parsed.stage,
                outcome=parsed.outcome,
                employment_type=employment_type,
                discord_message_id=str(message.id),
                channel_id=str(message.channel.id),
                source_command=message.content,
            )
        except ValueError as exc:
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

    @bot.tree.command(name="process", description="Log a recruiting process update")
    @app_commands.describe(company="Company name", stage="Recruiting stage", employment_type="Intern or full time")
    @app_commands.choices(stage=STAGE_CHOICES, employment_type=EMPLOYMENT_TYPE_CHOICES)
    @app_commands.autocomplete(company=company_name_autocomplete)
    async def process(
        interaction: discord.Interaction,
        company: str,
        stage: app_commands.Choice[str],
        employment_type: app_commands.Choice[str],
    ) -> None:
        del company, stage, employment_type
        await interaction.response.send_message(
            embed=build_notice_embed(
                title="Use Text Command",
                description=(
                    "Use `!process <company> <stage>` in `summer_2026_intern_process` "
                    "or `2026_grad_process`.\nThe channel decides intern vs full time."
                ),
            ),
            ephemeral=True,
        )

    @bot.tree.command(name="myprocesses", description="View your most recent logged process updates")
    async def myprocesses(interaction: discord.Interaction) -> None:
        with SessionLocal() as session:
            events = services.list_user_processes(session, str(interaction.user.id))[:10]
        if not events:
            await interaction.response.send_message(
                embed=build_notice_embed(
                    title="No Processes Yet",
                    description="Try `!process <company> <stage>` in one of the 2026 process channels.",
                ),
                ephemeral=True,
            )
            return

        lines = [
            f"`#{event.id}` {event.company} • {event.stage.title()}"
            + (f" • {humanize_employment_type(event.employment_type)}" if event.employment_type else "")
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
            await interaction.response.send_message(
                embed=build_notice_embed(
                    title="No Companies Yet",
                    description="No companies have been logged yet.",
                ),
                ephemeral=True,
            )
            return
        embed = discord.Embed(
            title="Tracked companies",
            color=discord.Color.orange(),
            description="\n".join(f"• {company.name}" for company in results),
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @bot.tree.command(name="stats", description="View recruiting stats for a company")
    @app_commands.describe(company="Exact tracked company name")
    @app_commands.autocomplete(company=company_name_autocomplete)
    async def stats(interaction: discord.Interaction, company: str) -> None:
        with SessionLocal() as session:
            suggestion = services.suggest_company_from_alias(session, company)
            company_record = services.find_company(session, company)
            stats_result = services.company_stats(session, company_record.slug) if company_record else None
        if suggestion:
            prompt_embed = discord.Embed(
                title=f"Did you mean {suggestion.canonical_name}?",
                color=discord.Color.gold(),
                description=(
                    f"You entered **{company}**.\n"
                    "If yes, I will show stats for the suggested company. If not, I will keep the name exactly as typed."
                ),
            )
            prompt_embed.set_footer(text="Only you can see and interact with this message.")
            view = StatsAliasConfirmationView(
                user_id=interaction.user.id,
                original_company=company,
                canonical_company=suggestion.canonical_name,
            )
            await interaction.response.send_message(embed=prompt_embed, view=view, ephemeral=True)
            return
        if not stats_result or not stats_result.total_events:
            await interaction.response.send_message(
                embed=build_notice_embed(
                    title="No Stats Yet",
                    description=f"No stats yet for **{company}**.",
                ),
                ephemeral=True,
            )
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
                "`!process <company> <stage>` log in the 2026 process channels\n"
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
            "Enable Message Content Intent for the text-command workflow."
        ) from exc
