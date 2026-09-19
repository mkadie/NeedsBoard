"""Generate the base_fruitjam.menu icon set and board composite.

Source art is the Moana icon set in original_icons/moana/ (flat vector, heavy
dark outline). Two of the six cells have no Moana equivalent, so they are
drawn here as type tiles in the same palette -- the project already used text
tiles for the old PLEASE / STINKY cells.

The type is laid out at the final pixel size rather than scaled down from a
master, because "DRINK" set for a 320px tile turns to mush when resampled to
53px. That is also why this script owns its output instead of feeding
image_tools.ImageScaler, which scales an existing tree.

Writes each cell and the 3x2 board to BOTH:
    image_160x128/base/   the per-resolution asset library
    menus/images/base/    what deploy.sh actually copies to the device

Usage:
    python3 make_base_icons.py
"""

import os

from PIL import Image, ImageDraw, ImageFont

from hardware_config import VARIANTS

MOANA = "original_icons/moana"

# Sampled from the Moana artwork so generated tiles sit in the same palette.
OUTLINE = (0x23, 0x1F, 0x20)
CREAM = (0xF9, 0xE8, 0xAC)
TEAL = (0x15, 0xAE, 0xAB)
DARK_TEAL = (0x32, 0x63, 0x68)
WHITE = (0xFF, 0xFF, 0xFF)

FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# Grid order, matching base_fruitjam.menu positions 1..6.
# A str spec is a Moana source file; a list spec is a generated type tile.
CELLS = [
    ("yes", "8_Icons-06.bmp"),       # thumbs up + green check
    ("no", "8_Icons-07.bmp"),        # thumbs down + red cross
    ("thankyou", "8_Icons-08.bmp"),  # praying hands
    ("bathroom", ["WC"]),
    ("play", "8_Icons-04.bmp"),      # football
    ("fooddrink", ["FOOD", "DRINK"]),
]

# Geometry comes from the variant table rather than being restated here, so
# the art can never disagree with the zones DisplayManager actually draws
# (zone = screen_width // button_cols, screen_height // button_rows).
# FRUITJAM_V2 and FRUITJAM_CLONE_18 share this screen and grid.
_V = VARIANTS["FRUITJAM_V2"]
BOARD_W, BOARD_H = _V["screen_width"], _V["screen_height"]
COLS, ROWS = _V["button_cols"], _V["button_rows"]

# The library tree (kept per resolution) and the tree deploy.sh copies to the
# device. Writing both is what makes "just run this script" actually true.
OUT_DIRS = ["image_{}x{}/base".format(BOARD_W, BOARD_H), "menus/images/base"]


def fit_font(draw, text, max_w, max_h):
    """Largest bold font size that keeps `text` inside max_w x max_h."""
    best = ImageFont.truetype(FONT_BOLD, 4)
    for size in range(5, 200):
        trial = ImageFont.truetype(FONT_BOLD, size)
        l, t, r, b = draw.textbbox((0, 0), text, font=trial)
        if r - l > max_w or b - t > max_h:
            break
        best = trial
    return best


def draw_centred(draw, text, font, cx, cy, fill):
    """Draw `text` centred on (cx, cy), correcting for the glyph bbox."""
    l, t, r, b = draw.textbbox((0, 0), text, font=font)
    draw.text((cx - (r + l) / 2, cy - (b + t) / 2), text, font=font, fill=fill)


def build_text_tile(w, h, lines):
    """A cream tile carrying one or two lines of bold type.

    Stands in for a pictogram where the Moana set has none. The outline is
    the icons' teal rather than their near-black, so a type tile does not
    out-weigh the drawn cells sitting beside it on the board.
    """
    img = Image.new("RGB", (w, h), WHITE)
    d = ImageDraw.Draw(img)

    pad = max(1, round(w * 0.04))
    stroke = max(2, round(w * 0.04))
    radius = max(3, round(w * 0.16))
    box = (pad, pad, w - 1 - pad, h - 1 - pad)
    d.rounded_rectangle(box, radius=radius, fill=CREAM,
                        outline=TEAL, width=stroke)

    # Generous inner margin: at 53px a glyph touching the outline reads as a
    # smudge, so buy legibility with whitespace rather than type size.
    margin = stroke + max(3, round(w * 0.11))
    inner_w = (box[2] - box[0]) - 2 * margin
    inner_h = (box[3] - box[1]) - 2 * margin

    # All lines share one size -- the smaller that fits -- so neither word
    # dominates. Nothing is drawn between them: at this size a divider rule
    # reads as a strikethrough.
    gap = max(2, round(h * 0.06))
    line_h = (inner_h - gap * (len(lines) - 1)) // len(lines)
    font = min((fit_font(d, ln, inner_w, line_h) for ln in lines),
               key=lambda f: f.size)

    heights = [d.textbbox((0, 0), ln, font=font)[3] -
               d.textbbox((0, 0), ln, font=font)[1] for ln in lines]
    y = h / 2 - (sum(heights) + gap * (len(lines) - 1)) / 2
    for ln, th in zip(lines, heights):
        draw_centred(d, ln, font, w / 2, y + th / 2, OUTLINE)
        y += th + gap
    return img


def build_moana_tile(filename, w, h):
    """Moana icon flattened onto white and fitted into w x h with padding.

    Flattening onto white matters: ImageScaler composites onto black
    (image_tools.py), which would put a dark halo round every icon.
    """
    src = Image.open(os.path.join(MOANA, filename)).convert("RGBA")
    flat = Image.new("RGBA", src.size, WHITE + (255,))
    flat.alpha_composite(src)
    art = flat.convert("RGB")

    pad = max(2, round(min(w, h) * 0.10))
    art.thumbnail((w - 2 * pad, h - 2 * pad), Image.LANCZOS)

    tile = Image.new("RGB", (w, h), WHITE)
    tile.paste(art, ((w - art.width) // 2, (h - art.height) // 2))
    return tile


def main():
    for d in OUT_DIRS:
        os.makedirs(d, exist_ok=True)

    cw, ch = BOARD_W // COLS, BOARD_H // ROWS
    board = Image.new("RGB", (BOARD_W, BOARD_H), WHITE)
    bd = ImageDraw.Draw(board)

    for i, (name, spec) in enumerate(CELLS):
        cell = (build_moana_tile(spec, cw, ch) if isinstance(spec, str)
                else build_text_tile(cw, ch, spec))
        for d in OUT_DIRS:
            cell.save(os.path.join(d, name + ".bmp"))

        x, y = (i % COLS) * cw, (i // COLS) * ch
        board.paste(cell, (x, y))
        # Thin separator so the 3x2 layout reads without the highlight.
        bd.rectangle((x, y, x + cw - 1, y + ch - 1), outline=DARK_TEAL, width=1)
        print("  {:10s} {}x{}".format(name, cw, ch))

    for d in OUT_DIRS:
        board.save(os.path.join(d, "base_board.bmp"))
    print("  board      {}x{}".format(BOARD_W, BOARD_H))
    print("  written to: " + ", ".join(OUT_DIRS))


if __name__ == "__main__":
    main()
