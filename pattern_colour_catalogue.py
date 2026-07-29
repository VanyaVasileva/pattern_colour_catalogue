"""
Vanya Illustrations — Pattern Colour Studio
============================================

Run locally:
    pip install streamlit pillow
    streamlit run pattern_colour_catalogue.py

GitHub / Streamlit Community Cloud:
    1. Add this file to the repository.
    2. Add a requirements.txt containing:
           streamlit>=1.42
           Pillow>=10.0
    3. EASIEST METHOD: add LOW-RESOLUTION preview PNGs directly beside this
       Python file. The filename tells the app how to recolour them:

       both__DINO001__Dinos_Doodle.png
       background__DUC015__Duck_Family.png
       line__FOX008__Little_Foxes.png

       Optional category in the filename:
       both__Animals__DINO001__Dinos_Doodle.png

       The older patterns/both, patterns/background and patterns/line folder
       structure is also supported.

Pattern modes:
    both        Transparent line-art PNG. Customer may change line + background.
    background  Coloured motifs on transparency. Customer changes background only.
    line        Transparent line-art PNG. Customer changes line only; background
                remains the fixed colour defined by DEFAULT_FIXED_BACKGROUND.

Filename format:
    PATTERN-ID__Readable_Title.png

Important:
    Never place printable/high-resolution originals in a public GitHub repository.
    Use reduced preview tiles only. This app intentionally has no download button.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Iterable
from urllib.parse import quote

import streamlit as st
from PIL import Image, ImageColor, ImageDraw, ImageFont


# ---------------------------------------------------------------------------
# App settings
# ---------------------------------------------------------------------------

APP_TITLE = "Vanya’s Pattern Colour Studio"
PATTERN_ROOT = Path(__file__).parent / "patterns"
PREVIEW_SIZE = (900, 720)
MAX_SOURCE_PREVIEW_PX = 520
DEFAULT_FIXED_BACKGROUND = "#F7F4EE"
WATERMARK_TEXT = "VANYA ILLUSTRATIONS · PREVIEW"
# Replace this once with the business email that should receive selections.
CONTACT_EMAIL = "vanya_illustrations@yahoo.com"


# ---------------------------------------------------------------------------
# Curated two-colour presets: background + line
# ---------------------------------------------------------------------------

PALETTES = [
    # Warm Neutrals
    {"category": "Warm Neutrals", "name": "Forest Cream", "bg": "#F3EFE4", "line": "#3F5147"},
    {"category": "Warm Neutrals", "name": "Milk & Cookies", "bg": "#EFE7DC", "line": "#4A3B32"},
    {"category": "Warm Neutrals", "name": "Vanilla Cream", "bg": "#FBF8F3", "line": "#7F6E61"},
    {"category": "Warm Neutrals", "name": "Cocoa Oat", "bg": "#E8DCCB", "line": "#665246"},
    {"category": "Warm Neutrals", "name": "Espresso Ivory", "bg": "#F5F0E6", "line": "#493D38"},
    {"category": "Warm Neutrals", "name": "Taupe Cloud", "bg": "#EEE9E0", "line": "#6B6259"},
    {"category": "Warm Neutrals", "name": "Woodland Mushroom", "bg": "#FAF6F0", "line": "#4D3E35"},
    {"category": "Warm Neutrals", "name": "Acorn Hollow", "bg": "#FAF6EE", "line": "#4A3C32"},

    # Sage & Green
    {"category": "Sage & Green", "name": "Warm Eucalyptus", "bg": "#E7E7D8", "line": "#52685B"},
    {"category": "Sage & Green", "name": "Olive Oat", "bg": "#E8E1D2", "line": "#66705A"},
    {"category": "Sage & Green", "name": "French Sage", "bg": "#F6F9F6", "line": "#6B705C"},
    {"category": "Sage & Green", "name": "Forest Floor", "bg": "#FAF7EE", "line": "#383D28"},
    {"category": "Sage & Green", "name": "Silver Eucalyptus", "bg": "#F2F5F3", "line": "#3E4D46"},
    {"category": "Sage & Green", "name": "Clover Field", "bg": "#F7F7F4", "line": "#434D3B"},
    {"category": "Sage & Green", "name": "Mossy Brook", "bg": "#F3F5F2", "line": "#3C4234"},
    {"category": "Sage & Green", "name": "Deep Moss", "bg": "#E2E5D5", "line": "#495C46"},

    # Blue & Teal
    {"category": "Blue & Teal", "name": "Dusty Blue", "bg": "#E7ECEA", "line": "#536A78"},
    {"category": "Blue & Teal", "name": "Cloud Blue", "bg": "#E9EEF0", "line": "#597188"},
    {"category": "Blue & Teal", "name": "Nordic Sky", "bg": "#F0F4F8", "line": "#4A5560"},
    {"category": "Blue & Teal", "name": "Muted Mallard", "bg": "#F6F5EE", "line": "#34413F"},
    {"category": "Blue & Teal", "name": "Forget-Me-Not", "bg": "#F5F7FA", "line": "#3B4654"},
    {"category": "Blue & Teal", "name": "Patina Cream", "bg": "#F2EBDD", "line": "#3F7472"},
    {"category": "Blue & Teal", "name": "Teal Mist", "bg": "#DDE9E4", "line": "#356B69"},
    {"category": "Blue & Teal", "name": "Denim Biscuit", "bg": "#E8D9C3", "line": "#465F75"},

    # Blush & Lavender
    {"category": "Blush & Lavender", "name": "Dusty Rose", "bg": "#F7F2F2", "line": "#5A4545"},
    {"category": "Blush & Lavender", "name": "Lavender Fog", "bg": "#EBE6ED", "line": "#6C6279"},
    {"category": "Blush & Lavender", "name": "Plum Blush", "bg": "#EADBDD", "line": "#725B66"},
    {"category": "Blush & Lavender", "name": "Muted Clay", "bg": "#F1DED4", "line": "#925F50"},
    {"category": "Blush & Lavender", "name": "Rose Cocoa", "bg": "#F0E2DC", "line": "#7C5D5A"},
    {"category": "Blush & Lavender", "name": "Sweet Plum", "bg": "#F8F5F6", "line": "#4A3A43"},
    {"category": "Blush & Lavender", "name": "Orchid Silk", "bg": "#F4EEF2", "line": "#705B6C"},
    {"category": "Blush & Lavender", "name": "Burgundy Blush", "bg": "#ECDDDD", "line": "#6E454D"},

    # Warm Retro
    {"category": "Warm Retro", "name": "Terracotta Sand", "bg": "#F0DDCF", "line": "#8A5848"},
    {"category": "Warm Retro", "name": "Groovy Apricot", "bg": "#FCEFE3", "line": "#A55742"},
    {"category": "Warm Retro", "name": "Olive & Amber", "bg": "#F7F4EB", "line": "#4A2E11"},
    {"category": "Warm Retro", "name": "Antique Marigold", "bg": "#FDFBF5", "line": "#615341"},
    {"category": "Warm Retro", "name": "Retro Pumpkin", "bg": "#FBF3EB", "line": "#522E1B"},
    {"category": "Warm Retro", "name": "Saffron Moon", "bg": "#FAF7F2", "line": "#5E4B3E"},
    {"category": "Warm Retro", "name": "Sunset Boulevard", "bg": "#FDF5EC", "line": "#613B30"},
    {"category": "Warm Retro", "name": "Butter Navy", "bg": "#F3E6B8", "line": "#364A61"},

    # Monochrome
    {"category": "Monochrome", "name": "Charcoal Linen", "bg": "#F1EDE4", "line": "#56534F"},
    {"category": "Monochrome", "name": "Minimal Cloud", "bg": "#F5F5F3", "line": "#333333"},
    {"category": "Monochrome", "name": "Soft Graphite", "bg": "#ECEAE6", "line": "#4C4A47"},
    {"category": "Monochrome", "name": "Warm Ink", "bg": "#F7F3EC", "line": "#514942"},
    {"category": "Monochrome", "name": "Slate Mist", "bg": "#EEF1F2", "line": "#46515A"},
    {"category": "Monochrome", "name": "Mushroom Ink", "bg": "#E9E3DC", "line": "#5D544D"},
    {"category": "Monochrome", "name": "Khaki Ink", "bg": "#E5DDC9", "line": "#5E5948"},
    {"category": "Monochrome", "name": "Aubergine Ink", "bg": "#F1E8DC", "line": "#5E465A"},
]

POPULAR_NAMES = [
    "Forest Cream",
    "Milk & Cookies",
    "Warm Eucalyptus",
    "Muted Mallard",
    "Dusty Blue",
    "Plum Blush",
    "Terracotta Sand",
    "Charcoal Linen",
]


@dataclass(frozen=True)
class Pattern:
    pattern_id: str
    title: str
    category: str
    mode: str
    path: Path | None

    @property
    def label(self) -> str:
        return f"{self.pattern_id} · {self.title}"


def normalise_hex(value: str, fallback: str) -> str:
    """Return a valid uppercase #RRGGBB value."""
    value = value.strip()
    if not value.startswith("#"):
        value = "#" + value
    if re.fullmatch(r"#[0-9A-Fa-f]{6}", value):
        return value.upper()
    return fallback.upper()


def hex_rgb(value: str) -> tuple[int, int, int]:
    return ImageColor.getrgb(normalise_hex(value, "#FFFFFF"))


def readable_title(raw: str) -> str:
    return re.sub(r"[_-]+", " ", raw).strip().title()


def discover_patterns(root: Path) -> list[Pattern]:
    patterns: list[Pattern] = []

    # Simple GitHub workflow: PNG files placed directly in the repository root.
    # Supported names:
    #   both__ID__Readable_Title.png
    #   both__Category__ID__Readable_Title.png
    repository_root = root.parent
    for path in sorted(repository_root.glob("*.png")):
        parts = path.stem.split("__")
        if len(parts) not in {3, 4}:
            continue
        mode = parts[0].strip().casefold()
        if mode not in {"both", "background", "line"}:
            continue
        if len(parts) == 3:
            category = "Patterns"
            pattern_id, raw_title = parts[1], parts[2]
        else:
            category = readable_title(parts[1])
            pattern_id, raw_title = parts[2], parts[3]
        patterns.append(
            Pattern(
                pattern_id.strip().upper(),
                readable_title(raw_title),
                category,
                mode,
                path,
            )
        )

    # Folder workflow remains supported for larger catalogues.
    for mode in ("both", "background", "line"):
        mode_root = root / mode
        if not mode_root.exists():
            continue
        for path in sorted(mode_root.rglob("*.png")):
            relative = path.relative_to(mode_root)
            category = readable_title(relative.parent.as_posix()) if relative.parent.as_posix() != "." else "Other"
            stem_parts = path.stem.split("__", 1)
            pattern_id = stem_parts[0].strip().upper()
            title = readable_title(stem_parts[1] if len(stem_parts) == 2 else stem_parts[0])
            patterns.append(Pattern(pattern_id, title, category, mode, path))
    return patterns


def make_demo_tile() -> Image.Image:
    """A small in-memory fallback so the app works before assets are added."""
    tile = Image.new("RGBA", (420, 420), (0, 0, 0, 0))
    draw = ImageDraw.Draw(tile)
    for ox, oy in ((45, 60), (250, 230)):
        draw.ellipse((ox, oy, ox + 112, oy + 88), outline=(0, 0, 0, 255), width=6)
        draw.ellipse((ox + 13, oy - 7, ox + 40, oy + 22), outline=(0, 0, 0, 255), width=6)
        draw.ellipse((ox + 73, oy - 7, ox + 100, oy + 22), outline=(0, 0, 0, 255), width=6)
        draw.ellipse((ox + 35, oy + 35, ox + 44, oy + 44), fill=(0, 0, 0, 255))
        draw.ellipse((ox + 70, oy + 35, ox + 79, oy + 44), fill=(0, 0, 0, 255))
        draw.arc((ox + 38, oy + 42, ox + 78, oy + 70), 10, 170, fill=(0, 0, 0, 255), width=5)
    return tile


@st.cache_data(show_spinner=False)
def load_source(path_text: str | None) -> Image.Image:
    if not path_text:
        return make_demo_tile()
    image = Image.open(path_text).convert("RGBA")
    image.thumbnail((MAX_SOURCE_PREVIEW_PX, MAX_SOURCE_PREVIEW_PX), Image.Resampling.LANCZOS)
    return image


def recolour_alpha_art(source: Image.Image, colour: str) -> Image.Image:
    """Replace all visible RGB pixels while preserving anti-aliased alpha."""
    alpha = source.getchannel("A")
    coloured = Image.new("RGBA", source.size, (*hex_rgb(colour), 255))
    coloured.putalpha(alpha)
    return coloured


def compose_tile(
    source: Image.Image,
    mode: str,
    line_colour: str,
    background_colour: str,
) -> Image.Image:
    if mode in {"both", "line"}:
        foreground = recolour_alpha_art(source, line_colour)
    else:
        foreground = source.copy()

    fixed_or_selected_bg = background_colour if mode in {"both", "background"} else DEFAULT_FIXED_BACKGROUND
    base = Image.new("RGBA", source.size, (*hex_rgb(fixed_or_selected_bg), 255))
    base.alpha_composite(foreground)
    return base.convert("RGB")


def repeat_preview(tile: Image.Image, canvas_size: tuple[int, int] = PREVIEW_SIZE) -> Image.Image:
    """Repeat the tile and add a light diagonal watermark."""
    canvas = Image.new("RGB", canvas_size, tile.getpixel((0, 0)))
    tile_w = max(150, min(360, canvas_size[0] // 3))
    tile_h = max(150, round(tile.height * tile_w / tile.width))
    resized = tile.resize((tile_w, tile_h), Image.Resampling.LANCZOS)

    for y in range(-tile_h // 2, canvas_size[1], tile_h):
        for x in range(-tile_w // 2, canvas_size[0], tile_w):
            canvas.paste(resized, (x, y))

    overlay = Image.new("RGBA", canvas_size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 24)
    except OSError:
        font = ImageFont.load_default()
    for y in range(70, canvas_size[1], 170):
        for x in range(-80, canvas_size[0], 330):
            draw.text((x, y), WATERMARK_TEXT, fill=(45, 45, 45, 42), font=font)
    return Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")


def palette_by_name(name: str) -> dict[str, str]:
    return next(p for p in PALETTES if p["name"] == name)


def pattern_catalogue(patterns: Iterable[Pattern]) -> Pattern:
    st.subheader("1. Choose a pattern")

    all_patterns = list(patterns)
    categories = ["All"] + sorted({p.category for p in all_patterns})
    left, right = st.columns([1, 1.35])
    with left:
        category = st.selectbox("Pattern category", categories)
    with right:
        query = st.text_input("Search", placeholder="Hippo, bunny, botanical…")

    filtered = [
        p for p in all_patterns
        if (category == "All" or p.category == category)
        and (not query or query.casefold() in f"{p.pattern_id} {p.title} {p.category}".casefold())
    ]
    if not filtered:
        st.warning("No matching pattern. Try another search.")
        filtered = all_patterns

    labels = [p.label for p in filtered]
    selected_label = st.selectbox("Pattern", labels)
    return next(p for p in filtered if p.label == selected_label)


def palette_controls(pattern: Pattern) -> tuple[str, str, str]:
    st.subheader("2. Choose your colours")

    if "line_colour" not in st.session_state:
        st.session_state.line_colour = "#3F5147"
    if "background_colour" not in st.session_state:
        st.session_state.background_colour = "#F3EFE4"
    if "palette_name" not in st.session_state:
        st.session_state.palette_name = "Forest Cream"

    category_options = ["Popular"] + sorted({p["category"] for p in PALETTES})
    palette_category = st.selectbox("Palette collection", category_options)
    visible_palettes = (
        [palette_by_name(name) for name in POPULAR_NAMES]
        if palette_category == "Popular"
        else [p for p in PALETTES if p["category"] == palette_category]
    )

    columns = st.columns(4)
    for index, palette in enumerate(visible_palettes):
        with columns[index % 4]:
            st.markdown(
                f"""
                <div style="height:28px;border-radius:8px;overflow:hidden;display:flex;margin-bottom:5px">
                  <span style="flex:1;background:{palette['bg']}"></span>
                  <span style="flex:1;background:{palette['line']}"></span>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button(palette["name"], key=f"palette_{palette['name']}", use_container_width=True):
                st.session_state.background_colour = palette["bg"]
                st.session_state.line_colour = palette["line"]
                st.session_state.palette_name = palette["name"]
                st.session_state.background_picker = palette["bg"]
                st.session_state.background_hex = palette["bg"]
                st.session_state.line_picker = palette["line"]
                st.session_state.line_hex = palette["line"]
                st.rerun()

    st.caption("Or create your own colour combination")
    custom_left, custom_right = st.columns(2)

    with custom_left:
        if pattern.mode in {"both", "background"}:
            picked_bg = st.color_picker(
                "Background colour",
                st.session_state.background_colour,
                key="background_picker",
            )
            typed_bg = st.text_input(
                "Background HEX",
                st.session_state.background_colour,
                key="background_hex",
            )
            background_colour = normalise_hex(typed_bg, picked_bg)
            if picked_bg.upper() != st.session_state.background_colour.upper():
                background_colour = picked_bg.upper()
        else:
            background_colour = DEFAULT_FIXED_BACKGROUND
            st.info(f"Background fixed: {DEFAULT_FIXED_BACKGROUND}")

    with custom_right:
        if pattern.mode in {"both", "line"}:
            picked_line = st.color_picker(
                "Line colour",
                st.session_state.line_colour,
                key="line_picker",
            )
            typed_line = st.text_input(
                "Line HEX",
                st.session_state.line_colour,
                key="line_hex",
            )
            line_colour = normalise_hex(typed_line, picked_line)
            if picked_line.upper() != st.session_state.line_colour.upper():
                line_colour = picked_line.upper()
        else:
            line_colour = "Original motif colours"
            st.info("The motif colours stay unchanged.")

    custom_changed = (
        background_colour != st.session_state.background_colour
        or (line_colour != "Original motif colours" and line_colour != st.session_state.line_colour)
    )
    if custom_changed:
        st.session_state.background_colour = background_colour
        if line_colour != "Original motif colours":
            st.session_state.line_colour = line_colour
        st.session_state.palette_name = "Custom"

    return (
        st.session_state.background_colour if pattern.mode in {"both", "background"} else DEFAULT_FIXED_BACKGROUND,
        st.session_state.line_colour if pattern.mode in {"both", "line"} else "Original motif colours",
        st.session_state.palette_name,
    )


def render_app() -> None:
    st.set_page_config(page_title=APP_TITLE, page_icon="🎨", layout="wide")
    st.title(APP_TITLE)
    st.write(
        "Choose a pattern, try a curated palette or enter your own colours, "
        "then send your chosen colour version or versions."
    )

    patterns = discover_patterns(PATTERN_ROOT)
    if not patterns:
        patterns = [Pattern("DEMO-001", "Demo Animals", "Animals", "both", None)]
        st.caption("Demo mode — add low-resolution PNG preview tiles to the patterns folders.")

    selected_pattern = pattern_catalogue(patterns)
    background_colour, line_colour, palette_name = palette_controls(selected_pattern)

    st.subheader("3. Preview your colour version")
    source = load_source(str(selected_pattern.path) if selected_pattern.path else None)
    tile = compose_tile(
        source=source,
        mode=selected_pattern.mode,
        line_colour=line_colour if line_colour != "Original motif colours" else "#000000",
        background_colour=background_colour,
    )
    preview = repeat_preview(tile)
    st.image(preview, use_container_width=True)

    line_display = line_colour if selected_pattern.mode in {"both", "line"} else "Original motif colours"
    background_display = (
        background_colour if selected_pattern.mode in {"both", "background"}
        else f"Fixed {DEFAULT_FIXED_BACKGROUND}"
    )
    st.markdown(
        f"""
        **Pattern:** {selected_pattern.label}  
        **Palette:** {palette_name}  
        **Background:** `{background_display}`  
        **Line / motif:** `{line_display}`
        """
    )
    st.subheader("4. Send your selection")
    customer_name = st.text_input("Your name", placeholder="Name or business name")
    order_number = st.text_input("Etsy order number (optional)", placeholder="For example: 1234567890")
    short_message = st.text_area(
        "Short message (optional)",
        placeholder="Anything you would like me to know about your colour choice…",
        max_chars=500,
    )

    subject = f"Pattern colour selection — {selected_pattern.title} ({selected_pattern.pattern_id})"
    body_lines = [
        "Hello Vanya,",
        "",
        "I would like this pattern in the following colours:",
        "",
        f"Pattern: {selected_pattern.label}",
        f"Palette: {palette_name}",
        f"Background: {background_display}",
        f"Line / motif: {line_display}",
    ]
    if customer_name.strip():
        body_lines.append(f"Customer: {customer_name.strip()}")
    if order_number.strip():
        body_lines.append(f"Etsy order number: {order_number.strip()}")
    if short_message.strip():
        body_lines.extend(["", "Message:", short_message.strip()])
    body_lines.extend(["", "Thank you!"])

    mailto_url = (
        f"mailto:{CONTACT_EMAIL}"
        f"?subject={quote(subject)}"
        f"&body={quote(chr(10).join(body_lines))}"
    )
    st.link_button("Send my colour selection by email", mailto_url, type="primary")
    st.caption(
        "This opens your own email app with the pattern name, colours and message already filled in. "
        "Please review the email and press Send."
    )

    st.caption("Preview only · No printable file is available in this colour studio.")


if __name__ == "__main__":
    render_app()
