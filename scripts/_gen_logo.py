#!/usr/bin/env python3
"""Generate the SA Systems honeycomb logo + MEDIFLOW store assets.

Faithful recreation of the supplied SA Systems mark:
  * three columns of stacked pointy-top hexagons (the "8" pinch per column)
  * a light-grey honeycomb lattice woven between the red columns
  * the inner vertical edges of the red hexes are grey (so red reads "open")
  * a short red bar through the dead centre
  * every edge is trimmed at its ends -> the segmented, woven look
  * lowercase "sa systems" wordmark

Geometry is computed, not hand-placed, so every asset stays in sync.
"""
from __future__ import annotations
import math
import os

# ---- palette -------------------------------------------------------------
RED = "#E5232A"
GREY = "#D7D9DB"      # light honeycomb lattice
INK = "#0B0B0B"       # wordmark

# ---- hex geometry --------------------------------------------------------
R = 60.0                       # centre -> vertex
W = R * math.sqrt(3) / 2.0     # centre -> flat side (~51.96)
COL_X = [i * 2 * W for i in range(5)]   # 5 interlocking columns: 0,2W,4W,6W,8W
ROW_CY = [0.0, 2 * R]                   # two rows, pinching at y = R
RED_COLS = {0, 2, 4}                    # red columns; 1,3 are the grey lattice

MARK_W = 10 * W                # natural bbox width  (-W .. 9W)
MARK_H = 4 * R                 # natural bbox height (-R .. 3R)
OX, OY = W, R                  # translate so the bbox starts at (0,0)


def _hex(cx: float, cy: float) -> list[tuple[float, float]]:
    """Pointy-top hexagon vertices (top, UR, LR, bottom, LL, UL)."""
    return [
        (cx, cy - R),
        (cx + W, cy - R / 2),
        (cx + W, cy + R / 2),
        (cx, cy + R),
        (cx - W, cy + R / 2),
        (cx - W, cy - R / 2),
    ]


def _red_edges(col: int, row: int) -> list[bool]:
    """Which of the 6 edges are red for a red hex.

    Edges: e0 UR, e1 R(vert), e2 LR, e3 LL, e4 L(vert), e5 UL.
    Inner-facing edges stay grey so each column reads as an open bracket
    rather than a closed hexagon (and the pinch points never cross in red).
    """
    red = [False] * 6
    if col == 0:                       # left column -> full red, open inner-right
        for i in (0, 2, 3, 4, 5):
            red[i] = True              # all but e1 (inner right vertical)
    elif col == 4:                     # right column -> full red, open inner-left
        for i in (0, 1, 2, 3, 5):
            red[i] = True              # all but e4 (inner left vertical)
    elif col == 2:                     # middle column -> lighter, peaks only
        if row == 0:
            red[5] = red[0] = True     # top peak
        else:
            red[2] = red[3] = True     # bottom peak
    return red


def _trim(p1, p2, g):
    x1, y1 = p1
    x2, y2 = p2
    dx, dy = x2 - x1, y2 - y1
    L = math.hypot(dx, dy)
    if L == 0:
        return p1, p2
    ux, uy = dx / L, dy / L
    return (x1 + ux * g, y1 + uy * g), (x2 - ux * g, y2 - uy * g)


def _line(p1, p2, color, sw, gap):
    a, b = _trim(p1, p2, gap)
    return (f'    <line x1="{a[0]:.2f}" y1="{a[1]:.2f}" '
            f'x2="{b[0]:.2f}" y2="{b[1]:.2f}" '
            f'stroke="{color}" stroke-width="{sw}"/>\n')


def build_mark(red: str = RED, grey: str = GREY,
               sw_red: float = 11, sw_grey: float = 7, gap: float = 4.2) -> str:
    """Return the honeycomb mark as an SVG group, bbox = MARK_W x MARK_H."""
    out = [f'  <g transform="translate({OX:.2f} {OY:.2f})" fill="none" '
           'stroke-linecap="round" stroke-linejoin="round">\n']

    # 1) grey lattice (columns 1 & 3) — woven behind the red
    for col in (1, 3):
        for cy in ROW_CY:
            pts = _hex(COL_X[col], cy)
            for i in range(6):
                out.append(_line(pts[i], pts[(i + 1) % 6], grey, sw_grey, gap))

    # 2) red hex outlines (columns 0,2,4) — only the red edges
    for col in (0, 2, 4):
        for row, cy in enumerate(ROW_CY):
            red_edge = _red_edges(col, row)
            pts = _hex(COL_X[col], cy)
            for i in range(6):
                if red_edge[i]:
                    out.append(_line(pts[i], pts[(i + 1) % 6], red, sw_red, gap))

    # 3) central red bar through the middle pinch
    mid_x, mid_y = COL_X[2], R
    out.append(_line((mid_x - W * 0.62, mid_y), (mid_x + W * 0.62, mid_y),
                     red, sw_red, gap))

    out.append("  </g>\n")
    return "".join(out)


# ---- file plumbing -------------------------------------------------------
def write(path: str, content: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(content)
    print("wrote", path, os.path.getsize(path), "bytes")


HERE = os.path.dirname(os.path.abspath(__file__))
DESC = os.path.normpath(os.path.join(HERE, "..", "mediflow", "static", "description"))
IMG = os.path.normpath(os.path.join(HERE, "..", "mediflow", "static", "src", "img"))
WORDMARK_FONT = "'Poppins','Segoe UI','Helvetica Neue',Arial,sans-serif"


def header(vb_w: float, vb_h: float, w: float, h: float, label: str) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<!-- SA Systems — {label} -->\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {vb_w:.0f} {vb_h:.0f}" width="{w:.0f}" height="{h:.0f}" '
        f'role="img" aria-label="SA Systems">\n'
    )


def _placed_mark(target_w: float, x: float, y: float, **kw) -> tuple[str, float]:
    """Mark scaled to target_w, translated to (x,y). Returns (svg, scaled_h)."""
    sc = target_w / MARK_W
    svg = (f'  <g transform="translate({x:.2f} {y:.2f}) scale({sc:.4f})">\n'
           + build_mark(**kw) + "  </g>\n")
    return svg, MARK_H * sc


def _hex_field(x0: float, y0: float, x1: float, y1: float, r: float,
               color: str, sw: float, opacity: float) -> str:
    """Faint honeycomb tessellation (derived from the logo motif) over a region."""
    w = r * math.sqrt(3) / 2.0
    vstep = 1.5 * r
    hstep = 2 * w
    out = [f'  <g fill="none" stroke="{color}" stroke-width="{sw}" '
           f'opacity="{opacity}" stroke-linejoin="round">\n']
    row = 0
    y = y0
    while y < y1 + r:
        off = w if (row % 2) else 0.0
        x = x0
        while x < x1 + w:
            cx, cy = x + off, y
            pts = [(cx, cy - r), (cx + w, cy - r / 2), (cx + w, cy + r / 2),
                   (cx, cy + r), (cx - w, cy + r / 2), (cx - w, cy - r / 2)]
            d = "M" + " L".join(f"{px:.1f},{py:.1f}" for px, py in pts) + " Z"
            out.append(f'    <path d="{d}"/>\n')
            x += hstep
        y += vstep
        row += 1
    out.append("  </g>\n")
    return "".join(out)


def gen_logo_light(dark: bool = False) -> str:
    """Primary logo: mark + lowercase wordmark."""
    mark_w = 360.0
    pad = 24.0
    grey = "#3A5563" if dark else GREY
    ink = "#FFFFFF" if dark else INK
    mark_svg, mh = _placed_mark(mark_w, pad, pad, grey=grey)
    vb_w = mark_w + pad * 2
    vb_h = pad + mh + 96
    s = header(vb_w, vb_h, vb_w, vb_h, "primary logo")
    s += mark_svg
    s += (f'  <text x="{vb_w/2:.0f}" y="{pad + mh + 64:.0f}" text-anchor="middle" '
          f'font-family="{WORDMARK_FONT}" font-size="74" font-weight="700" '
          f'fill="{ink}" letter-spacing="-1">sa systems</text>\n')
    s += "</svg>\n"
    return s


def gen_mark_square(dark: bool = False) -> str:
    """Just the honeycomb mark, centred in a square."""
    side = 360.0
    grey = "#3A5563" if dark else GREY
    mark_w = side - 48
    sc = mark_w / MARK_W
    mh = MARK_H * sc
    mark_svg, _ = _placed_mark(mark_w, (side - mark_w) / 2, (side - mh) / 2, grey=grey)
    label = "mark on dark" if dark else "mark"
    s = header(side, side, side, side, label)
    s += mark_svg
    s += "</svg>\n"
    return s


def gen_icon() -> str:
    """512x512 rounded app icon: the logo mark + MEDIFLOW wordmark on a light card."""
    s = header(512, 512, 512, 512, "MEDIFLOW app icon")
    s += (
        '  <defs>\n'
        '    <linearGradient id="card" x1="0" y1="0" x2="0.35" y2="1">\n'
        '      <stop offset="0" stop-color="#FFFFFF"/>\n'
        '      <stop offset="1" stop-color="#EEF3F7"/>\n'
        '    </linearGradient>\n'
        '    <linearGradient id="accent" x1="0" y1="0" x2="1" y2="0">\n'
        '      <stop offset="0" stop-color="#E5232A"/>\n'
        '      <stop offset="0.55" stop-color="#E5232A"/>\n'
        '      <stop offset="1" stop-color="#1B5E7E"/>\n'
        '    </linearGradient>\n'
        '    <radialGradient id="glow" cx="0.5" cy="0.42" r="0.55">\n'
        '      <stop offset="0" stop-color="#E5232A" stop-opacity="0.10"/>\n'
        '      <stop offset="1" stop-color="#E5232A" stop-opacity="0"/>\n'
        '    </radialGradient>\n'
        '    <clipPath id="cardclip">\n'
        '      <rect x="16" y="16" width="480" height="480" rx="108"/>\n'
        '    </clipPath>\n'
        '  </defs>\n'
        '  <rect x="16" y="16" width="480" height="480" rx="108" fill="url(#card)"/>\n'
    )
    # honeycomb texture (clipped to the card) + warm glow behind the mark
    s += '  <g clip-path="url(#cardclip)">\n'
    s += _hex_field(40, 40, 472, 472, 46, "#E5232A", 2.2, 0.05)
    s += '    <rect x="16" y="16" width="480" height="480" fill="url(#glow)"/>\n'
    s += '  </g>\n'
    # the logo mark, centred in the upper area
    mark_w = 380.0
    mark_svg, _ = _placed_mark(mark_w, (512 - mark_w) / 2, 128, grey=GREY)
    s += mark_svg
    # elegant centred underline
    s += ('  <rect x="196" y="372" width="120" height="6" rx="3" '
          'fill="url(#accent)"/>\n')
    s += (
        '  <g text-anchor="middle">\n'
        f'    <text x="256" y="446" font-family="{WORDMARK_FONT}" font-size="64" '
        'font-weight="800" fill="#0B1F2A" letter-spacing="1">MEDI'
        '<tspan fill="#1B5E7E" font-weight="600">FLOW</tspan></text>\n'
        f'    <text x="256" y="480" font-family="{WORDMARK_FONT}" font-size="19" '
        'font-weight="700" fill="#5B7282" letter-spacing="4.5">BY SA SYSTEMS</text>\n'
        '  </g>\n'
        '  <rect x="16" y="16" width="480" height="480" rx="108" fill="none" '
        'stroke="#E2E8EE" stroke-width="2"/>\n'
    )
    s += "</svg>\n"
    return s


def gen_banner() -> str:
    """1200x1200 square store banner, derived from the logo."""
    s = header(1200, 1200, 1200, 1200, "MEDIFLOW store banner")
    s += (
        '  <defs>\n'
        '    <linearGradient id="sky" x1="0" y1="0" x2="1" y2="1">\n'
        '      <stop offset="0" stop-color="#08171F"/>\n'
        '      <stop offset="0.52" stop-color="#123747"/>\n'
        '      <stop offset="1" stop-color="#1B5E7E"/>\n'
        '    </linearGradient>\n'
        '    <linearGradient id="rule" x1="0" y1="0" x2="1" y2="0">\n'
        '      <stop offset="0" stop-color="#E5232A"/>\n'
        '      <stop offset="1" stop-color="#21C7A8"/>\n'
        '    </linearGradient>\n'
        '    <radialGradient id="warm" cx="0.5" cy="0.5" r="0.5">\n'
        '      <stop offset="0" stop-color="#E5232A" stop-opacity="0.30"/>\n'
        '      <stop offset="1" stop-color="#E5232A" stop-opacity="0"/>\n'
        '    </radialGradient>\n'
        '    <linearGradient id="chip" x1="0" y1="0" x2="0" y2="1">\n'
        '      <stop offset="0" stop-color="#FFFFFF"/>\n'
        '      <stop offset="1" stop-color="#EDF2F6"/>\n'
        '    </linearGradient>\n'
        '  </defs>\n'
        '  <rect width="1200" height="1200" fill="url(#sky)"/>\n'
    )
    # full-bleed honeycomb texture derived from the logo
    s += _hex_field(-60, -60, 1260, 1260, 86, "#FFFFFF", 2.4, 0.04)
    # warm glow behind the brand chip
    s += '  <circle cx="266" cy="348" r="360" fill="url(#warm)"/>\n'
    # faint oversized watermark mark, lower-right
    wm, _ = _placed_mark(900, 470, 560, red="#FFFFFF", grey="#FFFFFF")
    s += f'  <g opacity="0.05">\n{wm}  </g>\n'
    # white brand chip holding the mark
    s += ('  <rect x="150" y="232" width="232" height="232" rx="50" '
          'fill="url(#chip)" stroke="#FFFFFF" stroke-opacity="0.6" stroke-width="2"/>\n')
    chip, _ = _placed_mark(178, 177, 322, grey=GREY)
    s += chip
    # product wordmark
    s += (
        '  <g font-family="' + WORDMARK_FONT + '">\n'
        '    <text x="430" y="330" font-size="124" font-weight="800" fill="#FFFFFF" '
        'letter-spacing="1">MEDI<tspan fill="#7FD4EC" font-weight="600">FLOW</tspan></text>\n'
        '    <text x="434" y="388" font-size="34" font-weight="700" fill="#9FB4C2" '
        'letter-spacing="6">BY SA SYSTEMS</text>\n'
        '  </g>\n'
        '  <rect x="152" y="514" width="320" height="8" rx="4" fill="url(#rule)"/>\n'
        '  <text x="152" y="606" font-family="' + WORDMARK_FONT + '" font-size="54" '
        'font-weight="700" fill="#EAF2F6">Clinic &amp; Diagnostics ERP</text>\n'
        '  <text x="152" y="672" font-family="' + WORDMARK_FONT + '" font-size="34" '
        'font-weight="400" fill="#C2D2DC">Front desk · Lab bench · Revenue cycle — one Odoo install</text>\n'
    )
    chips = ["Multi-currency", "FHIR R4", "10 region profiles", "Odoo 18 &amp; 19"]
    x, y = 152, 748
    for c in chips:
        label_len = len(c.replace("&amp;", "&"))
        w = 38 + label_len * 19
        s += (f'  <rect x="{x}" y="{y}" width="{w}" height="64" rx="32" '
              'fill="#FFFFFF" fill-opacity="0.06" stroke="#FFFFFF" '
              'stroke-opacity="0.38" stroke-width="2"/>\n'
              f'  <text x="{x + w/2:.0f}" y="{y + 41}" text-anchor="middle" '
              'font-family="' + WORDMARK_FONT + '" font-size="26" font-weight="600" '
              f'fill="#EAF2F6">{c}</text>\n')
        x += w + 22
        if x > 980:
            x, y = 152, y + 88
    # brand footer
    s += ('  <text x="152" y="1060" font-family="' + WORDMARK_FONT + '" '
          'font-size="30" font-weight="600" fill="#7FB0C4" '
          'letter-spacing="1">sasystems.solutions</text>\n')
    s += "</svg>\n"
    return s


if __name__ == "__main__":
    write(os.path.join(IMG, "sa_systems_logo.svg"), gen_logo_light())
    write(os.path.join(IMG, "sa_systems_mark.svg"), gen_mark_square())
    write(os.path.join(IMG, "sa_systems_mark_dark.svg"), gen_mark_square(dark=True))
    write(os.path.join(IMG, "mediflow_logo.svg"), gen_icon())
    write(os.path.join(DESC, "logo.svg"), gen_logo_light())
    write(os.path.join(DESC, "mark.svg"), gen_mark_square())
    write(os.path.join(DESC, "icon.svg"), gen_icon())
    write(os.path.join(DESC, "banner.svg"), gen_banner())
    print("done")
