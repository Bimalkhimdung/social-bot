"""
NEPSE News Card Generator — Template Mode
==========================================
Composites article content onto the pre-designed `news.png` template.

Updated template layout (1080×1350 px):
  ┌───────────────────────────────────────────────────────┐
  │  [BREAKING NEWS badge — baked into template]          │   y: 0–107
  │  ┌─────────────────────────────────────────────────┐  │
  │  │     ← article image pasted here →               │  │   y: 108–766
  │  └─────────────────────────────────────────────────┘  │
  │         [NEPSE TODAY green button — baked in]         │   y: 779–857
  │                                                       │
  │       { Nepali headline drawn here }                  │   y: 858–1214
  │                                                       │
  │  [Green footer strip — baked in]                      │   y: 1215–1350
  │    Read More               Source : domain            │
  └───────────────────────────────────────────────────────┘
"""

import asyncio
import io
import logging
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

import httpx
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger("nepsebot.image_card")

# ── Template ──────────────────────────────────────────────────────────────────
TEMPLATE_PATH = Path(__file__).parent / "news.png"
TMPL_W, TMPL_H = 1080, 1350

# ── Zone coordinates (measured by pixel scan) ────────────────────────────────

# Photo / image zone
IMG_X1, IMG_Y1 = 50,  108
IMG_X2, IMG_Y2 = 1031, 766
IMG_W = IMG_X2 - IMG_X1   # 981
IMG_H = IMG_Y2 - IMG_Y1   # 658

# White title zone (below NEPSE TODAY, above footer)
TITLE_X1, TITLE_Y1 = 50,  858
TITLE_X2, TITLE_Y2 = 1031, 1214
TITLE_W = TITLE_X2 - TITLE_X1   # 981
TITLE_H = TITLE_Y2 - TITLE_Y1   # 356

# Footer strip
FOOTER_STRIP_Y = 1215          # where green footer starts
FOOTER_Y       = 1272          # text baseline inside footer
FOOTER_LEFT_X  = 75            # "Read More" left edge
FOOTER_RIGHT_X = 1005          # "Source : domain" right edge (subtract text width)

# ── Fonts ─────────────────────────────────────────────────────────────────────
FONTS_DIR = Path(__file__).parent / "fonts"

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


def _ensure_fonts() -> None:
    """Download NotoSansDevanagari fonts if not cached (one-time, sync)."""
    FONTS_DIR.mkdir(parents=True, exist_ok=True)
    for filename, url in _FONT_URLS.items():
        path = FONTS_DIR / filename
        if not path.exists():
            logger.info(f"Downloading font: {filename} …")
            try:
                urllib.request.urlretrieve(url, path)
                logger.info(f"Font saved: {path}")
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
    """System font for Latin-only labels (Read More, Source)."""
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


# ── Helpers ───────────────────────────────────────────────────────────────────

def _domain(url: str) -> str:
    try:
        return urlparse(url).netloc.replace("www.", "")
    except Exception:
        return ""


def _wrap(text: str, font: ImageFont.FreeTypeFont,
          max_w: int, draw: ImageDraw.ImageDraw) -> list[str]:
    """Word-wrap text to fit within max_w pixels."""
    words = text.split()
    lines: list[str] = []
    cur = ""
    for word in words:
        test = (cur + " " + word).strip()
        if draw.textlength(test, font=font) <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


async def _download_image(url: str) -> Image.Image | None:
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            r = await client.get(url)
            r.raise_for_status()
            return Image.open(io.BytesIO(r.content)).convert("RGBA")
    except Exception as exc:
        logger.warning(f"Image download failed ({url[:80]}): {exc}")
        return None


# ── Main generator ────────────────────────────────────────────────────────────

async def generate_news_card(
    title: str,
    image_url: str | None,
    source_label: str = "",
    article_url: str = "",
) -> bytes:
    """
    Composite article content onto the news.png template.
    Returns JPEG bytes ready for Facebook upload.

    Process:
      1. Punch a transparent hole in the template's image zone
      2. Paste downloaded article image underneath
      3. Alpha-composite template on top (borders/badges/NEPSE TODAY preserved)
      4. Blank the { News heading here } placeholder in the white zone
      5. Draw Nepali title, centered in the white zone
      6. Overwrite footer text with dynamic Read More / Source : domain
    """
    await asyncio.to_thread(_ensure_fonts)

    # ── Load template + punch out image zone ─────────────────────────────────
    # Draw a fully-transparent rectangle in the image zone so the article
    # photo we paste underneath shows through (removes placeholder + watermark).
    template = Image.open(TEMPLATE_PATH).convert("RGBA")
    draw_tmpl = ImageDraw.Draw(template)
    draw_tmpl.rectangle(
        [(IMG_X1, IMG_Y1), (IMG_X2, IMG_Y2)],
        fill=(0, 0, 0, 0),
    )

    # ── Download + size article image ─────────────────────────────────────────
    article_img = await _download_image(image_url) if image_url else None

    if article_img:
        # Scale to fill zone width, then center-crop to zone height
        scale = IMG_W / article_img.width
        new_h = max(int(article_img.height * scale), IMG_H)
        article_img = article_img.resize((IMG_W, new_h), Image.LANCZOS)
        crop_top = (article_img.height - IMG_H) // 2
        article_img = article_img.crop((0, crop_top, IMG_W, crop_top + IMG_H))
    else:
        # Dark placeholder
        article_img = Image.new("RGBA", (IMG_W, IMG_H), (30, 90, 35, 255))

    # ── Composite layers ──────────────────────────────────────────────────────
    # Base: solid white (so all opaque white template zones look correct)
    base = Image.new("RGBA", (TMPL_W, TMPL_H), (255, 255, 255, 255))
    # Layer 1: article image in the punched-out zone
    base.paste(article_img.convert("RGBA"), (IMG_X1, IMG_Y1))
    # Layer 2: template on top (transparent punch-out lets image show through)
    base.alpha_composite(template)
    canvas = base
    draw = ImageDraw.Draw(canvas)

    # ── Blank the white title area fully (removes { News heading here }) ──────
    draw.rectangle(
        [(IMG_X1, TITLE_Y1), (IMG_X2, TITLE_Y2)],
        fill=(255, 255, 255, 255),
    )

    # ── Draw Nepali title, centered in the white zone ─────────────────────────
    title_font = _devanagari_font(48, bold=True)
    padding    = 50
    max_tw     = TITLE_W - 2 * padding
    lines      = _wrap(title, title_font, max_tw, draw)
    line_h     = 64
    total_h    = len(lines) * line_h
    # Center vertically, but bias toward the upper half of the zone
    ty = TITLE_Y1 + max(40, (TITLE_H - total_h) // 2 - 20)

    for i, line in enumerate(lines[:5]):
        tw = int(draw.textlength(line, font=title_font))
        tx = IMG_X1 + (TITLE_W - tw) // 2
        draw.text(
            (tx, ty + i * line_h),
            line,
            font=title_font,
            fill=(20, 20, 20, 255),
        )

    # ── Overwrite baked-in footer text with dynamic values ───────────────────
    # Cover template's "Read More" and "Source : www.nepsesignal.com" first
    draw.rectangle(
        [(0, FOOTER_STRIP_Y), (TMPL_W, TMPL_H)],
        fill=(41, 145, 25, 255),   # exact green sampled from template footer
    )

    # "Read More" — bold white, left
    ft_bold = _latin_font(36, bold=True)
    draw.text(
        (FOOTER_LEFT_X, FOOTER_Y),
        "Read More",
        font=ft_bold,
        fill=(255, 255, 255, 255),
    )

    # "Source : domain" — regular white, right-aligned
    ft_reg = _latin_font(34)
    domain_str = (
        f"Source : nepsesignal.com"
    )
    d_tw = int(draw.textlength(domain_str, font=ft_reg))
    draw.text(
        (FOOTER_RIGHT_X - d_tw, FOOTER_Y + 2),
        domain_str,
        font=ft_reg,
        fill=(255, 255, 255, 255),
    )

    # ── Serialize → JPEG ──────────────────────────────────────────────────────
    buf = io.BytesIO()
    canvas.convert("RGB").save(buf, format="JPEG", quality=93, optimize=True)
    buf.seek(0)
    return buf.read()
