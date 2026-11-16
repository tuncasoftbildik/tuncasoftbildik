#!/usr/bin/env python3
"""Profile banner generator.

Edit CERTS below and run:  python3 tools/banner.py
Renders banner.png (1600x420 layout, exported at 1.5x) with headless Chrome.
Fonts: DIN Condensed + DIN Alternate (ship with macOS).
"""
import math
import pathlib
import random
import subprocess
import sys
import tempfile

W, H = 1600, 420
SCALE = 1.5
RADIUS = 20
ACCENT = "#00E084"
INK = "#07140f"

NAME = "TUNCA BILDIK"
TAGLINE = ["Travel Tech CTO", "Builder", "Cybersecurity"]
SKILLS = ["Ethical Hacking", "Network Defense", "Endpoint Security", "Threat Management"]
ISSUER = "CISCO NETWORKING ACADEMY"

# One entry per earned credential: (name, icon). The honeycomb has six slots
# around the shield; unused slots are drawn dashed ("next one goes here").
CERTS = [
    ("Junior Cybersecurity Analyst", "eye"),
    ("Ethical Hacker", "terminal"),
    ("Endpoint Security", "laptop"),
    ("Cyber Threat Management", "alert"),
    ("Network Defense", "network"),
]

# Stroke icons on a 24x24 grid (Lucide, ISC licence).
ICONS = {
    "eye": '<path d="M2.062 12.348a1 1 0 0 1 0-.696 10.75 10.75 0 0 1 19.876 0 1 1 0 0 1 0 .696 10.75 10.75 0 0 1-19.876 0"/><circle cx="12" cy="12" r="3"/>',
    "terminal": '<path d="m4 17 6-6-6-6"/><path d="M12 19h8"/>',
    "laptop": '<path d="M18 5a2 2 0 0 1 2 2v8.526a2 2 0 0 0 .212.897l1.068 2.127a1 1 0 0 1-.9 1.45H3.62a1 1 0 0 1-.9-1.45l1.068-2.127A2 2 0 0 0 4 15.526V7a2 2 0 0 1 2-2z"/><path d="M20.054 15.987H3.946"/>',
    "alert": '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
    "network": '<rect x="16" y="16" width="6" height="6" rx="1"/><rect x="2" y="16" width="6" height="6" rx="1"/><rect x="9" y="2" width="6" height="6" rx="1"/><path d="M5 16v-3a1 1 0 0 1 1-1h12a1 1 0 0 1 1 1v3"/><path d="M12 12V8"/>',
    "plus": '<path d="M5 12h14"/><path d="M12 5v14"/>',
}
SHIELD = "M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"
BOLT = "M13.3 5.6 8.2 13h3.3l-1 5.4 5.3-7.6h-3.4z"

# Honeycomb geometry (pointy-top hexagons around a centre cell).
CX, CY = 1336, 210
R = 63
GAP = 9
SLOT_ANGLES = [180, 240, 300, 120, 60, 0]  # W, NW, NE, SW, SE, E


def hex_path(cx, cy, r, corner=0.16):
    pts = [(cx + r * math.cos(math.radians(a)), cy + r * math.sin(math.radians(a)))
           for a in range(-90, 270, 60)]
    d = []
    for i, v in enumerate(pts):
        p, n = pts[i - 1], pts[(i + 1) % 6]
        a = (v[0] + (p[0] - v[0]) * corner, v[1] + (p[1] - v[1]) * corner)
        b = (v[0] + (n[0] - v[0]) * corner, v[1] + (n[1] - v[1]) * corner)
        d.append(f"{'M' if i == 0 else 'L'}{a[0]:.1f} {a[1]:.1f}Q{v[0]:.1f} {v[1]:.1f} {b[0]:.1f} {b[1]:.1f}")
    return "".join(d) + "Z"


def icon(name, cx, cy, size, stroke, width=1.7, opacity=1.0):
    s = size / 24
    return (f'<g transform="translate({cx - size / 2:.1f} {cy - size / 2:.1f}) scale({s:.3f})" fill="none" '
            f'stroke="{stroke}" stroke-width="{width}" stroke-linecap="round" stroke-linejoin="round" '
            f'opacity="{opacity}">{ICONS[name]}</g>')


def traces(seed=7):
    """Circuit traces: thin lines with a node at one end, denser to the right."""
    rnd = random.Random(seed)
    out = []
    for _ in range(58):
        x = rnd.triangular(40, W - 20, W * 0.72)
        y = rnd.uniform(8, H - 8)
        horizontal = rnd.random() < 0.66
        length = rnd.uniform(90, 360) if horizontal else rnd.uniform(60, 190)
        x2, y2 = (x + length, y) if horizontal else (x, y + length)
        op = rnd.uniform(0.10, 0.26) * (0.55 if x < 1050 else 1.0)
        nx, ny = (x2, y2) if rnd.random() < 0.6 else (x, y)
        out.append(f'<line x1="{x:.0f}" y1="{y:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" stroke="{ACCENT}" stroke-width="1" opacity="{op:.2f}"/>'
                   f'<circle cx="{nx:.0f}" cy="{ny:.0f}" r="2.6" fill="{ACCENT}" opacity="{min(op * 1.9, 0.6):.2f}"/>')
    return "".join(out)


def honeycomb():
    dist = math.sqrt(3) * R + GAP
    cells = []
    for i, ang in enumerate(SLOT_ANGLES):
        x = CX + dist * math.cos(math.radians(ang))
        y = CY + dist * math.sin(math.radians(ang))
        if i < len(CERTS):
            cells.append(
                f'<path d="{hex_path(x, y, R)}" fill="url(#cell)" stroke="{ACCENT}" stroke-opacity=".62" stroke-width="1.6"/>'
                + icon(CERTS[i][1], x, y, 44, "#eafff5", 1.6))
        else:
            cells.append(
                f'<path d="{hex_path(x, y, R)}" fill="none" stroke="{ACCENT}" stroke-opacity=".42" stroke-width="1.6" stroke-dasharray="7 8"/>'
                + icon("plus", x, y, 30, ACCENT, 1.8, 0.55))
    s = 104 / 24  # shield size in the centre cell
    centre = (
        f'<path d="{hex_path(CX, CY, R)}" fill="rgba(0,224,132,.16)" stroke="{ACCENT}" stroke-width="2"/>'
        f'<g transform="translate({CX - 52:.1f} {CY - 53:.1f}) scale({s:.3f})" filter="url(#glow)">'
        f'<path d="{SHIELD}" fill="{ACCENT}"/><path d="{BOLT}" fill="{INK}"/></g>')
    return "".join(cells) + centre


def svg():
    sep = f'<tspan dx="16" dy="-1" fill="{ACCENT}" opacity=".9">•</tspan><tspan dx="16" dy="1">'
    tagline = TAGLINE[0] + "".join(f"{sep}{t}</tspan>" for t in TAGLINE[1:])
    gsep = '<tspan dx="12" fill="#5c6877">•</tspan><tspan dx="12">'
    skills = SKILLS[0] + "".join(f"{gsep}{t}</tspan>" for t in SKILLS[1:])
    n = len(CERTS)
    eyebrow = f"{n} × {ISSUER} CREDENTIALS"
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">
<defs>
  <linearGradient id="bg" x1="0" x2="1" y1="0" y2="0">
    <stop offset="0" stop-color="#0a0d13"/><stop offset=".58" stop-color="#0b1117"/>
    <stop offset=".8" stop-color="#0b2a20"/><stop offset="1" stop-color="#0d4631"/>
  </linearGradient>
  <radialGradient id="halo" cx="{CX}" cy="{CY}" r="330" gradientUnits="userSpaceOnUse">
    <stop offset="0" stop-color="{ACCENT}" stop-opacity=".30"/><stop offset=".45" stop-color="{ACCENT}" stop-opacity=".10"/>
    <stop offset="1" stop-color="{ACCENT}" stop-opacity="0"/>
  </radialGradient>
  <linearGradient id="cell" x1="0" x2="0" y1="0" y2="1">
    <stop offset="0" stop-color="#0f2b22" stop-opacity=".96"/><stop offset="1" stop-color="#0a1a16" stop-opacity=".96"/>
  </linearGradient>
  <filter id="glow" x="-60%" y="-60%" width="220%" height="220%">
    <feGaussianBlur in="SourceGraphic" stdDeviation="2.2" result="b"/>
    <feColorMatrix in="b" values="0 0 0 0 0  0 0 0 0 .88  0 0 0 0 .52  0 0 0 .75 0" result="g"/>
    <feMerge><feMergeNode in="g"/><feMergeNode in="SourceGraphic"/></feMerge>
  </filter>
  <clipPath id="card"><rect width="{W}" height="{H}" rx="{RADIUS}"/></clipPath>
  <style>
    .h {{ font-family: "DIN Condensed", "DIN Alternate", sans-serif; font-weight: 700; }}
    .t {{ font-family: "DIN Alternate", "DIN Condensed", sans-serif; font-weight: 700; }}
  </style>
</defs>
<g clip-path="url(#card)">
<rect width="{W}" height="{H}" fill="url(#bg)"/>
{traces()}
<rect width="{W}" height="{H}" fill="url(#halo)"/>
<g fill="none" stroke="{ACCENT}" stroke-opacity=".10">
  <circle cx="{CX}" cy="{CY}" r="215"/><circle cx="{CX}" cy="{CY}" r="262" stroke-dasharray="2 10"/>
</g>
{honeycomb()}

<g transform="translate(92 68)">
  <g transform="scale(.92)" fill="none" stroke="{ACCENT}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
    <path d="{SHIELD}"/><path d="m9 12 2 2 4-4"/>
  </g>
  <text class="t" x="32" y="17.5" font-size="19" letter-spacing="3.1" fill="#8fe9c0">{eyebrow}</text>
</g>
<text class="h" x="92" y="235" font-size="158" fill="#ffffff" letter-spacing="1">{NAME}</text>
<rect x="92" y="249" width="122" height="5" rx="2.5" fill="{ACCENT}"/>
<text class="t" x="92" y="302" font-size="39" fill="{ACCENT}">{tagline}</text>
<text class="t" x="92" y="348" font-size="25" fill="#aab3bf">{skills}</text>
</g>
</svg>'''


def main():
    out = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else pathlib.Path(__file__).resolve().parent.parent / "banner.png")
    html = ('<!doctype html><meta charset="utf-8"><style>html,body{margin:0;background:transparent;overflow:hidden}'
            'svg{display:block}</style>' + svg())
    with tempfile.TemporaryDirectory() as tmp:
        page = pathlib.Path(tmp) / "banner.html"
        page.write_text(html, encoding="utf-8")
        chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
        subprocess.run([
            chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
            "--default-background-color=00000000",
            f"--user-data-dir={tmp}/profile", f"--window-size={W},{H}",
            f"--force-device-scale-factor={SCALE}", f"--screenshot={out}", page.as_uri(),
        ], check=True, capture_output=True)
    try:  # lossless recompression, optional
        from PIL import Image
        Image.open(out).save(out, optimize=True, compress_level=9)
    except ImportError:
        pass
    print(f"{out} ({out.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
