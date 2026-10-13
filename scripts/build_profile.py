#!/usr/bin/env python3
"""Build assets/profile.svg, the whole profile card, in one pass.

  header      name, tagline and the "now shipping" ticker (items come from now.txt)
  projects    three panels, each with one headline and one figure
  timeline    how I got here, in code

Edit now.txt for the ticker, or the PROJECTS and STOPS text below, then run from the repo root:
    python3 scripts/build_profile.py
The GitHub workflow runs this whenever now.txt or this script changes.
"""
import json
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parent.parent
NOW = ROOT / "now.txt"
CURVES = ROOT / "scripts" / "data" / "equity_curves.json"
OUT = ROOT / "assets" / "profile.svg"

W = 1200
INK, SOFT, MUTED, FAINT = "#F4F7FB", "#C9D3E0", "#8A97A8", "#FFFFFF"
GREEN, BLUE, AMBER = "#3DF5B0", "#7AA2FF", "#FFB547"
SANS = "font-family=\"'Segoe UI', Ubuntu, 'Helvetica Neue', Arial, sans-serif\""

# ---------------------------------------------------------------- text you may want to edit
NAME = "Waseem"
HANDLE, SCHOOL = "~/wabuein", "MSc Financial Technology, Imperial"
TAGLINE = "I build systems end to end, then try to break them."

PROJECTS = [
    # kicker, headline, footer (repo and context), figure
    ("QUANT RESEARCH", "Found the bug that faked a +110R edge.", "fx-research · 12 FX pairs · 2015 to 2026", "fx"),
    ("AI COMPUTER VISION", "A camera and an AI model sort real objects.", "CBD · Best Project Prize, 82%", "cbd"),
    ("PRODUCT AND REVENUE", "Turned a game server into a business.", "SurfPractice · Java · PvP Surf", "surf"),
]

STOPS = [  # year, title, tools, colour
    ("2020", "Minecraft plugins", "Java", "#7AA2FF"),
    ("2021", "Game backends", "Redis · MongoDB", "#6FAAF6"),
    ("2024", "Data analysis", "pandas · NumPy", "#62BCE6"),
    ("2025", "Fitsylvania", "Next.js · Stripe", "#56CCD8"),
    ("2026", "AI vision sorter", "Python · computer vision", "#49DCC4"),
    ("now", "Quant research", "Python · pytest", "#3DF5B0"),
]

# ---------------------------------------------------------------- layout
HEADER_H = 236
PANEL_Y, PANEL_H, PANEL_W, GAP = 286, 246, 360, 24
PANEL_X = [(W - 3 * PANEL_W - 2 * GAP) // 2 + i * (PANEL_W + GAP) for i in range(3)]
TL_LABEL_Y = PANEL_Y + PANEL_H + 56
TL_Y = TL_LABEL_Y + 70
H = TL_Y + 92
TL_X0, TL_X1 = 120, 1080

TICK_SLOT = 3.5   # seconds each ticker item stays up
CBD_LOOP = 10     # seconds per pass of the sorter animation


def t(x, y, text, size, fill, *, cls="", weight=None, anchor=None, extra=""):
    attrs = f'x="{x}" y="{y}" font-size="{size}" fill="{fill}"'
    if weight: attrs += f' font-weight="{weight}"'
    if anchor: attrs += f' text-anchor="{anchor}"'
    c = f' class="{cls}"' if cls else ""
    return f"<text{c} {attrs}{extra}>{escape(text)}</text>"


def read_now():
    label, items = "now shipping", []
    for raw in NOW.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.lower().startswith("label:"):
            label = line.split(":", 1)[1].strip() or label
        else:
            items.append(line)
    if not items:
        raise SystemExit("now.txt has no items. Add at least one line.")
    return label, items


# ---------------------------------------------------------------- header
def header():
    label, items = read_now()
    n, x, y, size = len(items), 64, 212, 14
    item_x = x + round((len(label) + 1) * size * 0.6)
    css = ""
    if n > 1:
        p = 100 / n
        f = lambda v: f"{v:.3f}".rstrip("0").rstrip(".")
        css = (f"      .tk {{ opacity: 0; animation: tick {TICK_SLOT * n:g}s cubic-bezier(.3,.7,.2,1) infinite both; }}\n"
               "      @keyframes tick { 0% { opacity: 0; transform: translateY(16px); }"
               f" {f(p * .12)}% {{ opacity: 1; transform: translateY(0); }} {f(p)}% {{ opacity: 1; transform: translateY(0); }}"
               f" {f(p * 1.12)}%, 100% {{ opacity: 0; transform: translateY(-16px); }} }}\n")
    rows = "\n".join(
        f'        <g{f" class=\"tk\" style=\"animation-delay: {TICK_SLOT * i:g}s\"" if n > 1 else ""}>'
        f'{t(item_x, y, item, size, GREEN, cls="mono")}</g>' for i, item in enumerate(items))
    svg = f'''    <!-- header -->
    <text class="mono rise" style="animation-delay: .1s" x="66" y="64" font-size="15" letter-spacing=".5"><tspan fill="{GREEN}">{escape(HANDLE)}</tspan><tspan fill="{MUTED}">  ·  {escape(SCHOOL)}</tspan></text>
    {t(60, 134, NAME, 64, INK, cls="sans rise", weight="700", extra=' letter-spacing="-1.5" style="animation-delay: .3s"')}
    {t(64, 176, TAGLINE, 22, SOFT, cls="sans rise", extra=' style="animation-delay: .5s"')}
    <clipPath id="ticker"><rect x="{item_x - 4}" y="{y - 20}" width="{W - item_x - 64}" height="28"/></clipPath>
    <g class="rise" style="animation-delay: .7s">
      {t(x, y, label, size, MUTED, cls="mono")}
      <g clip-path="url(#ticker)">
{rows}
      </g>
    </g>'''
    return css, svg, label, items


# ---------------------------------------------------------------- project figures
def fig_fx(px, top, w):
    data = json.loads(CURVES.read_text(encoding="utf-8"))
    n = len(data["causal"])
    x0, x1, y0, y1 = px + 22, px + w - 58, top + 26, top + 118
    rmin, rmax = -70, 170
    sx = lambda i: x0 + (x1 - x0) * i / (n - 1)
    sy = lambda r: y1 - (y1 - y0) * (r - rmin) / (rmax - rmin)
    path = lambda v: "M" + " L".join(f"{sx(i):.1f} {sy(r):.1f}" for i, r in enumerate(v))
    lx, ly, cy = sx(n - 1), sy(data["leaky"][-1]), sy(data["causal"][-1])
    return f'''      <g class="mono" font-size="11" fill="{SOFT}">
        <rect x="{x0}" y="{top + 2}" width="12" height="3" rx="1.5" fill="{AMBER}"/>{t(x0 + 17, top + 7, "backtest with bug", 11, SOFT)}
        <rect x="{x0 + 150}" y="{top + 2}" width="12" height="3" rx="1.5" fill="{GREEN}"/>{t(x0 + 167, top + 7, "bug fixed", 11, SOFT)}
      </g>
      <line x1="{x0}" y1="{sy(0):.1f}" x2="{x1}" y2="{sy(0):.1f}" stroke="{FAINT}" stroke-opacity=".16" stroke-dasharray="3 4"/>
      <path class="eq" pathLength="1" d="{path(data['leaky'])}" fill="none" stroke="{AMBER}" stroke-width="2" stroke-linejoin="round" stroke-opacity=".9"/>
      <path class="eq" pathLength="1" d="{path(data['causal'])}" fill="none" stroke="{GREEN}" stroke-width="2.3" stroke-linejoin="round"/>
      <g class="eqend mono" font-size="12" font-weight="700">
        <circle cx="{lx:.1f}" cy="{ly:.1f}" r="3" fill="{AMBER}"/>{t(f"{lx + 8:.1f}", f"{ly + 4:.1f}", "+110R", 12, AMBER)}
        <circle cx="{lx:.1f}" cy="{cy:.1f}" r="3" fill="{GREEN}"/>{t(f"{lx + 8:.1f}", f"{cy + 4:.1f}", "-42R", 12, GREEN)}
      </g>'''


def fig_cbd(px, top, w):
    # the README's own example rule: apple, red, min confidence 0.4, path C5
    belt_y, cam_x, gate_x = top + 96, px + 128, px + 248
    item_r, start_x = 11, px + 34
    return f'''      <!-- conveyor -->
      <line x1="{px + 22}" y1="{belt_y}" x2="{gate_x}" y2="{belt_y}" stroke="{SOFT}" stroke-opacity=".35" stroke-width="3" stroke-linecap="round"/>
      <circle cx="{px + 26}" cy="{belt_y + 7}" r="5" fill="none" stroke="{SOFT}" stroke-opacity=".3"/>
      <circle cx="{gate_x - 4}" cy="{belt_y + 7}" r="5" fill="none" stroke="{SOFT}" stroke-opacity=".3"/>
      <!-- camera and its field of view -->
      <rect x="{cam_x - 13}" y="{top + 8}" width="26" height="16" rx="3" fill="none" stroke="{BLUE}" stroke-width="1.6"/>
      <circle cx="{cam_x}" cy="{top + 16}" r="4" fill="none" stroke="{BLUE}" stroke-width="1.4"/>
      <path d="M{cam_x - 6} {top + 25} L{cam_x - 30} {belt_y - 4} M{cam_x + 6} {top + 25} L{cam_x + 30} {belt_y - 4}" stroke="{BLUE}" stroke-opacity=".28" stroke-dasharray="3 3"/>
      {t(cam_x + 20, top + 20, "camera", 11, MUTED, cls="mono")}
      <!-- the item travels along the belt, gets classified, then is routed -->
      <g class="cbd-item">
        <circle cx="{start_x}" cy="{belt_y - item_r - 2}" r="{item_r}" fill="#FF6B6B"/>
        <path d="M{start_x + 1} {belt_y - 2 * item_r - 2} q3 -6 7 -6" stroke="#7BD88F" stroke-width="2" fill="none"/>
      </g>
      <g class="cbd-box">
        <rect x="{cam_x - 17}" y="{belt_y - 2 * item_r - 9}" width="34" height="{2 * item_r + 6}" rx="3" fill="none" stroke="{GREEN}" stroke-width="1.6"/>
        {t(cam_x - 17, belt_y - 2 * item_r - 13, "apple · red", 11, GREEN, cls="mono")}
      </g>
      <!-- diverter gate and the destination lane -->
      <line class="cbd-gate" x1="{gate_x}" y1="{belt_y - 1}" x2="{gate_x + 28}" y2="{belt_y - 1}" stroke="{SOFT}" stroke-width="3" stroke-linecap="round"/>
      <path d="M{gate_x + 14} {belt_y + 18} h{w - (gate_x - px) - 40}" stroke="{SOFT}" stroke-opacity=".2" stroke-width="2"/>
      {t(gate_x + 6, belt_y + 30, "path C5", 11, MUTED, cls="mono", anchor="end")}'''


def fig_cbd_css(px, top):
    cam_x, gate_x, start_x = px + 128, px + 248, px + 34
    to_cam, to_gate = cam_x - start_x, gate_x - start_x + 22
    return (f"      .cbd-item {{ animation: cbd-item {CBD_LOOP}s cubic-bezier(.45,.05,.3,1) 1s infinite both; }}\n"
            "      @keyframes cbd-item { 0% { transform: translate(0,0); opacity: 0; } 4% { opacity: 1; }"
            f" 22%, 40% {{ transform: translate({to_cam}px,0); }} 58% {{ transform: translate({to_gate}px,0); }}"
            f" 66% {{ transform: translate({to_gate + 34}px,28px); opacity: 1; }} 74%, 100% {{ transform: translate({to_gate + 34}px,28px); opacity: 0; }} }}\n"
            f"      .cbd-box {{ opacity: 0; animation: cbd-box {CBD_LOOP}s ease 1s infinite both; }}\n"
            "      @keyframes cbd-box { 0%, 23% { opacity: 0; } 27%, 39% { opacity: 1; } 43%, 100% { opacity: 0; } }\n"
            f"      .cbd-gate {{ transform-box: fill-box; transform-origin: 0 50%; animation: cbd-gate {CBD_LOOP}s ease 1s infinite both; }}\n"
            "      @keyframes cbd-gate { 0%, 44% { transform: rotate(0deg); } 52%, 70% { transform: rotate(38deg); } 78%, 100% { transform: rotate(0deg); } }\n")


def fig_surf(px, top, w):
    cx = px + 22
    return f'''      <text class="sans pop" x="{cx}" y="{top + 62}"><tspan font-size="46" font-weight="700" fill="{INK}" letter-spacing="-1">USD 1,200</tspan><tspan font-size="17" fill="{MUTED}" dx="12">a month</tspan></text>
      <g class="pop2">
        <rect x="{cx}" y="{top + 84}" width="{w - 44}" height="1" fill="{FAINT}" fill-opacity=".1"/>
        {t(cx, top + 110, "100+ users on a multiplayer platform", 13, GREEN, cls="mono")}
      </g>'''


def projects():
    css = (".eq { stroke-dasharray: 1; stroke-dashoffset: 1; animation: draw-eq 3s cubic-bezier(.45,.05,.3,1) 1.2s forwards; }\n"
           "      @keyframes draw-eq { to { stroke-dashoffset: 0; } }\n"
           "      .eqend { opacity: 0; animation: fade .6s ease 4.1s forwards; }\n"
           "      .pop { opacity: 0; animation: rise .8s cubic-bezier(.2,.7,.2,1) 1.4s forwards; }\n"
           "      .pop2 { opacity: 0; animation: rise .8s cubic-bezier(.2,.7,.2,1) 1.8s forwards; }\n"
           "      @keyframes fade { to { opacity: 1; } }\n")
    out = [f'    <!-- selected work -->\n    {t(PANEL_X[0], PANEL_Y - 18, "SELECTED WORK", 13, MUTED, cls="mono rise", extra=" letter-spacing=\"2\" style=\"animation-delay: .9s\"")}']
    for (kicker, headline, footer, fig), px in zip(PROJECTS, PANEL_X):
        top = PANEL_Y + 74
        body = {"fx": fig_fx, "cbd": fig_cbd, "surf": fig_surf}[fig](px, top, PANEL_W)
        if fig == "cbd":
            css += "      " + fig_cbd_css(px, top).lstrip()
        out.append(f'''    <g class="rise" style="animation-delay: 1s">
      <rect x="{px}" y="{PANEL_Y}" width="{PANEL_W}" height="{PANEL_H}" rx="14" fill="{FAINT}" fill-opacity=".025" stroke="{FAINT}" stroke-opacity=".08"/>
      {t(px + 22, PANEL_Y + 32, kicker, 11, MUTED, cls="mono", extra=' letter-spacing="1.5"')}
      {t(px + 22, PANEL_Y + 58, headline, 15, INK, cls="sans", weight="600")}
    </g>
    <g>
{body}
    </g>
    {t(px + 22, PANEL_Y + PANEL_H - 20, footer, 11, FAINT, cls="mono", extra=' fill-opacity=".4"')}''')
    return css, "\n".join(out)


# ---------------------------------------------------------------- timeline
def timeline():
    xs = [round(TL_X0 + (TL_X1 - TL_X0) * i / (len(STOPS) - 1)) for i in range(len(STOPS))]
    length = TL_X1 - TL_X0
    t0 = 1.6
    css = (f".draw {{ stroke-dasharray: {length}; stroke-dashoffset: {length}; animation: draw 3s cubic-bezier(.45,.05,.25,1) {t0}s forwards; }}\n"
           "      @keyframes draw { to { stroke-dashoffset: 0; } }\n"
           "      .stop { opacity: 0; animation: rise .6s cubic-bezier(.2,.8,.2,1.2) forwards; }\n")
    out = [f'''    <!-- timeline -->
    {t(PANEL_X[0], TL_LABEL_Y, "HOW I GOT HERE, IN CODE", 13, MUTED, cls="mono rise", extra=f' letter-spacing="2" style="animation-delay: {t0}s"')}
    <line x1="{TL_X0}" y1="{TL_Y}" x2="{TL_X1}" y2="{TL_Y}" stroke="{FAINT}" stroke-opacity=".08" stroke-width="4" stroke-linecap="round"/>
    <line class="draw" x1="{TL_X0}" y1="{TL_Y}" x2="{TL_X1}" y2="{TL_Y}" stroke="url(#track)" stroke-width="4" stroke-linecap="round"/>''']
    for i, ((year, title, tools, c), x) in enumerate(zip(STOPS, xs)):
        last = i == len(STOPS) - 1
        dot = f'<circle cx="{x}" cy="{TL_Y}" r="9" fill="{c}"/>' if last else \
              f'<circle cx="{x}" cy="{TL_Y}" r="9" fill="#0A0F1A" stroke="{c}" stroke-width="3"/>'
        out.append(f'''    <g class="stop" style="animation-delay: {t0 + i * .5:.2f}s">
      {t(x, TL_Y - 26, year, 14, c, cls="mono", anchor="middle")}
      {dot}
      {t(x, TL_Y + 44, title, 17, INK, cls="sans", weight="700", anchor="middle")}
      {t(x, TL_Y + 68, tools, 12, c, cls="mono", anchor="middle")}
    </g>''')
    return css, "\n".join(out)


# ---------------------------------------------------------------- assemble
def build():
    h_css, h_svg, label, items = header()
    p_css, p_svg = projects()
    tl_css, tl_svg = timeline()
    work = "; ".join(f"{k.capitalize()}: {h} ({f})" for k, h, f, _ in PROJECTS)
    path = " ".join(f"{y}: {ti} ({to.replace(' · ', ', ')})." for y, ti, to, _ in STOPS)
    aria = escape(f"{NAME}, {SCHOOL}. {TAGLINE} {label}: {', '.join(items)}. Selected work. {work}. "
                  f"The FX chart shows the same strategy ending at +110R with the bug and -42R with it fixed. "
                  f"How I got here, in code. {path}", {'"': "&quot;"})
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-label="{aria}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2=".35" y2="1">
      <stop offset="0" stop-color="#0A0F1A"/>
      <stop offset="1" stop-color="#0E1A24"/>
    </linearGradient>
    <radialGradient id="glow" cx=".85" cy=".1" r=".55">
      <stop offset="0" stop-color="{GREEN}" stop-opacity=".09"/>
      <stop offset="1" stop-color="{GREEN}" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="track" gradientUnits="userSpaceOnUse" x1="{TL_X0}" y1="0" x2="{TL_X1}" y2="0">
      <stop offset="0" stop-color="{BLUE}"/>
      <stop offset="1" stop-color="{GREEN}"/>
    </linearGradient>
    <pattern id="grid" width="24" height="24" patternUnits="userSpaceOnUse">
      <path d="M24 0H0V24" fill="none" stroke="{FAINT}" stroke-opacity=".045"/>
    </pattern>
    <clipPath id="card"><rect width="{W}" height="{H}" rx="18"/></clipPath>
    <style>
      .sans {{ font-family: 'Segoe UI', Ubuntu, 'Helvetica Neue', Arial, sans-serif; }}
      .mono {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace; }}
      .rise {{ opacity: 0; animation: rise .8s cubic-bezier(.2,.7,.2,1) forwards; }}
      @keyframes rise {{ from {{ opacity: 0; transform: translateY(8px); }} to {{ opacity: 1; transform: translateY(0); }} }}
{h_css}      {p_css}      {tl_css}    </style>
  </defs>
  <g clip-path="url(#card)">
    <rect width="{W}" height="{H}" fill="url(#bg)"/>
    <rect width="{W}" height="{H}" fill="url(#grid)"/>
    <rect width="{W}" height="{H}" fill="url(#glow)"/>
{h_svg}

{p_svg}

{tl_svg}
  </g>
</svg>
'''
    OUT.write_text(svg, encoding="utf-8")
    print(f"Wrote {OUT.relative_to(ROOT)} ({W}x{H}), {len(items)} ticker item(s).")


if __name__ == "__main__":
    build()
