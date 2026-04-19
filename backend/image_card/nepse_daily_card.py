"""
NEPSE Daily Update Card Generator
===================================
Composites live NEPSE market data onto the pre-designed `nepse_today.png` template.

Template layout (977×1221 px approx):
  ┌──────────────────────────────────────────┐
  │  [Nepali date at top — white box]        │
  │  [Bull/Bear market image — baked in]     │
  │  [NEPSE TODAY — green badge, baked in]   │
  │  [White content zone]                    │
  │     NEPSE POINT: { value }               │
  │     Total Turnover: { value }            │
  │     Total Traded Shares: { value }       │
  │  [Green footer strip — baked in]        │
  └──────────────────────────────────────────┘

Data source: https://sharehubnepal.com/live/api/v2/nepselive/home-page-data
"""

import asyncio
import io
import logging
from pathlib import Path

import httpx
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger("nepsebot.nepse_card")

# ── Template ──────────────────────────────────────────────────────────────────
TEMPLATE_PATH = Path(__file__).parent / "nepse_today.png"
FONTS_DIR = Path(__file__).parent / "fonts"

# ── ShareHub API ──────────────────────────────────────────────────────────────
SHAREHUB_API = "https://sharehubnepal.com/live/api/v2/nepselive/home-page-data"

# ── Nepali month names ────────────────────────────────────────────────────────
NEPALI_MONTHS = [
    "बैशाख", "जेठ", "असार", "श्रावण",
    "भाद्र", "असोज", "कार्तिक", "मंसिर",
    "पुष", "माघ", "फाल्गुण", "चैत्र",
]

NEPALI_DIGITS = str.maketrans("0123456789", "०१२३४५६७८९")


def _to_nepali_digits(s: str) -> str:
    return s.translate(NEPALI_DIGITS)


def _gregorian_to_bs(year: int, month: int, day: int) -> tuple[int, int, int]:
    """
    Approximate Gregorian → Bikram Sambat conversion.
    Accurate enough for NEPSE market cards.
    """
    # BS year starts ~mid-April of Gregorian year
    # Approximation: BS_year = AD_year + 56, adjusted for month
    bs_year = year + 56
    # Month offset: Nepali new year falls in mid-April (roughly April 14)
    from datetime import date
    new_year_approx = date(year, 4, 14)
    d = date(year, month, day)

    # Approximate number of days since last Nepali new year
    days_since_ny = (d - new_year_approx).days

    if days_since_ny < 0:
        # Before mid-April: still in previous BS year
        bs_year -= 1
        # Use previous year's new year
        prev_new_year = date(year - 1, 4, 14)
        days_since_ny = (d - prev_new_year).days

    # Approximate BS month and day from days elapsed
    # Each BS month is roughly 29-32 days; use static cumulative days per month
    # These are approximate averages:
    cum_days = [0, 31, 62, 92, 123, 153, 184, 214, 245, 275, 305, 336, 365]
    bs_month = 1
    bs_day = 1
    for i in range(1, 13):
        if days_since_ny < cum_days[i]:
            bs_month = i
            bs_day = days_since_ny - cum_days[i - 1] + 1
            break
    else:
        bs_month = 12
        bs_day = days_since_ny - cum_days[11] + 1

    return bs_year, bs_month, max(1, min(bs_day, 32))


def _nepali_date_str() -> str:
    """Return today's date in Nepali script, e.g. 'बैशाख-४, २०८२'."""
    from datetime import date, timezone, timedelta
    # Nepal is UTC+5:45
    nst = timezone(timedelta(hours=5, minutes=45))
    today = date.today()  # local date is fine for daily card
    bs_year, bs_month, bs_day = _gregorian_to_bs(today.year, today.month, today.day)
    month_name = NEPALI_MONTHS[bs_month - 1]
    day_str = _to_nepali_digits(str(bs_day))
    year_str = _to_nepali_digits(str(bs_year))
    return f"{month_name}-{day_str}, {year_str}"


def _ensure_fonts() -> None:
    """Download NotoSansDevanagari fonts if not cached (one-time, sync)."""
    import urllib.request
    _FONT_URLS = {
        "NotoSansDevanagari-Regular.ttf": (
            "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/"
            "NotoSansDevanagari/NotoSansDevanagari-Regular.ttf"
        ),
        "NotoSansDevanagari-Bold.ttf": (
            "https://github.com/googlefonts/noto-fonts/raw/main/hinted/ttf/"
            "NotoSansDevanagari/NotoSansDevanagari-Bold.ttf"
        ),
    }
    FONTS_DIR.mkdir(parents=True, exist_ok=True)
    for filename, url in _FONT_URLS.items():
        path = FONTS_DIR / filename
        if not path.exists():
            logger.info(f"Downloading font: {filename} …")
            try:
                urllib.request.urlretrieve(url, path)
            except Exception as exc:
                logger.warning(f"Font download failed ({filename}): {exc}")


def _devanagari_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    variant = "Bold" if bold else "Regular"
    path = FONTS_DIR / f"NotoSansDevanagari-{variant}.ttf"
    try:
        return ImageFont.truetype(str(path), size)
    except Exception:
        return ImageFont.load_default()


def _latin_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for p in candidates:
        if Path(p).exists():
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _format_turnover(value: float) -> str:
    """Format turnover in human-readable crore/arba format."""
    if value >= 1_000_000_000:
        return f"रू. {value / 1_000_000_000:.2f} अर्ब"
    elif value >= 10_000_000:
        return f"रू. {value / 10_000_000:.2f} करोड"
    else:
        return f"रू. {value:,.0f}"


def _format_shares(value: float) -> str:
    """Format share count."""
    if value >= 10_000_000:
        return f"{value / 10_000_000:.2f} करोड"
    elif value >= 100_000:
        return f"{value / 100_000:.2f} लाख"
    else:
        return f"{value:,.0f}"


async def fetch_nepse_data() -> dict:
    """Fetch live NEPSE market data from ShareHub API."""
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(SHAREHUB_API)
        resp.raise_for_status()
        return resp.json()


async def generate_nepse_daily_card() -> bytes:
    """
    Generate the daily NEPSE update card by compositing live data
    onto the nepse_today.png template.
    Returns JPEG bytes ready for Facebook upload.
    """
    await asyncio.to_thread(_ensure_fonts)

    # ── Fetch live API data ───────────────────────────────────────────────────
    try:
        data = await fetch_nepse_data()
    except Exception as exc:
        logger.error(f"Failed to fetch NEPSE data: {exc}")
        raise

    # ── Extract key values ────────────────────────────────────────────────────
    # NEPSE index
    nepse_index = next(
        (idx for idx in data.get("indices", []) if idx.get("symbol") == "NEPSE"),
        None,
    )
    nepse_point = nepse_index["currentValue"] if nepse_index else 0.0
    nepse_change = nepse_index["change"] if nepse_index else 0.0
    nepse_change_pct = nepse_index["changePercent"] if nepse_index else 0.0

    # Market summary
    market_summary = {item["name"]: item["value"] for item in data.get("marketSummary", [])}
    turnover = market_summary.get("Total Turnover Rs:", 0)
    traded_shares = market_summary.get("Total Traded Shares", 0)

    # Stock summary
    stock_summary = data.get("stockSummary", {})
    advanced = stock_summary.get("advanced", 0)
    declined = stock_summary.get("declined", 0)

    # ── Load template ─────────────────────────────────────────────────────────
    template = Image.open(TEMPLATE_PATH).convert("RGBA")
    tmpl_w, tmpl_h = template.size
    canvas = Image.new("RGBA", (tmpl_w, tmpl_h), (255, 255, 255, 255))
    canvas.alpha_composite(template)
    draw = ImageDraw.Draw(canvas)

    # ── Date box (top white rectangle) ────────────────────────────────────────
    # Pixel-scanned exact boundaries: x 333–798, y 0–95 (template 1080×1350)
    DATE_X1, DATE_X2 = 333, 798
    DATE_Y1, DATE_Y2 = 0, 95
    DATE_BOX_W = DATE_X2 - DATE_X1   # 465 px
    DATE_BOX_H = DATE_Y2 - DATE_Y1   # 95 px

    # Repaint the white box cleanly
    draw.rectangle([(DATE_X1, DATE_Y1), (DATE_X2, DATE_Y2)], fill=(255, 255, 255, 255))

    # Draw Nepali date — perfectly centred in the box
    date_str = _nepali_date_str()
    date_font = _devanagari_font(44, bold=True)
    date_color = (200, 30, 30, 255)   # red — matches original template style
    date_tw = int(draw.textlength(date_str, font=date_font))
    # textbbox gives accurate ascent/descent for vertical centering
    bbox = draw.textbbox((0, 0), date_str, font=date_font)
    text_h = bbox[3] - bbox[1]
    date_tx = DATE_X1 + (DATE_BOX_W - date_tw) // 2
    date_ty = DATE_Y1 + (DATE_BOX_H - text_h) // 2 - bbox[1]   # subtract top bearing
    draw.text((date_tx, date_ty), date_str, font=date_font, fill=date_color)

    # ── White content zone (pixel-scanned: x 108–971, y 628–1239) ───────────
    CONT_X1, CONT_X2 = 108, 971
    CONT_Y1, CONT_Y2 = 628, 1239
    CONT_W = CONT_X2 - CONT_X1   # 863 px
    CONT_H = CONT_Y2 - CONT_Y1   # 611 px

    # Blank all placeholder text in the content zone
    draw.rectangle([(CONT_X1, CONT_Y1), (CONT_X2, CONT_Y2)], fill=(255, 255, 255, 255))

    # ── Fonts ──────────────────────────────────────────────────────────────────
    label_font  = _latin_font(36, bold=False)        # section label (grey)
    value_font  = _devanagari_font(52, bold=True)    # big value number
    change_font = _latin_font(30, bold=False)        # change sub-text

    is_positive  = nepse_change >= 0
    change_color = (20, 140, 20, 255) if is_positive else (180, 20, 20, 255)
    arrow        = "▲" if is_positive else "▼"
    dark_blue    = (15, 25, 80, 255)
    grey_label   = (100, 100, 100, 255)

    # Helper: draw text perfectly centred horizontally within content zone
    def _cx(text: str, font) -> int:
        """Return x so text is centred in CONT_X1…CONT_X2."""
        bb = draw.textbbox((0, 0), text, font=font)
        tw = bb[2] - bb[0]
        return CONT_X1 + (CONT_W - tw) // 2

    def _draw_centred(y: int, text: str, font, color) -> int:
        """Draw text centred horizontally; return y advanced by true text height."""
        bb = draw.textbbox((0, 0), text, font=font)
        tx = CONT_X1 + (CONT_W - (bb[2] - bb[0])) // 2
        # Compensate for top bearing so top of glyph is at y
        draw.text((tx, y - bb[1]), text, font=font, fill=color)
        return y + (bb[3] - bb[1])   # advance by true text height

    # Thin grey divider
    def _divider(y: int, gap_before: int = 14, gap_after: int = 14) -> int:
        y += gap_before
        draw.line(
            [(CONT_X1 + 40, y), (CONT_X2 - 40, y)],
            fill=(210, 210, 210, 255), width=2,
        )
        return y + gap_after

    # ── Layout: distribute 4 sections evenly across CONT_H ────────────────────
    # Section heights (approx): use fixed spacing to fill the zone nicely
    # Total sections: NEPSE POINT (label+value+change), Turnover, Shares, Adv/Dec
    SECTION_GAP = 22   # gap between divider and next label

    y = CONT_Y1 + 28

    # ── 1. NEPSE POINT ─────────────────────────────────────────────────────────
    y = _draw_centred(y, "NEPSE POINT", label_font, grey_label)
    y += 6
    y = _draw_centred(y, f"{nepse_point:,.2f}", value_font, dark_blue)
    y += 8
    change_str = f"{arrow}  {abs(nepse_change):,.2f}  ({abs(nepse_change_pct):.2f}%)"
    y = _draw_centred(y, change_str, change_font, change_color)

    y = _divider(y, gap_before=18, gap_after=SECTION_GAP)

    # ── 2. Total Turnover ──────────────────────────────────────────────────────
    y = _draw_centred(y, "Total Turnover", label_font, grey_label)
    y += 6
    y = _draw_centred(y, _format_turnover(turnover), value_font, dark_blue)

    y = _divider(y, gap_before=18, gap_after=SECTION_GAP)

    # ── 3. Total Traded Shares ─────────────────────────────────────────────────
    y = _draw_centred(y, "Total Traded Shares", label_font, grey_label)
    y += 6
    y = _draw_centred(y, _format_shares(traded_shares), value_font, dark_blue)

    y = _divider(y, gap_before=18, gap_after=SECTION_GAP)

    # ── 4. Advanced / Declined ────────────────────────────────────────────────
    adv_font = _latin_font(32, bold=True)
    adv_str  = f"▲ {advanced} Advanced    |    {declined} Declined ▼"
    # Remaining space — vertically centre this line in what's left
    remaining = CONT_Y2 - y
    bb = draw.textbbox((0, 0), adv_str, font=adv_font)
    adv_h = bb[3] - bb[1]
    y_adv = y + max(10, (remaining - adv_h) // 2)
    _draw_centred(y_adv, adv_str, adv_font, (60, 60, 60, 255))


    # ── Footer: overwrite baked-in footer text ────────────────────────────────
    #footer_y1 = tmpl_h - 88
    #draw.rectangle([(0, footer_y1), (tmpl_w, tmpl_h)], fill=(41, 145, 25, 255))
    #ft_bold = _latin_font(30, bold=True)
    #ft_reg = _latin_font(28)
    #footer_baseline = footer_y1 + 28
    #draw.text((60, footer_baseline), "sharehubnepal.com", font=ft_bold, fill=(255, 255, 255, 255))
    #source_str = "Source : sharehubnepal.com"
    #s_tw = int(draw.textlength(source_str, font=ft_reg))
    #draw.text((tmpl_w - 60 - s_tw, footer_baseline + 2), source_str, font=ft_reg, fill=(255, 255, 255, 255))

    # ── Serialize → JPEG ──────────────────────────────────────────────────────
    buf = io.BytesIO()
    canvas.convert("RGB").save(buf, format="JPEG", quality=93, optimize=True)
    buf.seek(0)
    return buf.read()
