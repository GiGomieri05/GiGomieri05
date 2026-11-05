#!/usr/bin/env python3
"""
Generates every animated SVG used in the profile README.

    python3 scripts/build_profile_svgs.py

Output goes to profile/anim/. Everything is hand-made SVG + CSS/SMIL
animation, so it runs inside GitHub's <img> sandbox with no external
service, no JavaScript and no web fonts.

Tweak the constants (texts, timings, colors) and re-run.
"""

from __future__ import annotations

import math
import random
from pathlib import Path
from xml.sax.saxutils import escape

OUT = Path(__file__).resolve().parent.parent / "profile" / "anim"

# ── palette (GitHub dark) ────────────────────────────────────────────────
BG = "#0d1117"
PANEL = "#0b0f17"
BORDER = "#30363d"
TEXT = "#c9d1d9"
MUTED = "#8b949e"
DIM = "#484f58"
BLUE = "#58a6ff"
GREEN = "#3fb950"
ORANGE = "#f0883e"
YELLOW = "#e3b341"
RED = "#ff7b72"
PURPLE = "#bc8cff"

MONO = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', 'DejaVu Sans Mono', monospace"


# ── helpers ──────────────────────────────────────────────────────────────
def pct(t: float, total: float) -> str:
    return f"{max(0.0, min(100.0, t / total * 100)):.3f}%"


def keyframes(name: str, total: float, points: list[tuple[float, str]]) -> str:
    """points = [(seconds, 'css declarations'), ...] → @keyframes block."""
    pts = sorted(points, key=lambda p: p[0])
    if pts[0][0] > 0:
        pts.insert(0, (0, pts[0][1]))
    if pts[-1][0] < total:
        pts.append((total, pts[-1][1]))
    body = " ".join(f"{pct(t, total)}{{{css}}}" for t, css in pts)
    return f"@keyframes {name}{{{body}}}"


def windows_kf(name: str, total: float, wins: list[tuple[float, float]], fade: float = 0.0) -> str:
    """Opacity 1 inside each (start, end) window, 0 elsewhere."""
    eps = 0.01
    pts: list[tuple[float, str]] = [(0, "opacity:0")]
    for a, b in wins:
        f = fade or eps
        if a <= 0:
            pts = [(0, "opacity:1")]
        else:
            pts += [(max(0, a - f), "opacity:0"), (a, "opacity:1")]
        if b >= total:
            pts.append((total, "opacity:1"))
        else:
            pts += [(b, "opacity:1"), (min(total, b + f), "opacity:0")]
    return keyframes(name, total, pts)


def mono(x: float, y: float, s: str, cw: float, cls: str = "", fill: str | None = None,
         size: float | None = None, weight: str | None = None, anchor_col: int = 0,
         extra: str = "") -> str:
    """Monospace text with every glyph forced onto a cw-wide grid (textLength),
    so ASCII art lines up no matter which monospace font the viewer has."""
    lead = len(s) - len(s.lstrip(" "))
    body = s.strip(" ")
    if not body:
        return ""
    xx = x + (lead - anchor_col) * cw
    attrs = [f'x="{xx:.2f}"', f'y="{y:.2f}"', f'textLength="{len(body) * cw:.2f}"',
             'lengthAdjust="spacingAndGlyphs"']
    if cls:
        attrs.append(f'class="{cls}"')
    if fill:
        attrs.append(f'fill="{fill}"')
    if size:
        attrs.append(f'font-size="{size}"')
    if weight:
        attrs.append(f'font-weight="{weight}"')
    if extra:
        attrs.append(extra)
    return f'<text {" ".join(attrs)} xml:space="preserve">{escape(body)}</text>'


def svg_doc(w: int, h: int, title: str, css: str, body: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
        f'role="img" aria-label="{escape(title)}">\n<title>{escape(title)}</title>\n'
        f"<style>\n"
        f"text{{font-family:{MONO};}}\n"
        f".m{{fill:{MUTED}}} .d{{fill:{DIM}}} .t{{fill:{TEXT}}} .b{{fill:{BLUE}}} .g{{fill:{GREEN}}} "
        f".o{{fill:{ORANGE}}} .y{{fill:{YELLOW}}} .r{{fill:{RED}}} .p{{fill:{PURPLE}}}\n"
        f"@keyframes blink{{0%,49%{{opacity:1}}50%,100%{{opacity:0}}}}\n"
        f"@keyframes twinkle{{0%,100%{{opacity:.25}}50%{{opacity:1}}}}\n"
        f".blink{{animation:blink 1.05s steps(1,end) infinite}}\n"
        f"{css}\n</style>\n{body}\n</svg>\n"
    )


def card(w: int, h: int, x: float = 0.5, y: float = 0.5, r: int = 14, fill: str = BG) -> str:
    return f'<rect x="{x}" y="{y}" width="{w - 2 * x}" height="{h - 2 * y}" rx="{r}" fill="{fill}" stroke="{BORDER}"/>'


def starfield(rng: random.Random, n: int, x0: float, y0: float, x1: float, y1: float, cls_prefix: str) -> tuple[str, str]:
    css, out = [], []
    for i in range(n):
        x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
        r = rng.choice([0.6, 0.8, 0.8, 1.0, 1.3])
        dur = rng.uniform(2.2, 5.5)
        delay = -rng.uniform(0, 5)
        col = rng.choice([TEXT, TEXT, TEXT, BLUE, "#a5d6ff"])
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{col}" '
                   f'style="animation:twinkle {dur:.2f}s ease-in-out {delay:.2f}s infinite"/>')
    return "\n".join(out), "\n".join(css)


# ═════════════════════════════════════════════════════════════════════════
# 1. HERO — ASCII rocket launch + pilot card
# ═════════════════════════════════════════════════════════════════════════
def build_hero() -> str:
    W, H, T = 840, 400, 14.0
    rng = random.Random(488)
    css: list[str] = []
    body: list[str] = [card(W, H)]

    # ── scene panel ──
    px, py, pw, ph = 16, 16, 392, 368
    body.append(f'<defs><clipPath id="scene"><rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="10"/></clipPath>'
                f'<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">'
                f'<stop offset="0" stop-color="#060a12"/><stop offset="1" stop-color="#101826"/></linearGradient>'
                f'<linearGradient id="trail" x1="0" y1="1" x2="0" y2="0">'
                f'<stop offset="0" stop-color="{ORANGE}" stop-opacity=".0"/>'
                f'<stop offset=".15" stop-color="{ORANGE}" stop-opacity=".55"/>'
                f'<stop offset="1" stop-color="{YELLOW}" stop-opacity=".9"/></linearGradient>'
                f'<linearGradient id="fadeTop" x1="0" y1="0" x2="0" y2="1">'
                f'<stop offset="0" stop-color="#060a12"/><stop offset=".55" stop-color="#060a12" stop-opacity=".85"/>'
                f'<stop offset="1" stop-color="#060a12" stop-opacity="0"/></linearGradient>'
                f'<linearGradient id="gauge" x1="0" y1="1" x2="0" y2="0">'
                f'<stop offset="0" stop-color="{GREEN}"/><stop offset="1" stop-color="{BLUE}"/></linearGradient>'
                f'</defs>')
    body.append(f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" rx="10" fill="url(#sky)" stroke="{BORDER}"/>')
    body.append('<g clip-path="url(#scene)">')

    # flight profile: altitude fraction u(t) for 5.5s → 9.0s (quadratic ease-in)
    t_lift, t_apo, t_reset = 5.5, 9.0, 13.2
    travel = 360.0
    samples = [t_lift + i * (t_apo - t_lift) / 14 for i in range(15)]

    def frac(t: float) -> float:
        return ((t - t_lift) / (t_apo - t_lift)) ** 2

    # stars (parallax: drift down while the "camera" follows the rocket)
    stars, _ = starfield(rng, 46, px + 6, py - 70, px + pw - 40, py + 250, "s")
    body.append(f'<g style="animation:parallax {T}s linear infinite">{stars}</g>')
    par = [(0, "transform:translateY(0px);opacity:1")]
    par += [(t, f"transform:translateY({70 * frac(t):.2f}px);opacity:1") for t in samples]
    par += [(t_reset - 0.4, "transform:translateY(70px);opacity:1"), (t_reset, "transform:translateY(70px);opacity:0"),
            (t_reset + 0.01, "transform:translateY(0px);opacity:0"), (T, "transform:translateY(0px);opacity:1")]
    css.append(keyframes("parallax", T, par))

    # moon
    body.append(f'<circle cx="{px + 262}" cy="{py + 96}" r="15" fill="#1b2433"/>'
                f'<circle cx="{px + 268}" cy="{py + 91}" r="15" fill="url(#sky)"/>')

    # geometry
    fs, cw, lh = 13, 7.8, 14.0
    cx = px + pw / 2 - 28            # rocket centre line
    col_c = 7                         # centre column of the art
    x0 = cx - (col_c + 0.5) * cw
    top = 140.0
    rocket = [
        "       .",
        "      / \\",
        "     /   \\",
        "    /_____\\",
        "    |     |",
        "    |  O  |",
        "    |     |",
        "    | RDB |",
        "    |     |",
        "   /|     |\\",
        "  / |     | \\",
        " /__|_____|__\\",
        "     /___\\",
    ]
    rocket_cls = ["y", "t", "t", "t", "t", "b", "t", "o", "t", "t", "t", "t", "m"]
    nozzle_y = top + (len(rocket) - 1) * lh
    ground_y = nozzle_y + 3 * lh + 6

    # tower (left) with retracting arm
    tx = x0 - 6 * cw
    for i in range(0, int((ground_y - top) / lh) + 1):
        y = top + 2 * lh + i * lh
        if y > ground_y - 4:
            break
        body.append(mono(tx, y, "|X|", cw, "d", size=fs))
    body.append(f'<g style="animation:arm {T}s linear infinite">'
                + mono(tx + 3 * cw, top + 5 * lh, "==", cw, "m", size=fs)
                + mono(tx + 3 * cw, top + 9 * lh, "==", cw, "m", size=fs) + "</g>")
    css.append(windows_kf("arm", T, [(0, 3.0), (t_reset + 0.2, T)], fade=0.25))

    # exhaust trail (grows with the rocket, then dissipates)
    trail_bottom = ground_y - 4
    body.append(f'<rect x="{cx - 2.5:.1f}" y="{trail_bottom - travel:.1f}" width="5" height="{travel:.1f}" rx="2.5" '
                f'fill="url(#trail)" style="transform-box:fill-box;transform-origin:50% 100%;'
                f'animation:trail {T}s linear infinite"/>')
    tr = [(0, "transform:scaleY(0);opacity:0"), (t_lift, "transform:scaleY(0);opacity:1")]
    tr += [(t, f"transform:scaleY({frac(t):.3f});opacity:1") for t in samples]
    tr += [(t_apo + 0.3, "transform:scaleY(1);opacity:.8"), (11.2, "transform:scaleY(1);opacity:0"),
           (T, "transform:scaleY(0);opacity:0")]
    css.append(keyframes("trail", T, tr))

    # rocket + flames (move together)
    rk = ['<g style="animation:fly {T}s linear infinite">'.replace("{T}", str(T))]
    details = {5: ("       O", "b"), 7: ("      RDB", "o")}   # coloured overlays inside the body
    for i, (line, c) in enumerate(zip(rocket, rocket_cls)):
        y = top + i * lh
        if i in details:
            rk.append(mono(x0, y, "    |     |", cw, "t", size=fs, weight="700"))
            s, dc = details[i]
            rk.append(mono(x0, y, s, cw, dc, size=fs, weight="700"))
        else:
            rk.append(mono(x0, y, line, cw, c, size=fs, weight="700"))
    flames = [
        ["     (\\|/)", "      \\|/", "       '"],
        ["     )/|\\(", "      /|\\", "       :"],
        ["     \\\\|//", "      )|(", "       V"],
    ]
    rk.append(f'<g style="animation:ign {T}s linear infinite">')
    for k, fr in enumerate(flames):
        rk.append(f'<g style="animation:flick .36s steps(1,end) {-0.12 * k:.2f}s infinite">')
        for j, (ln, c) in enumerate(zip(fr, ["y", "o", "r"])):
            rk.append(mono(x0, nozzle_y + (j + 1) * lh, ln, cw, c, size=fs, weight="700"))
        rk.append("</g>")
    rk.append("</g></g>")
    body.append("\n".join(rk))
    css.append("@keyframes flick{0%{opacity:1}33.3%{opacity:0}100%{opacity:0}}")
    css.append(windows_kf("ign", T, [(4.5, t_apo + 0.2)]))
    fly = [(0, "transform:translate(0px,0px);opacity:1"), (3.6, "transform:translate(0px,0px);opacity:1")]
    # pre-launch rumble
    for k, t in enumerate([3.8, 4.0, 4.2, 4.5, 4.7, 4.9, 5.1, 5.3]):
        dx = (0.6 if k % 2 else -0.6) * (1.6 if t > 4.4 else 1)
        fly.append((t, f"transform:translate({dx}px,0px);opacity:1"))
    fly += [(t, f"transform:translate(0px,{-travel * frac(t):.2f}px);opacity:1") for t in samples]
    fly += [(t_reset, f"transform:translate(0px,{-travel}px);opacity:0"),
            (t_reset + 0.01, "transform:translate(0px,0px);opacity:0"),
            (t_reset + 0.6, "transform:translate(0px,0px);opacity:1")]
    css.append(keyframes("fly", T, fly))

    # launch pad + ground
    pad_w = 15
    body.append(mono(x0 - 1 * cw, ground_y, "=====" + " " * 5 + "=====", cw, "m", size=fs, weight="700"))
    body.append(mono(px + 6, ground_y + lh, "/" * 60, cw * 0.82, "d", size=11))
    body.append(f'<rect x="{px}" y="{ground_y + 2}" width="{pw}" height="{ph}" fill="#0b0f17" opacity=".55"/>')
    _ = pad_w

    # smoke clouds
    clouds = [("( ~  )", -9, -70, 6), ("(  ~~ )", 9, 70, -4), ("( ~ )", -6, -120, -18), ("(~  ~)", 6, 125, -14),
              ("(  ~ )", -4, -40, -30), ("( ~~ )", 4, 45, -34)]
    for i, (s, col, dx, dy) in enumerate(clouds):
        y = ground_y - 6
        body.append(f'<g style="animation:smoke{i} {T}s ease-out infinite">'
                    + mono(cx + col * cw - len(s) * cw / 2, y, s, cw, "m", size=fs) + "</g>")
        st = 4.6 + 0.12 * i
        css.append(keyframes(f"smoke{i}", T, [
            (0, "transform:translate(0px,0px);opacity:0"),
            (st - 0.01, "transform:translate(0px,0px);opacity:0"),
            (st, "transform:translate(0px,0px);opacity:.95"),
            (st + 1.4, f"transform:translate({dx * .55:.1f}px,{dy * .5:.1f}px);opacity:.8"),
            (11.5, f"transform:translate({dx:.1f}px,{dy - 10:.1f}px);opacity:0"),
            (T, f"transform:translate({dx:.1f}px,{dy - 10:.1f}px);opacity:0"),
        ]))

    # top fade: the rocket dissolves into deep space behind the HUD
    body.append(f'<rect x="{px}" y="{py}" width="{pw}" height="120" fill="url(#fadeTop)"/>')
    body.append("</g>")  # end clip

    # ── HUD inside scene: countdown + altitude gauge ──
    body.append(mono(px + 16, py + 22, "PAD-01 // FLIGHT COMPUTER", 6.6, "m", size=11))
    cd = [("T-03", "y", [(0, 1.5), (t_reset, T)]), ("T-02", "y", [(1.5, 3.0)]), ("T-01", "y", [(3.0, 4.5)]),
          ("IGNITION", "o", [(4.5, t_lift)]), ("LIFTOFF", "g", [(t_lift, t_apo)]), ("APOGEE", "b", [(t_apo, t_reset)])]
    for i, (s, c, wins) in enumerate(cd):
        body.append(f'<g style="animation:cd{i} {T}s linear infinite">'
                    + mono(px + 16, py + 50, s, 13.2, c, size=22, weight="800") + "</g>")
        css.append(windows_kf(f"cd{i}", T, wins))

    gx, gy0, gy1 = px + pw - 26, py + 64, ground_y - 6
    gh = gy1 - gy0
    body.append(f'<rect x="{gx}" y="{gy0}" width="6" height="{gh}" rx="3" fill="#161b22" stroke="{BORDER}"/>')
    for m in range(0, 501, 100):
        y = gy1 - gh * m / 500
        body.append(f'<line x1="{gx - 5}" x2="{gx}" y1="{y:.1f}" y2="{y:.1f}" stroke="{DIM}"/>')
        body.append(mono(gx - 8 - len(str(m)) * 6, y + 3.5, str(m), 6, "d", size=10))
    rec_y = gy1 - gh * 488.5 / 500
    body.append(f'<line x1="{gx - 4}" x2="{gx + 10}" y1="{rec_y:.1f}" y2="{rec_y:.1f}" stroke="{YELLOW}" stroke-dasharray="2 2"/>')
    body.append(f'<rect x="{gx + 1}" y="{gy0 + 1}" width="4" height="{gh - 2}" rx="2" fill="url(#gauge)" '
                f'style="transform-box:fill-box;transform-origin:50% 100%;animation:gfill {T}s linear infinite"/>')
    gf = [(0, "transform:scaleY(0)"), (t_lift, "transform:scaleY(0)")]
    gf += [(t, f"transform:scaleY({0.977 * frac(t):.4f})") for t in samples]
    gf += [(t_reset, "transform:scaleY(.977)"), (t_reset + 0.5, "transform:scaleY(0)")]
    css.append(keyframes("gfill", T, gf))

    # altitude readout (discrete frames)
    body.append(mono(gx - 96, py + 22, "ALT", 6.6, "m", size=11))
    alt_times = [0.0] + samples[1:] + [t_reset]
    for i in range(len(alt_times) - 1):
        a, b = alt_times[i], alt_times[i + 1]
        val = 0.0 if i == 0 else 488.5 * frac(samples[i])
        wins = [(a, b)] if i else [(0, t_lift + (samples[1] - t_lift)), (t_reset, T)]
        c = "y" if i == len(alt_times) - 2 else "t"
        body.append(f'<g style="animation:alt{i} {T}s linear infinite">'
                    + mono(gx - 72, py + 22, f"{val:05.1f} m", 7.2, c, size=12, weight="700") + "</g>")
        css.append(windows_kf(f"alt{i}", T, wins))

    # ── right side: pilot card ──
    rx = 436
    body.append(mono(rx, 52, "> PILOT // GIGOMIERI05", 7.2, "m", size=12))
    body.append(mono(rx, 94, "GIOVANNI DE LUCA", 22.0, "t", size=34, weight="800"))
    body.append(mono(rx, 134, "GOMIERI", 22.0, "b", size=34, weight="800"))
    body.append(f'<rect x="{rx + 7 * 22 + 8}" y="111" width="14" height="26" fill="{BLUE}" class="blink"/>')

    # typing roles
    roles = [
        ("Computer Engineering @ FACENS", "g"),
        ("Founder & Developer @ RDB Futura", "o"),
        ("Building software + physical tech", "b"),
        ("Competitive Programming · Robotics", "p"),
        ("National Rocketry Record · 488.5 m", "y"),
    ]
    RT, per = 17.5, 3.5
    rcw = 8.4
    for i, (s, c) in enumerate(roles):
        st = i * per
        n = len(s)
        type_end = st + n * 0.045
        clip_id = f"role{i}"
        full = (n + 2) * rcw
        # SMIL discrete width animation → typewriter
        vals = [0.0]
        times = [0.0]
        if st > 0:
            vals.append(0.0)
            times.append(st / RT)
        for k in range(1, n + 1):
            vals.append((k + 2) * rcw)
            times.append((st + k * 0.045) / RT)
        vals += [full, 0.0]
        times += [(st + per - 0.35) / RT, (st + per) / RT]
        if times[-1] < 1:
            vals.append(0.0)
            times.append(1.0)
        else:
            times[-1] = 1.0
        body.append(
            f'<clipPath id="{clip_id}"><rect x="{rx}" y="150" height="30" width="0">'
            f'<animate attributeName="width" dur="{RT}s" repeatCount="indefinite" calcMode="discrete" '
            f'values="{";".join(f"{v:.1f}" for v in vals)}" keyTimes="{";".join(f"{t:.4f}" for t in times)}"/>'
            f"</rect></clipPath>")
        body.append(f'<g clip-path="url(#{clip_id})">'
                    + mono(rx, 170, "> " + s, rcw, c, size=14, weight="600") + "</g>")
        _ = type_end

    # mission log
    ly0 = 214
    body.append(f'<rect x="{rx - 8}" y="{ly0 - 22}" width="{W - rx - 10}" height="{H - ly0 + 4}" rx="10" fill="#0b0f17" stroke="{BORDER}"/>')
    body.append(mono(rx + 6, ly0, "MISSION LOG", 7.2, "m", size=12))
    body.append(f'<circle cx="{rx + 104}" cy="{ly0 - 4}" r="3.5" fill="{RED}" class="blink"/>')
    body.append(mono(rx + 112, ly0, "REC", 7.2, "r", size=12))
    log = [
        (0.4, "T-03  GO / NO-GO POLL ....... GO", "g"),
        (3.0, "T-01  ARM RETRACT ........... OK", "t"),
        (4.5, "T+00  IGNITION .............. OK", "o"),
        (5.6, "T+01  LIFTOFF ............... OK", "g"),
        (7.4, "T+03  MAX-Q ................. OK", "t"),
        (t_apo, "T+04  APOGEE ........... 488.5 m", "b"),
        (t_apo + 1.0, "T+05  NATIONAL RECORD ........ ★", "y"),
    ]
    for i, (t, s, c) in enumerate(log):
        y = ly0 + 26 + i * 21
        body.append(f'<g style="animation:log{i} {T}s linear infinite">'
                    + mono(rx + 6, y, s, 7.8, c, size=13, weight="600") + "</g>")
        css.append(windows_kf(f"log{i}", T, [(t, t_reset)], fade=0.15))

    return svg_doc(W, H, "Giovanni de Luca Gomieri — ASCII rocket launch", "\n".join(css), "\n".join(body))


# ═════════════════════════════════════════════════════════════════════════
# 2. TERMINAL — boot sequence
# ═════════════════════════════════════════════════════════════════════════
def build_terminal() -> str:
    W, T = 840, 20.0
    cw, lh, fs = 8.4, 25, 14
    x0, y0 = 28, 78
    prompt = "giovanni@facens:~$ "
    lines: list[tuple[str, str, list[tuple[str, str]]]] = [
        ("cmd", "whoami", []),
        ("out", "", [("Giovanni de Luca Gomieri", "t"), ("  ·  Sorocaba, SP, Brazil", "m")]),
        ("cmd", "cat roles.txt", []),
        ("out", "", [("  ▸ ", "g"), ("founder & developer ...... ", "t"), ("RDB Futura", "o")]),
        ("out", "", [("  ▸ ", "g"), ("engineering student ...... ", "t"), ("FACENS · Computer Engineering", "b")]),
        ("out", "", [("  ▸ ", "g"), ("technology teacher ....... ", "t"), ("teaching what I build", "p")]),
        ("cmd", "./current_vector --verbose", []),
        ("out", "", [("  studying  ", "m"), ("→ ", "y"), ("competitive programming", "t")]),
        ("out", "", [("  exploring ", "m"), ("→ ", "y"), ("embedded · robotics & IoT · cloud · astronomy", "t")]),
        ("cmd", "", []),
    ]
    H = int(y0 + len(lines) * lh + 8)
    css: list[str] = []
    body = [card(W, H)]
    body.append(f'<path d="M0.5 14.5a14 14 0 0 1 14-14h811a14 14 0 0 1 14 14v26h-839z" fill="#161b22"/>')
    body.append(f'<line x1="0.5" x2="{W - .5}" y1="40.5" y2="40.5" stroke="{BORDER}"/>')
    for i, c in enumerate([RED, YELLOW, GREEN]):
        body.append(f'<circle cx="{24 + i * 20}" cy="20.5" r="6" fill="{c}"/>')
    body.append(mono(W / 2 - 15 * 7.2, 25, "giovanni@facens: ~/mission", 7.2, "m", size=12))

    t = 0.5
    end_hold = T - 0.6
    for i, (kind, cmd, segs) in enumerate(lines):
        y = y0 + i * lh
        if kind == "cmd":
            # prompt appears, then command types
            g = f'<g style="animation:tl{i} {T}s linear infinite">'
            g += mono(x0, y, "giovanni@facens", cw, "g", size=fs, weight="700")
            g += mono(x0 + 15 * cw, y, ":", cw, "t", size=fs)
            g += mono(x0 + 16 * cw, y, "~", cw, "b", size=fs, weight="700")
            g += mono(x0 + 17 * cw, y, "$", cw, "t", size=fs)
            g += "</g>"
            body.append(g)
            css.append(windows_kf(f"tl{i}", T, [(t, end_hold)]))
            cx = x0 + len(prompt) * cw
            if cmd:
                n = len(cmd)
                t_type = t + 0.35
                vals, times = [0.0, 0.0], [0.0, t_type / T]
                for k in range(1, n + 1):
                    vals.append(k * cw)
                    times.append((t_type + k * 0.055) / T)
                vals += [n * cw, 0.0, 0.0]
                times += [end_hold / T, (end_hold + 0.01) / T, 1.0]
                body.append(
                    f'<clipPath id="c{i}"><rect x="{cx}" y="{y - 18}" height="26" width="0">'
                    f'<animate attributeName="width" dur="{T}s" repeatCount="indefinite" calcMode="discrete" '
                    f'values="{";".join(f"{v:.1f}" for v in vals)}" keyTimes="{";".join(f"{q:.4f}" for q in times)}"/>'
                    f"</rect></clipPath>")
                body.append(f'<g clip-path="url(#c{i})">' + mono(cx, y, cmd, cw, "t", size=fs) + "</g>")
                t = t_type + n * 0.055 + 0.35
            else:
                body.append(f'<g style="animation:tl{i} {T}s linear infinite">'
                            f'<rect x="{cx + 2}" y="{y - 14}" width="9" height="18" fill="{TEXT}" class="blink"/></g>')
        else:
            g = f'<g style="animation:tl{i} {T}s linear infinite">'
            col = 0
            for s, c in segs:
                g += mono(x0 + col * cw, y, s, cw, c, size=fs)
                col += len(s)
            g += "</g>"
            body.append(g)
            css.append(windows_kf(f"tl{i}", T, [(t, end_hold)]))
            t += 0.18
    return svg_doc(W, H, "Terminal boot sequence — whoami", "\n".join(css), "\n".join(body))


# ═════════════════════════════════════════════════════════════════════════
# 3. FLIGHT PROFILE — record flight trajectory
# ═════════════════════════════════════════════════════════════════════════
def build_flight() -> str:
    W, H, T = 840, 360, 12.0
    css: list[str] = []
    body = [card(W, H)]
    L, R, TOP, BOT = 74, 812, 104, 262

    def ay(m: float) -> float:
        return BOT - (BOT - TOP) * m / 500

    body.append(mono(24, 32, "FLIGHT PROFILE // RECORD FLIGHT", 7.2, "m", size=12))
    body.append(mono(R - 22 * 7.2, 32, "MOBFOG · JORNADA BRAS.", 7.2, "d", size=12))
    for m in range(0, 501, 100):
        y = ay(m)
        body.append(f'<line x1="{L}" x2="{R}" y1="{y:.1f}" y2="{y:.1f}" stroke="#161b22"/>')
        s = f"{m} m"
        body.append(mono(L - 10 - len(s) * 6.6, y + 4, s, 6.6, "d", size=11))
    body.append(f'<line x1="{L}" x2="{R}" y1="{BOT}" y2="{BOT}" stroke="{BORDER}"/>')

    ax, ay_ = 300, ay(488.5)
    asc = f"M{L + 16} {BOT} C {L + 60} {BOT - 120}, {ax - 120} {ay_}, {ax} {ay_}"
    desc = f"M{ax} {ay_} C {ax + 140} {ay_}, {R - 150} {BOT - 140}, {R - 30} {BOT}"
    body.append(f'<path d="{asc}" fill="none" stroke="url(#asc)" stroke-width="3" stroke-linecap="round" '
                f'pathLength="1" stroke-dasharray="1 1" style="animation:draw1 {T}s linear infinite"/>')
    body.append('<defs><linearGradient id="asc" x1="0" y1="1" x2="1" y2="0">'
                f'<stop offset="0" stop-color="{ORANGE}"/><stop offset="1" stop-color="{YELLOW}"/></linearGradient>'
                f'<mask id="dm"><path d="{desc}" fill="none" stroke="#fff" stroke-width="8" pathLength="1" '
                f'stroke-dasharray="1 1" style="animation:draw2 {T}s linear infinite"/></mask></defs>')
    body.append(f'<path d="{desc}" fill="none" stroke="{BLUE}" stroke-width="2" stroke-dasharray="3 7" '
                f'stroke-linecap="round" mask="url(#dm)"/>')
    css.append(keyframes("draw1", T, [(0, "stroke-dashoffset:1;opacity:1"), (0.4, "stroke-dashoffset:1;opacity:1"),
                                      (2.4, "stroke-dashoffset:0;opacity:1"), (11.3, "stroke-dashoffset:0;opacity:1"),
                                      (11.9, "stroke-dashoffset:0;opacity:0")]))
    css.append(keyframes("draw2", T, [(0, "stroke-dashoffset:1;opacity:1"), (3.0, "stroke-dashoffset:1;opacity:1"),
                                      (9.0, "stroke-dashoffset:0;opacity:1"), (11.3, "stroke-dashoffset:0;opacity:1"),
                                      (11.9, "stroke-dashoffset:0;opacity:0")]))

    # rocket marker on ascent
    k1, k2 = 0.4 / T, 2.4 / T
    body.append(f'<g style="animation:mk1 {T}s linear infinite"><path d="M7 0 L-5 -4.5 L-2 0 L-5 4.5 Z" fill="{YELLOW}">'
                f'<animateMotion dur="{T}s" repeatCount="indefinite" rotate="auto" path="{asc}" '
                f'keyPoints="0;0;1;1" keyTimes="0;{k1:.4f};{k2:.4f};1" calcMode="linear"/></path></g>')
    css.append(windows_kf("mk1", T, [(0.4, 2.45)]))
    # parachute marker on descent
    k3, k4 = 3.0 / T, 9.0 / T
    chute = (f'<g><path d="M-9 -6 A9 7 0 0 1 9 -6 Z" fill="{BLUE}" opacity=".9"/>'
             f'<path d="M-9 -6 L0 6 M9 -6 L0 6 M0 -6 L0 6" stroke="{BLUE}" stroke-width=".8"/>'
             f'<rect x="-1.5" y="5" width="3" height="7" fill="{TEXT}"/>'
             f'<animateMotion dur="{T}s" repeatCount="indefinite" path="{desc}" '
             f'keyPoints="0;0;1;1" keyTimes="0;{k3:.4f};{k4:.4f};1" calcMode="linear"/></g>')
    body.append(f'<g style="animation:mk2 {T}s linear infinite">{chute}</g>')
    css.append(windows_kf("mk2", T, [(2.9, 11.3)], fade=0.3))

    # apogee callout
    body.append(f'<g style="animation:apo {T}s linear infinite">'
                f'<circle cx="{ax}" cy="{ay_:.1f}" r="5" fill="{YELLOW}"/>'
                f'<circle cx="{ax}" cy="{ay_:.1f}" r="5" fill="none" stroke="{YELLOW}" '
                f'style="transform-box:fill-box;transform-origin:center;animation:ping 1.6s ease-out infinite"/>'
                f'<line x1="{ax}" x2="{ax}" y1="{ay_ + 8:.1f}" y2="{BOT}" stroke="{YELLOW}" stroke-dasharray="2 4" opacity=".5"/>'
                + mono(ax + 18, ay_ - 34, "488.5 m", 15.6, "y", size=26, weight="800")
                + mono(ax + 18, ay_ - 13, "APOGEE · NATIONAL ROCKETRY RECORD", 7.2, "t", size=12, weight="600")
                + "</g>")
    css.append("@keyframes ping{0%{transform:scale(1);opacity:.9}100%{transform:scale(4.2);opacity:0}}")
    css.append(windows_kf("apo", T, [(2.4, 11.4)], fade=0.4))

    # labels on the chart
    body.append(f'<g style="animation:lb {T}s linear infinite">'
                + mono(R - 196, BOT - 14, "recovery · parachute", 7.2, "b", size=12) + "</g>")
    css.append(windows_kf("lb", T, [(6.5, 11.4)], fade=0.4))
    body.append(mono(L + 4, BOT + 18, "launch  ·  illustrative trajectory", 7.2, "d", size=11))

    # achievement chips
    chips = [("26", "awards & counting", YELLOW), ("2×", "AMERIFOG champion", GREEN),
             ("1st", "Copa Paulista", BLUE), ("46ª", "Jornada Brasileira", ORANGE)]
    cx = 24
    gap = 12
    widths = [len(a) * 9.6 + len(b) * 7.2 + 34 for a, b, _ in chips]
    total = sum(widths) + gap * (len(chips) - 1)
    cx = (W - total) / 2
    for i, ((a, b, col), w) in enumerate(zip(chips, widths)):
        body.append(f'<g style="animation:chip{i} {T}s linear infinite">'
                    f'<rect x="{cx:.1f}" y="296" width="{w:.1f}" height="38" rx="19" fill="#161b22" stroke="{BORDER}"/>'
                    + mono(cx + 14, 321, a, 9.6, "", fill=col, size=16, weight="800")
                    + mono(cx + 20 + len(a) * 9.6, 320, b, 7.2, "t", size=12) + "</g>")
        css.append(keyframes(f"chip{i}", T, [
            (0, "opacity:0;transform:translateY(6px)"), (3 + i * 0.35, "opacity:0;transform:translateY(6px)"),
            (3.6 + i * 0.35, "opacity:1;transform:translateY(0px)"), (11.3, "opacity:1;transform:translateY(0px)"),
            (11.9, "opacity:0;transform:translateY(0px)")]))
        cx += w + gap
    return svg_doc(W, H, "Flight profile of the 488.5 m national rocketry record", "\n".join(css), "\n".join(body))


# ═════════════════════════════════════════════════════════════════════════
# 4. ORBIT — RDB Futura as a planetary system
# ═════════════════════════════════════════════════════════════════════════
def build_orbit() -> str:
    W, H = 840, 340
    cx, cy = 420, 168
    rng = random.Random(7)
    body = [card(W, H)]
    stars, _ = starfield(rng, 60, 12, 12, W - 12, H - 12, "o")
    body.append(stars)
    body.append('<defs><radialGradient id="planet" cx=".35" cy=".3" r=".8">'
                f'<stop offset="0" stop-color="#2f81f7"/><stop offset=".55" stop-color="#1f3b6e"/>'
                f'<stop offset="1" stop-color="#0d1117"/></radialGradient>'
                f'<radialGradient id="glow"><stop offset="0" stop-color="{BLUE}" stop-opacity=".35"/>'
                f'<stop offset="1" stop-color="{BLUE}" stop-opacity="0"/></radialGradient></defs>')
    orbits = [(215, 64, 26, ["hands-on STEAM missions", "gamified platform", "physical kits"], GREEN),
              (330, 116, 40, ["BNCC-aligned evidence", "astronomy as a gateway"], ORANGE)]
    for rx, ry, _, _, _ in orbits:
        body.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="none" stroke="{BORDER}" stroke-dasharray="2 5"/>')
    body.append(f'<circle cx="{cx}" cy="{cy}" r="110" fill="url(#glow)"/>')
    body.append(f'<circle cx="{cx}" cy="{cy}" r="46" fill="url(#planet)" stroke="#388bfd" stroke-opacity=".5"/>')
    body.append(mono(cx - 5 * 9, cy + 5, "RDB FUTURA", 9, "t", size=15, weight="800"))
    for rx, ry, dur, labels, col in orbits:
        path = f"M{cx - rx} {cy} a{rx} {ry} 0 1 0 {2 * rx} 0 a{rx} {ry} 0 1 0 {-2 * rx} 0"
        n = len(labels)
        for i, lab in enumerate(labels):
            w = len(lab) * 7.2 + 18
            begin = -dur * i / n
            body.append(
                f'<g><circle r="6" fill="{col}"/><circle r="11" fill="{col}" opacity=".18"/>'
                f'<rect x="{-w / 2:.1f}" y="-36" width="{w:.1f}" height="22" rx="11" fill="#161b22" stroke="{BORDER}"/>'
                + mono(-w / 2 + 9, -21, lab, 7.2, "t", size=12)
                + f'<animateMotion dur="{dur}s" begin="{begin:.2f}s" repeatCount="indefinite" path="{path}"/></g>')
    body.append(mono(24, H - 20, "mission: transform theory into practical learning experiences", 7.2, "m", size=12))
    body.append(mono(W - 24 - 18 * 7.2, H - 20, "rdbfutura.com.br ↗", 7.2, "b", size=12))
    return svg_doc(W, H, "RDB Futura — the system in orbit", "", "\n".join(body))


# ═════════════════════════════════════════════════════════════════════════
# 5. DIVIDER + FOOTER
# ═════════════════════════════════════════════════════════════════════════
def build_divider() -> str:
    W, H = 840, 24
    body = ['<defs><linearGradient id="ln" x1="0" x2="1">'
            f'<stop offset="0" stop-color="{BORDER}" stop-opacity="0"/><stop offset=".5" stop-color="{BORDER}"/>'
            f'<stop offset="1" stop-color="{BORDER}" stop-opacity="0"/></linearGradient>'
            '<linearGradient id="tail" x1="0" x2="1">'
            f'<stop offset="0" stop-color="{BLUE}" stop-opacity="0"/><stop offset="1" stop-color="{BLUE}"/></linearGradient></defs>',
            f'<rect x="0" y="11.5" width="{W}" height="1" fill="url(#ln)"/>',
            '<g style="animation:comet 7s cubic-bezier(.45,0,.55,1) infinite">'
            f'<rect x="-120" y="11" width="120" height="2" rx="1" fill="url(#tail)"/>'
            f'<circle cx="0" cy="12" r="3" fill="#a5d6ff"/><circle cx="0" cy="12" r="7" fill="{BLUE}" opacity=".25"/></g>']
    css = "@keyframes comet{0%{transform:translateX(-20px)}70%{transform:translateX(980px)}100%{transform:translateX(980px)}}"
    return svg_doc(W, H, "divider", css, "\n".join(body))


def build_footer() -> str:
    W, H = 840, 190
    rng = random.Random(42)
    body = [card(W, H)]
    stars, _ = starfield(rng, 70, 12, 12, W - 12, H - 12, "f")
    body.append(stars)
    # shooting star
    body.append('<g style="animation:shoot 9s ease-in 2s infinite;opacity:0">'
                f'<line x1="0" y1="0" x2="-70" y2="-24" stroke="#a5d6ff" stroke-width="1.5" stroke-linecap="round"/>'
                f'<circle r="1.8" fill="#fff"/></g>')
    css = ["@keyframes shoot{0%{transform:translate(560px,30px);opacity:0}2%{opacity:1}"
           "12%{transform:translate(760px,98px);opacity:0}100%{transform:translate(760px,98px);opacity:0}}"]
    # orbiting satellite across the card
    sat = "-=[ o ]=-"
    body.append('<g style="animation:sat 26s linear infinite">'
                + mono(0, 0, sat, 7.8, "b", size=13, weight="700")
                + f'<circle cx="{4.5 * 7.8:.1f}" cy="-4" r="9" fill="none" stroke="{BLUE}" stroke-opacity=".25"/>'
                + "</g>")
    css.append("@keyframes sat{0%{transform:translate(-90px,58px)}100%{transform:translate(900px,38px)}}")
    q = "“A ciência prática produz resultados concretos e visíveis.”"
    body.append(mono(W / 2 - len(q) * 8.4 / 2, 112, q, 8.4, "t", size=14, weight="600"))
    s2 = "— built, tested and launched from Sorocaba, Brazil"
    body.append(mono(W / 2 - len(s2) * 7.2 / 2, 140, s2, 7.2, "m", size=12))
    return svg_doc(W, H, "A ciência prática produz resultados concretos e visíveis.", "\n".join(css), "\n".join(body))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    files = {
        "hero.svg": build_hero(),
        "terminal.svg": build_terminal(),
        "flight-profile.svg": build_flight(),
        "orbit.svg": build_orbit(),
        "divider.svg": build_divider(),
        "footer.svg": build_footer(),
    }
    for name, svg in files.items():
        (OUT / name).write_text(svg, encoding="utf-8")
        print(f"wrote profile/anim/{name}  ({len(svg) / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
