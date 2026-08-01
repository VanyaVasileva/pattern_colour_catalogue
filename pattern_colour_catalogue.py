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
    Most catalogue patterns should use reduced preview tiles only. Patterns listed
    in DIRECT_DOWNLOAD_PATTERN_IDS intentionally provide the recoloured original
    tile as a customer download, so only add purchased-pattern assets there.
"""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
import re
from typing import Iterable

import streamlit as st
from PIL import Image, ImageColor, ImageDraw


# ---------------------------------------------------------------------------
# App settings
# ---------------------------------------------------------------------------

APP_TITLE = "Vanya’s Pattern Colour Studio"
PATTERN_ROOT = Path(__file__).parent / "patterns"
DEFAULT_FIXED_BACKGROUND = "#F7F4EE"
DEFAULT_DOODLE_BACKGROUND = "#FCFBF8"
DEFAULT_BACKGROUND_ONLY = "#FFFFFF"
ITEMS_PER_PAGE = 12
DIRECT_DOWNLOAD_PATTERN_IDS = {"LEOPARD001", "MOUSE001"}


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

    # 2026 Trend Edit
    {"category": "2026 Trend Edit", "name": "Cloud Dancer", "bg": "#FAF9F6", "line": "#3F4745"},
    {"category": "2026 Trend Edit", "name": "Soft Jade", "bg": "#F2F4EE", "line": "#68745F"},
    {"category": "2026 Trend Edit", "name": "Cool Blue Ink", "bg": "#EFF8FC", "line": "#547185"},
    {"category": "2026 Trend Edit", "name": "Plum Noir", "bg": "#F8F3F5", "line": "#351E28"},
    {"category": "2026 Trend Edit", "name": "Persimmon Milk", "bg": "#FFF3EE", "line": "#A94F39"},

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
    "Vanilla Cream",
    "Warm Eucalyptus",
    "Deep Moss",
    "Muted Mallard",
    "Dusty Blue",
    "Teal Mist",
    "Plum Blush",
    "Lavender Fog",
    "Terracotta Sand",
    "Charcoal Linen",
    "Cloud Dancer",
    "Soft Jade",
    "Cool Blue Ink",
    "Plum Noir",
    "Persimmon Milk",
    "Dusty Rose",
    "Butter Navy",
    "Minimal Cloud",
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
    # Keep the uploaded tile at its complete original resolution. The same
    # full-resolution pixels are used for the on-screen preview and downloads.
    with Image.open(path_text) as image:
        return image.convert("RGBA")


def recolour_alpha_art(source: Image.Image, colour: str) -> Image.Image:
    """Recolour transparent line art while preserving its original alpha."""
    coloured = Image.new("RGBA", source.size, (*hex_rgb(colour), 255))
    coloured.putalpha(source.getchannel("A"))
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


def image_download_bytes(image: Image.Image, file_format: str) -> bytes:
    """Encode the exact full-resolution tile for a customer download."""
    output = BytesIO()
    rgb_image = image.convert("RGB")
    if file_format == "JPEG":
        rgb_image.save(
            output,
            format="JPEG",
            quality=95,
            subsampling=0,
            dpi=(300, 300),
        )
    elif file_format == "TIFF":
        rgb_image.save(
            output,
            format="TIFF",
            compression="tiff_lzw",
            dpi=(300, 300),
        )
    else:
        raise ValueError(f"Unsupported download format: {file_format}")
    return output.getvalue()


def download_filename(pattern: Pattern, background: str, line: str, suffix: str) -> str:
    """Create a useful filename containing the chosen colours."""
    safe_title = re.sub(r"[^A-Za-z0-9]+", "_", pattern.title).strip("_")
    if pattern.mode == "background":
        return (
            f"{pattern.pattern_id}_{safe_title}"
            f"_BG-{background.lstrip('#').upper()}.{suffix}"
        )
    return (
        f"{pattern.pattern_id}_{safe_title}"
        f"_BG-{background.lstrip('#').upper()}"
        f"_LINE-{line.lstrip('#').upper()}.{suffix}"
    )


def single_tile_preview(tile: Image.Image, canvas_size: tuple[int, int]) -> Image.Image:
    """Show one complete pattern tile for a clear catalogue thumbnail."""
    canvas = Image.new("RGB", canvas_size, tile.getpixel((0, 0)))
    resized = tile.copy()
    resized.thumbnail(canvas_size, Image.Resampling.LANCZOS)
    paste_x = (canvas_size[0] - resized.width) // 2
    paste_y = (canvas_size[1] - resized.height) // 2
    canvas.paste(resized, (paste_x, paste_y))
    return canvas


def palette_by_name(name: str) -> dict[str, str]:
    return next(p for p in PALETTES if p["name"] == name)


def catalogue_thumbnail(pattern: Pattern) -> Image.Image:
    source = load_source(str(pattern.path) if pattern.path else None)
    tile = compose_tile(
        source=source,
        mode=pattern.mode,
        line_colour="#46504C",
        background_colour="#FCFBF8",
    )
    return single_tile_preview(tile, canvas_size=(480, 480))


def pattern_catalogue(patterns: Iterable[Pattern]) -> Pattern:
    st.subheader("1. Choose a pattern")

    all_patterns = list(patterns)
    if (
        "selected_pattern_label" not in st.session_state
        or st.session_state.selected_pattern_label not in {p.label for p in all_patterns}
    ):
        st.session_state.selected_pattern_label = all_patterns[0].label

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

    page_count = max(1, (len(filtered) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
    if page_count > 1:
        page_number = st.selectbox(
            "Catalogue page",
            options=list(range(1, page_count + 1)),
            format_func=lambda value: f"Page {value} of {page_count}",
        )
    else:
        page_number = 1

    start = (page_number - 1) * ITEMS_PER_PAGE
    visible_patterns = filtered[start : start + ITEMS_PER_PAGE]
    st.caption(f"Showing {start + 1}–{start + len(visible_patterns)} of {len(filtered)} patterns")

    gallery_columns = st.columns(2)
    for index, pattern in enumerate(visible_patterns):
        with gallery_columns[index % 2]:
            st.image(catalogue_thumbnail(pattern), use_container_width=True)
            if pattern.label == st.session_state.selected_pattern_label:
                st.success(f"Selected · {pattern.label}")
            if st.button(
                f"Choose {pattern.title}",
                key=f"choose_pattern_{pattern.pattern_id}_{index}_{page_number}",
                use_container_width=True,
                type="primary" if pattern.label == st.session_state.selected_pattern_label else "secondary",
            ):
                st.session_state.selected_pattern_label = pattern.label
                st.rerun()

    return next(p for p in all_patterns if p.label == st.session_state.selected_pattern_label)


def pattern_from_direct_link(patterns: Iterable[Pattern]) -> Pattern | None:
    """Resolve ?pattern=ID links used in pattern-specific Etsy PDFs."""
    requested_id = str(st.query_params.get("pattern", "")).strip().upper()
    if not requested_id:
        return None
    return next(
        (pattern for pattern in patterns if pattern.pattern_id == requested_id),
        None,
    )


def sync_colour_from_picker(colour_type: str) -> None:
    """Keep the picker, HEX field, preview colour, and palette label in sync."""
    value = st.session_state[f"{colour_type}_picker"].upper()
    st.session_state[f"{colour_type}_colour"] = value
    st.session_state[f"{colour_type}_hex"] = value
    st.session_state.palette_name = "Custom"


def sync_colour_from_hex(colour_type: str) -> None:
    """Validate a typed HEX value and copy it back to the colour picker."""
    value = normalise_hex(
        st.session_state[f"{colour_type}_hex"],
        st.session_state[f"{colour_type}_picker"],
    )
    st.session_state[f"{colour_type}_colour"] = value
    st.session_state[f"{colour_type}_picker"] = value
    st.session_state[f"{colour_type}_hex"] = value
    st.session_state.palette_name = "Custom"


def swap_background_and_line() -> None:
    """Reverse the current background and line colours everywhere."""
    old_background = st.session_state.background_colour
    old_line = st.session_state.line_colour
    st.session_state.background_colour = old_line
    st.session_state.line_colour = old_background
    st.session_state.background_picker = old_line
    st.session_state.background_hex = old_line
    st.session_state.line_picker = old_background
    st.session_state.line_hex = old_background
    st.session_state.palette_name = "Custom · Reversed"


def default_background_for(pattern: Pattern) -> str:
    if pattern.mode == "background":
        return DEFAULT_BACKGROUND_ONLY
    if pattern.mode == "both":
        return DEFAULT_DOODLE_BACKGROUND
    return DEFAULT_FIXED_BACKGROUND


def initialise_pattern_colours(pattern: Pattern) -> None:
    """Start each newly selected pattern with its correct default colours."""
    if st.session_state.get("active_pattern_id") == pattern.pattern_id:
        return

    background = default_background_for(pattern)
    line = "#46504C"
    st.session_state.active_pattern_id = pattern.pattern_id
    st.session_state.background_colour = background
    st.session_state.background_picker = background
    st.session_state.background_hex = background
    st.session_state.line_colour = line
    st.session_state.line_picker = line
    st.session_state.line_hex = line
    st.session_state.palette_name = "Custom"


def palette_controls(pattern: Pattern) -> tuple[str, str, str]:
    st.subheader("2. Choose your colours")

    if "line_colour" not in st.session_state:
        st.session_state.line_colour = "#46504C"
    if "background_colour" not in st.session_state:
        st.session_state.background_colour = default_background_for(pattern)
    if "palette_name" not in st.session_state:
        st.session_state.palette_name = "Custom"
    for colour_type in ("background", "line"):
        if f"{colour_type}_picker" not in st.session_state:
            st.session_state[f"{colour_type}_picker"] = st.session_state[f"{colour_type}_colour"]
        if f"{colour_type}_hex" not in st.session_state:
            st.session_state[f"{colour_type}_hex"] = st.session_state[f"{colour_type}_colour"]

    category_options = ["Popular"] + sorted({p["category"] for p in PALETTES})
    collection_label = (
        "Background colour collection"
        if pattern.mode == "background"
        else "Palette collection"
    )
    palette_category = st.selectbox(collection_label, category_options)
    visible_palettes = (
        [palette_by_name(name) for name in POPULAR_NAMES]
        if palette_category == "Popular"
        else [p for p in PALETTES if p["category"] == palette_category]
    )

    columns = st.columns(4)
    for index, palette in enumerate(visible_palettes):
        with columns[index % 4]:
            st.markdown(
                (
                    f"""
                    <div style="height:28px;border-radius:8px;overflow:hidden;display:flex;margin-bottom:5px">
                      <span style="flex:1;background:{palette['bg']}"></span>
                    </div>
                    """
                    if pattern.mode == "background"
                    else f"""
                    <div style="height:28px;border-radius:8px;overflow:hidden;display:flex;margin-bottom:5px">
                      <span style="flex:1;background:{palette['bg']}"></span>
                      <span style="flex:1;background:{palette['line']}"></span>
                    </div>
                    """
                ),
                unsafe_allow_html=True,
            )
            if st.button(palette["name"], key=f"palette_{palette['name']}", use_container_width=True):
                st.session_state.background_colour = palette["bg"]
                st.session_state.palette_name = palette["name"]
                st.session_state.background_picker = palette["bg"]
                st.session_state.background_hex = palette["bg"]
                if pattern.mode in {"both", "line"}:
                    st.session_state.line_colour = palette["line"]
                    st.session_state.line_picker = palette["line"]
                    st.session_state.line_hex = palette["line"]
                st.rerun()

    st.caption("Or create your own colour combination")
    if pattern.mode == "both":
        st.button(
            "↔ Swap background and line colours",
            on_click=swap_background_and_line,
            use_container_width=True,
        )
    if pattern.mode == "background":
        st.color_picker(
            "Background colour",
            key="background_picker",
            on_change=sync_colour_from_picker,
            args=("background",),
        )
        st.text_input(
            "Background HEX",
            key="background_hex",
            on_change=sync_colour_from_hex,
            args=("background",),
        )
        st.info("The original watercolour motifs stay unchanged.")
        return (
            st.session_state.background_colour,
            "Original watercolour motifs",
            st.session_state.palette_name,
        )

    custom_left, custom_right = st.columns(2)

    with custom_left:
        if pattern.mode in {"both", "background"}:
            picked_bg = st.color_picker(
                "Background colour",
                key="background_picker",
                on_change=sync_colour_from_picker,
                args=("background",),
            )
            typed_bg = st.text_input(
                "Background HEX",
                key="background_hex",
                on_change=sync_colour_from_hex,
                args=("background",),
            )
            background_colour = st.session_state.background_colour
        else:
            background_colour = DEFAULT_FIXED_BACKGROUND
            st.info(f"Background fixed: {DEFAULT_FIXED_BACKGROUND}")

    with custom_right:
        if pattern.mode in {"both", "line"}:
            picked_line = st.color_picker(
                "Line colour",
                key="line_picker",
                on_change=sync_colour_from_picker,
                args=("line",),
            )
            typed_line = st.text_input(
                "Line HEX",
                key="line_hex",
                on_change=sync_colour_from_hex,
                args=("line",),
            )
            line_colour = st.session_state.line_colour
        else:
            line_colour = "Original motif colours"
            st.info("The motif colours stay unchanged.")

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
        "then preview your chosen colour version."
    )

    patterns = discover_patterns(PATTERN_ROOT)
    if not patterns:
        patterns = [Pattern("DEMO-001", "Demo Animals", "Animals", "both", None)]
        st.caption("Demo mode — add low-resolution PNG preview tiles to the patterns folders.")

    requested_id = str(st.query_params.get("pattern", "")).strip().upper()
    selected_pattern = pattern_from_direct_link(patterns)
    if selected_pattern:
        st.subheader("1. Your purchased pattern")
        st.success(selected_pattern.label)
    else:
        if requested_id:
            st.warning(
                f"The pattern link `{requested_id}` was not found. "
                "Please choose a pattern from the catalogue."
            )
        selected_pattern = pattern_catalogue(patterns)

    initialise_pattern_colours(selected_pattern)
    background_colour, line_colour, palette_name = palette_controls(selected_pattern)

    st.subheader("3. Preview your colour version")
    is_direct_download = selected_pattern.pattern_id in DIRECT_DOWNLOAD_PATTERN_IDS
    source = load_source(str(selected_pattern.path) if selected_pattern.path else None)
    tile = compose_tile(
        source=source,
        mode=selected_pattern.mode,
        line_colour=line_colour if line_colour != "Original motif colours" else "#000000",
        background_colour=background_colour,
    )
    # Do not ask Streamlit to resize or optimise the preview to the container.
    # Passing the native pixel width keeps the full original tile in the image
    # element; smaller screens may scale it visually, but the source stays exact.
    st.image(tile, width=tile.width)
    st.caption(
        f"Original full-resolution tile · {tile.width} × {tile.height} px"
    )

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

    if is_direct_download:
        st.subheader("4. Download your colour version")
        st.info(
            f"Your downloaded tile keeps the original {tile.width} × {tile.height} px "
            "dimensions, motif placement, scale and spacing exactly as purchased."
        )
        jpeg_data = image_download_bytes(tile, "JPEG")
        tiff_data = image_download_bytes(tile, "TIFF")
        jpeg_name = download_filename(
            selected_pattern,
            background_colour,
            line_colour,
            "jpg",
        )
        tiff_name = download_filename(
            selected_pattern,
            background_colour,
            line_colour,
            "tiff",
        )
        jpeg_column, tiff_column = st.columns(2)
        with jpeg_column:
            st.download_button(
                "Download JPEG",
                data=jpeg_data,
                file_name=jpeg_name,
                mime="image/jpeg",
                type="primary",
                use_container_width=True,
            )
        with tiff_column:
            st.download_button(
                "Download TIFF",
                data=tiff_data,
                file_name=tiff_name,
                mime="image/tiff",
                use_container_width=True,
            )
        st.success("Your JPEG and TIFF files are ready to download.")
        st.caption(
            "Colour changes only · The original drawings, tile layout, scale and spacing remain unchanged."
        )
        return

    st.info(
        "Direct downloads are not enabled for this pattern yet. "
        "Only purchased patterns listed for direct download provide JPEG and TIFF files."
    )


if __name__ == "__main__":
    render_app()
