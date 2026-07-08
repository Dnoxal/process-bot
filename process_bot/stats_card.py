from __future__ import annotations

from io import BytesIO

from PIL import Image, ImageDraw, ImageFont

from process_bot import schemas
from process_bot.normalization import PROCESS_STAGE_ORDER, ordered_process_distribution, stage_display_name


WIDTH = 1200
HEIGHT = 820
BACKGROUND = (244, 247, 251)
PANEL = (255, 255, 255)
TEXT = (25, 32, 44)
MUTED = (99, 112, 133)
SUBTLE = (226, 232, 240)
TRACK = (235, 240, 247)
GREEN = (25, 135, 84)
BLUE = (37, 99, 235)
AMBER = (217, 119, 6)
RED = (220, 38, 38)
INK = (17, 24, 39)


def _font(size: int, *, bold: bool = False) -> ImageFont.ImageFont:
    names = (
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    )
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _draw_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    *,
    font: ImageFont.ImageFont,
    fill: tuple[int, int, int] = TEXT,
) -> None:
    draw.text(xy, text, font=font, fill=fill)


def _draw_fit_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    *,
    max_width: int,
    size: int,
    fill: tuple[int, int, int] = TEXT,
    bold: bool = False,
    min_size: int = 14,
) -> None:
    font = _font(size, bold=bold)
    while size > min_size and draw.textlength(text, font=font) > max_width:
        size -= 1
        font = _font(size, bold=bold)
    draw.text(xy, text, font=font, fill=fill)


def _draw_right_text(
    draw: ImageDraw.ImageDraw,
    right_x: int,
    y: int,
    text: str,
    *,
    font: ImageFont.ImageFont,
    fill: tuple[int, int, int] = TEXT,
) -> None:
    text_width = int(draw.textlength(text, font=font))
    draw.text((right_x - text_width, y), text, font=font, fill=fill)


def _draw_metric(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    label: str,
    value: str,
    accent: tuple[int, int, int],
) -> None:
    draw.rounded_rectangle(box, radius=16, fill=PANEL, outline=SUBTLE, width=1)
    x1, y1, _, _ = box
    draw.rounded_rectangle((x1 + 22, y1 + 22, x1 + 30, y1 + 86), radius=4, fill=accent)
    _draw_text(draw, (x1 + 48, y1 + 22), label.upper(), font=_font(17, bold=True), fill=MUTED)
    _draw_text(draw, (x1 + 48, y1 + 52), value, font=_font(40, bold=True), fill=TEXT)


def _draw_process_activity(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    distribution: dict[str, int],
) -> None:
    draw.rounded_rectangle(box, radius=18, fill=PANEL, outline=SUBTLE, width=1)
    x1, y1, x2, _ = box
    _draw_text(draw, (x1 + 30, y1 + 26), "Process Activity", font=_font(31, bold=True), fill=TEXT)
    _draw_text(draw, (x1 + 32, y1 + 68), "Grouped as OA -> Behavioral -> Technical -> Offer", font=_font(19), fill=MUTED)

    ordered = ordered_process_distribution(distribution)
    max_count = max(ordered.values(), default=0)
    bar_left = x1 + 36
    bar_right = x2 - 112
    bar_width = bar_right - bar_left
    y = y1 + 128
    for stage in PROCESS_STAGE_ORDER:
        count = ordered.get(stage, 0)
        label = stage_display_name(stage)
        _draw_text(draw, (bar_left, y), label, font=_font(23, bold=True), fill=INK)
        _draw_right_text(draw, x2 - 36, y + 1, str(count), font=_font(23, bold=True), fill=INK)
        track_y = y + 38
        draw.rounded_rectangle((bar_left, track_y, bar_left + bar_width, track_y + 22), radius=11, fill=TRACK)
        if max_count and count:
            fill_width = round(bar_width * (count / max_count))
            fill_width = max(12, fill_width)
            draw.rounded_rectangle((bar_left, track_y, bar_left + fill_width, track_y + 22), radius=11, fill=BLUE)
        y += 76


def _draw_outcome_mix(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    distribution: dict[str, int],
) -> None:
    draw.rounded_rectangle(box, radius=18, fill=PANEL, outline=SUBTLE, width=1)
    x1, y1, x2, _ = box
    _draw_text(draw, (x1 + 30, y1 + 26), "Outcomes", font=_font(31, bold=True), fill=TEXT)
    _draw_fit_text(
        draw,
        (x1 + 32, y1 + 68),
        "Final results logged",
        max_width=x2 - x1 - 64,
        size=19,
        fill=MUTED,
    )

    offered = distribution.get("offered", 0) + distribution.get("accepted", 0)
    rejected = distribution.get("rejected", 0) + distribution.get("withdrawn", 0)
    total = offered + rejected
    rows = (("Offers", offered, GREEN), ("Rejections", rejected, RED))

    y = y1 + 136
    for label, count, color in rows:
        percent = round((count / total) * 100) if total else 0
        draw.rounded_rectangle((x1 + 30, y, x2 - 30, y + 92), radius=14, fill=(248, 250, 252), outline=SUBTLE)
        draw.ellipse((x1 + 54, y + 30, x1 + 82, y + 58), fill=color)
        _draw_text(draw, (x1 + 102, y + 22), label, font=_font(24, bold=True), fill=INK)
        _draw_text(draw, (x1 + 102, y + 54), f"{percent}% of outcomes", font=_font(18), fill=MUTED)
        _draw_right_text(draw, x2 - 54, y + 27, str(count), font=_font(36, bold=True), fill=INK)
        y += 116


def build_company_stats_card(stats_result: schemas.CompanyStatsResponse) -> BytesIO:
    image = Image.new("RGB", (WIDTH, HEIGHT), BACKGROUND)
    draw = ImageDraw.Draw(image)

    _draw_text(draw, (58, 42), f"{stats_result.company} Stats", font=_font(54, bold=True), fill=TEXT)
    _draw_text(draw, (62, 106), "Recruiting process insights from Discord activity", font=_font(23), fill=MUTED)

    latest = "No activity yet"
    if stats_result.latest_activity:
        latest = stats_result.latest_activity.strftime("%b %d, %Y")

    _draw_metric(draw, (58, 166, 372, 292), "Tracked Events", str(stats_result.total_events), BLUE)
    _draw_metric(draw, (443, 166, 757, 292), "Candidates", str(stats_result.total_candidates), GREEN)
    _draw_metric(draw, (828, 166, 1142, 292), "Latest Activity", latest, AMBER)

    _draw_process_activity(draw, (58, 334, 746, 760), stats_result.stage_distribution)
    _draw_outcome_mix(draw, (782, 334, 1142, 760), stats_result.outcome_distribution)

    output = BytesIO()
    image.save(output, format="PNG", optimize=True)
    output.seek(0)
    return output
