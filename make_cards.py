#!/usr/bin/env python3
"""Render coated stat-card PNGs that mimic the look of a GitHub readme stats card:
dark gradient background, rounded corners, accent border, icon + big value,
small label. Values are curated/presentation values in this repo (not live data)."""

from pathlib import Path
import math
from PIL import Image, ImageDraw, ImageFont

OUT = Path("profile-cards")
OUT.mkdir(exist_ok=True)

W, H = 320, 128
RAD = 14
PAD = 14
VALUE_SIZE = 28
LABEL_SIZE = 14

GRADIENT = (
    ((0, 0), (17, 17, 23)),     # #0d1117
    ((W, H), (1, 4, 9)),          # #010409
)


def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def hex_to_rgb(h):
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(ch * 2 for ch in h)
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def card_image(value, icon, accent, label_text):
    """Render one coated card PNG. Returns an Image."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # Rounded gradient background.
    mask = Image.new("L", (W, H), 0)
    md = ImageDraw.Draw(mask)
    md.rounded_rectangle([0, 0, W - 1, H - 1], radius=RAD, fill=255)
    bg = Image.new("RGB", (W, H), (0, 0, 0))
    bd = ImageDraw.Draw(bg)
    for y in range(H):
        t = y / (H - 1)
        bd.line([(0, y), (W, y)], fill=lerp(GRADIENT[0][1], GRADIENT[1][1], t))
    bg.putalpha(mask)

    ac = hex_to_rgb(accent)

    # Accent border.
    border = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bd2 = ImageDraw.Draw(border)
    bd2.rounded_rectangle([0, 0, W - 1, H - 1], radius=RAD, outline=ac, width=2)

    # Subtle inner second border for depth.
    inner = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    idd = ImageDraw.Draw(inner)
    idd.rounded_rectangle([3, 3, W - 4, H - 4], radius=RAD - 1, outline=ac, width=1)

    img = Image.alpha_composite(img, bg)
    img = Image.alpha_composite(img, border)
    img = Image.alpha_composite(img, inner)

    d = ImageDraw.Draw(img)

    def font(size, bold=False):
        paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        ]
        for p in paths:
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
        return ImageFont.load_default()

    try:
        val_font = font(VALUE_SIZE, bold=True)
        lab_font = font(LABEL_SIZE, bold=True)
    except Exception:
        val_font = lab_font = ImageFont.load_default()

    # Icon.
    try:
        import cairosvg
        ICON_SIZE = 30
        icon_svg_str = icon_svg_glyph(icon, accent)
        icon_img = Image.open(cairosvg.svg2png(bytestring=icon_svg_str.encode("utf-8"), output_width=ICON_SIZE, output_height=ICON_SIZE)).convert("RGBA")
        icon_img.putalpha(icon_img.split()[3].point(lambda a: int(a * 0.95))) # fmt: skip
        ix = PAD
        iy = (H - ICON_SIZE) // 2
        img.alpha_composite(icon_img, (ix, iy))
        label_x = ix + ICON_SIZE + 12
    except Exception:
        # Fallback: draw a simple circle + letters as icon.
        cx = PAD + 15
        cy = (H) // 2
        d.ellipse([cx - 12, cy - 12, cx + 12, cy + 12], fill=ac)
        try:
            icf = font(16, bold=True)
            d.text((cx - 10, cy - 11), icon[0].upper(), font=icf, fill=(255, 255, 255, 255)) # fmt: skip
        except Exception:
            pass
        label_x = cx + 28

    # Value.
    try:
        d.text((label_x, (H - VALUE_SIZE - 4) // 2 - 2), value, font=val_font, fill=(255, 255, 255, 255))
        try:
            _, vh = d.textsize(value, font=val_font)
        except Exception:
            vh = 20
    except Exception:
        d.text((label_x, 30), value, fill=(255, 255, 255, 255))
        vh = 20

    # Label.
    ly = H - PAD - 14
    d.text((label_x, ly), label_text, font=lab_font, fill=ac + (255,))

    # Bottom hairline.
    d.line([PAD, H - PAD - 4, W - PAD, H - PAD - 4], fill=ac + (255,), width=1)

    return img


def icon_svg_glyph(name, color):
    color_hex = "#" + color
    glyphs = {
        "github": f'''<svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" viewBox="0 0 24 24"><path fill="{color_hex}" d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm0 22.5c-5.38 0-10.26-2.16-13.85-5.66-.65 1.5-1 3.14-1 4.85 0 4.58 3.57 8.38 8.51 9.12l.55.06c.67.07 1.34-.19 1.74-.74 2.47-3 3.94-6.49 3.94-10.36 0-5.6-4.5-10.1-10-10.1-1.78 0-3.45.47-4.91 1.3l-.04-.03-.82-1.63c2.45-.89 5.05-1.39 7.78-1.39 6.63 0 12 5.37 12 12s-5.37 12-12 12z"/></svg>''',
        "code": f'''<svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" viewBox="0 0 24 24"><path fill="{color_hex}" d="M9.5 3.5c.83 0 1.5.67 1.5 1.5S10.33 6.5 9.5 6.5 8 5.83 8 5 8.67 3.5 9.5 3.5zm4 0c.83 0 1.5.67 1.5 1.5S14.33 6.5 13.5 6.5 12 5.83 12 5 12.67 3.5 13.5 3.5zm-7 6.5c0 .83.67 1.5 1.5 1.5s1.5-.67 1.5-1.5-.67-1.5-1.5-1.5-1.5.67-1.5 1.5zm3 0c0 .83.67 1.5 1.5 1.5s1.5-.67 1.5-1.5-.67-1.5-1.5-1.5-1.5.67-1.5 1.5zm-7 6.5c.83 0 1.5.67 1.5 1.5S7.33 16.5 6.5 16.5 5 15.83 5 15 5.67 13.5 6.5 13.5zm4 0c.83 0 1.5.67 1.5 1.5s-.67 1.5-1.5 1.5-1.5-.67-1.5-1.5.67-1.5 1.5-1.5zm0-7.5c.83 0 1.5.67 1.5 1.5s-.67 1.5-1.5 1.5-1.5-.67-1.5-1.5.67-1.5 1.5-1.5z"/></svg>''',
        "git": f'''<svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" viewBox="0 0 24 24"><path fill="{color_hex}" d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm0 20c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm-1-13h2v6h-2zm0 8h2v2h-2z"/></svg>''',
        "python": f'''<svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" viewBox="0 0 24 24"><path fill="{color_hex}" d="M12 0c3.9 0 7 3.1 7 7s-3.1 7-7 7-7-3.1-7-7 3.1-7 7-7zm0 12.5c.4-.3.9-.4 1.3-.1l.2.3c.2.3.3.6.1.8l-.1.2-.1-.1c-.2-.2-.5-.4-.8-.2-.2.1-.4.1-.5 0-.2-.1-.4-.1-.5-.2l-.2-.2-.2-.1c-.2-.1-.4 0-.5.1l-.2.2-.1-.1h-.1c-.3-.3-.6-.4-.9-.2-.2.1-.4.2-.5.4-.1.2-.1.4-.1.6 0 .4.2.6.5.7l.2.1h.1c.1 0 .3-.1.4-.1.2-.1.4-.2.5-.1.3.1.4.1.5.3l.1.2h.1c.2 0 .4-.1.5-.3.1-.2.2-.4.2-.6 0-.3-.1-.5-.3-.6z"/></svg>''',
        "javascript": f'''<svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" viewBox="0 0 24 24"><path fill="{color_hex}" d="M12 0c3.9 0 7 3.1 7 7s-3.1 7-7 7-7-3.1-7-7 3.1-7 7-7zm0 12.5c.4-.3.9-.4 1.3-.1l.2.3c.2.3.3.6.1.8l-.1.2-.1-.1c-.2-.2-.5-.4-.8-.2-.2.1-.4.1-.5 0-.2-.1-.4-.1-.5-.2l-.2-.2-.2-.1c-.2-.1-.4 0-.5.1l-.2.2-.1-.1h-.1c-.3-.3-.6-.4-.9-.2-.2.1-.4.2-.5.4-.1.2-.1.4-.1.6 0 .4.2.6.5.7l.2.1h.1c.1 0 .3-.1.4-.1.2-.1.4-.2.5-.1.3.1.4.1.5.3l.1.2h.1c.2 0 .4-.1.5-.3.1-.2.2-.4.2-.6 0-.3-.1-.5-.3-.6z"/></svg>''',
        "c": f'''<svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" viewBox="0 0 24 24"><path fill="{color_hex}" d="M12 0C4 0 0 4 0 12s4 12 12 12 12-4 12-12S20 0 12 0zm0 20.5c-4.1 0-7.5-3.4-7.5-7.5S7.9 5.5 12 5.5s7.5 3.4 7.5 7.5S16.1 20.5 12 20.5zm-1.5-9c.2.0.4.18.4.42S10.5 12.5 10.3 12.5 10.1 12.32 10.1 12.1s.18-.42.42-.42zm5.7 0c.2 0 .4.18.4.42s-.18.42-.42.42-.42-.18-.42-.42.18-.42.42-.42z"/></svg>''',
        "cpp": f'''<svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" viewBox="0 0 24 24"><path fill="{color_hex}" d="M12 0c3.9 0 7 3.1 7 7s-3.1 7-7 7-7-3.1-7-7 3.1-7 7-7zm0 12.5c.4-.3.9-.4 1.3-.1l.2.3c.2.3.3.6.1.8l-.1.2-.1-.1c-.2-.2-.5-.4-.8-.2-.2.1-.4.1-.5 0-.2-.1-.4-.1-.5-.2l-.2-.2-.2-.1c-.2-.1-.4 0-.5.1l-.2.2-.1-.1h-.1c-.3-.3-.6-.4-.9-.2-.2.1-.4.2-.5.4-.1.2-.1.4-.1.6 0 .4.2.6.5.7l.2.1h.1c.1 0 .3-.1.4-.1.2-.1.4-.2.5-.1.3.1.4.1.5.3l.1.2h.1c.2 0 .4-.1.5-.3.1-.2.2-.4.2-.6 0-.3-.1-.5-.3-.6z"/></svg>''',
        "php": f'''<svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" viewBox="0 0 24 24"><path fill="{color_hex}" d="M12 0C5.4 0 0 5.4 0 12s5.4 12 12 12 12-5.4 12-12S18.6 0 12 0zm0 21.5c-5.2 0-9.5-4.3-9.5-9.5S6.8 2.5 12 2.5s9.5 4.3 9.5 9.5S17.2 21.5 12 21.5zm0-17c-3 0-5.5 2.5-5.5 5.5s2.5 5.5 5.5 5.5 5.5-2.5 5.5-5.5S15 4.5 12 4.5z"/></svg>''',
    }
    g = glyphs.get(name)
    if g is None:
        g = f'<svg xmlns="http://www.w3.org/2000/svg" width="30" height="30" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10" fill="{color_hex}"/></svg>'
    return g


ITEMS = [
    ("12,480", "github", "0073B1", "Total Commits"),
    ("8,250", "code", "24C6DC", "Contributions"),
    ("1,560", "git", "FF6B35", "PRs Merged"),
    ("38%", "python", "3776AB", "Python"),
    ("22%", "javascript", "F7DF1E", "JavaScript"),
    ("15%", "c", "00599C", "C"),
    ("13%", "cpp", "00599C", "C++"),
    ("12%", "php", "777BB4", "PHP"),
]

for i, (value, icon, accent, label_text) in enumerate(ITEMS):
    im = card_image(value, icon, accent, label_text)
    path = OUT / f"card_{i:02d}_{label_text.lower().replace(' ', '_')}.png"
    im.save(path, optimize=True)
    print(path, im.size)

print("done")
