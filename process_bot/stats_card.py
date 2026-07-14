from __future__ import annotations

from io import BytesIO

from PIL import Image, ImageDraw, ImageFont

from process_bot import schemas
from process_bot.normalization import PROCESS_STAGE_ORDER, ordered_process_distribution, stage_display_name


WIDTH = 1200
HEIGHT = 872
BACKGROUND = (246, 248, 252)
PANEL = (255, 255, 255)
PANEL_ALT = (249, 251, 255)
TEXT = (23, 31, 45)
MUTED = (96, 109, 132)
BORDER = (224, 230, 240)
TRACK = (230, 236, 245)
SHADOW = (232, 237, 246)
BLUE = (45, 99, 232)
BLUE_GLOW = (49, 83, 173)
GREEN = (29, 135, 84)
AMBER = (223, 131, 22)
RED = (225, 47, 47)
INK = (16, 24, 40)

PAGE_PAD_X = 56
HEADER_TOP = 42
HEADER_SUBTOP = 104
CARD_GAP = 22
METRIC_TOP = 166
METRIC_HEIGHT = 126
LOWER_TOP = 334
LOWER_BOTTOM = 816


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
) -> ImageFont.ImageFont:
    font = _font(size, bold=bold)
    while size > min_size and draw.textlength(text, font=font) > max_width:
        size -= 1
        font = _font(size, bold=bold)
    draw.text(xy, text, font=font, fill=fill)
    return font


def _draw_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    *,
    font: ImageFont.ImageFont,
    fill: tuple[int, int, int] = TEXT,
) -> None:
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


def _card(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], *, radius: int = 24) -> None:
    x1, y1, x2, y2 = box
    draw.rounded_rectangle((x1, y1 + 8, x2, y2 + 8), radius=radius, fill=SHADOW)
    draw.rounded_rectangle(box, radius=radius, fill=PANEL, outline=BORDER, width=1)


def _draw_metric(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    label: str,
    value: str,
    accent: tuple[int, int, int],
) -> None:
    _card(draw, box, radius=20)
    x1, y1, x2, _ = box
    stripe_x = x1 + 24
    draw.rounded_rectangle((stripe_x, y1 + 22, stripe_x + 10, y1 + 92), radius=5, fill=accent)
    _draw_text(draw, (x1 + 50, y1 + 22), label.upper(), font=_font(16, bold=True), fill=MUTED)
    _draw_fit_text(
        draw,
        (x1 + 50, y1 + 58),
        value,
        max_width=x2 - x1 - 76,
        size=46,
        bold=True,
        min_size=24,
        fill=TEXT,
    )


def _draw_process_activity(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    distribution: dict[str, int],
) -> None:
    _card(draw, box)
    x1, y1, x2, _ = box
    _draw_text(draw, (x1 + 32, y1 + 26), "Process Activity", font=_font(30, bold=True), fill=TEXT)
    _draw_text(draw, (x1 + 32, y1 + 66), "Grouped as OA -> Behavioral -> Technical -> Offer", font=_font(18), fill=MUTED)

    ordered = ordered_process_distribution(distribution)
    max_count = max(ordered.values(), default=0)
    label_font = _font(22, bold=True)
    count_font = _font(22, bold=True)
    bar_left = x1 + 36
    bar_right = x2 - 34
    count_col_width = 58
    value_gap = 18
    fill_right = bar_right - count_col_width - value_gap
    bar_width = fill_right - bar_left
    y = y1 + 126

    for stage in PROCESS_STAGE_ORDER:
        count = ordered.get(stage, 0)
        label = stage_display_name(stage)
        _draw_text(draw, (bar_left, y), label, font=label_font, fill=INK)
        track_y = y + 42
        count_bbox = draw.textbbox((0, 0), str(count), font=count_font)
        count_height = count_bbox[3] - count_bbox[1]
        count_y = track_y + ((22 - count_height) // 2) - 1
        _draw_right_text(draw, bar_right, count_y, str(count), font=count_font, fill=INK)
        draw.rounded_rectangle((bar_left, track_y, fill_right, track_y + 22), radius=11, fill=TRACK)
        if max_count and count:
            fill_width = round(bar_width * (count / max_count))
            fill_width = max(16, fill_width)
            draw.rounded_rectangle((bar_left, track_y, bar_left + fill_width, track_y + 22), radius=11, fill=BLUE)
        y += 84


def _draw_outcome_row(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    *,
    label: str,
    count: int,
    percent: int,
    color: tuple[int, int, int],
) -> None:
    x1, y1, x2, y2 = box
    draw.rounded_rectangle((x1, y1 + 4, x2, y2 + 4), radius=18, fill=SHADOW)
    draw.rounded_rectangle(box, radius=18, fill=PANEL_ALT, outline=BORDER, width=1)
    center_y = (y1 + y2) // 2
    draw.ellipse((x1 + 24, center_y - 15, x1 + 54, center_y + 15), fill=color)
    _draw_text(draw, (x1 + 72, y1 + 22), label, font=_font(23, bold=True), fill=INK)
    _draw_text(draw, (x1 + 72, y1 + 54), f"{percent}% of outcomes", font=_font(17), fill=MUTED)

    count_text = str(count)
    count_font = _font(42, bold=True)
    count_width = int(draw.textlength(count_text, font=count_font))
    count_x = x2 - 26 - count_width
    count_y = y1 + max(16, ((y2 - y1) - 42) // 2)
    draw.text((count_x, count_y), count_text, font=count_font, fill=INK)


def _draw_outcome_mix(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    distribution: dict[str, int],
) -> None:
    _card(draw, box)
    x1, y1, x2, _ = box
    _draw_text(draw, (x1 + 30, y1 + 26), "Outcomes", font=_font(30, bold=True), fill=TEXT)
    _draw_text(draw, (x1 + 30, y1 + 66), "Final results logged", font=_font(18), fill=MUTED)

    offered = distribution.get("offered", 0) + distribution.get("accepted", 0)
    rejected = distribution.get("rejected", 0) + distribution.get("withdrawn", 0)
    total = offered + rejected
    rows = (
        ("Offers", offered, GREEN),
        ("Rejections", rejected, RED),
    )

    row_top = y1 + 140
    row_height = 100
    row_gap = 28
    for label, count, color in rows:
        percent = round((count / total) * 100) if total else 0
        _draw_outcome_row(
            draw,
            (x1 + 28, row_top, x2 - 28, row_top + row_height),
            label=label,
            count=count,
            percent=percent,
            color=color,
        )
        row_top += row_height + row_gap


def build_company_stats_card(stats_result: schemas.CompanyStatsResponse) -> BytesIO:
    image = Image.new("RGB", (WIDTH, HEIGHT), BACKGROUND)
    draw = ImageDraw.Draw(image)

    _draw_fit_text(
        draw,
        (PAGE_PAD_X, HEADER_TOP),
        f"{stats_result.company} Stats",
        max_width=WIDTH - (PAGE_PAD_X * 2),
        size=56,
        bold=True,
        min_size=34,
    )
    _draw_text(draw, (PAGE_PAD_X + 4, HEADER_SUBTOP), "Recruiting process insights from Discord activity", font=_font(22), fill=MUTED)

    latest = "No activity yet"
    if stats_result.latest_activity:
        latest = stats_result.latest_activity.strftime("%b %d, %Y")

    metric_width = (WIDTH - (PAGE_PAD_X * 2) - (CARD_GAP * 2)) // 3
    metric_boxes = [
        (PAGE_PAD_X + (metric_width + CARD_GAP) * index, METRIC_TOP, PAGE_PAD_X + (metric_width + CARD_GAP) * index + metric_width, METRIC_TOP + METRIC_HEIGHT)
        for index in range(3)
    ]
    _draw_metric(draw, metric_boxes[0], "Tracked Events", str(stats_result.total_events), BLUE)
    _draw_metric(draw, metric_boxes[1], "Candidates", str(stats_result.total_candidates), GREEN)
    _draw_metric(draw, metric_boxes[2], "Latest Activity", latest, AMBER)

    left_width = 690
    left_box = (PAGE_PAD_X, LOWER_TOP, PAGE_PAD_X + left_width, LOWER_BOTTOM)
    right_box = (left_box[2] + CARD_GAP + 14, LOWER_TOP, WIDTH - PAGE_PAD_X, LOWER_BOTTOM)

    _draw_process_activity(draw, left_box, stats_result.stage_distribution)
    _draw_outcome_mix(draw, right_box, stats_result.outcome_distribution)

    output = BytesIO()
    image.save(output, format="PNG", optimize=True)
    output.seek(0)
    return output
