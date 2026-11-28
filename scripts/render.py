#!/usr/bin/env python3
"""Render the profile README images (hero and project cards) in light and dark.

The images reproduce the look of the portfolio: Inter, neutral greys, rounded
tiles and a blue accent. Each one is an HTML page captured with headless Chrome
at 2x, with a transparent background so it sits on GitHub's own light or dark
theme.

Usage: python3 scripts/render.py   (needs google-chrome and the Inter font)
"""

import html
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets"

THEMES = {
    "light": dict(fg="#1d1d1f", muted="#636366", surface="#f5f5f7", accent="#0066cc"),
    "dark": dict(fg="#f5f5f7", muted="#a1a1a6", surface="#161617", accent="#60a5fa"),
}

HERO = dict(
    name="Eduardo Ruiz",
    role="Software engineer.",
    tagline="Building software across the stack, from web applications to desktop tools and low-level systems.",
    status="Relocating to Dublin in February 2027",
)

FEATURED = dict(
    slug="ms43",
    status="In progress",
    name="MS43 Virtual Lab",
    text="Running the real firmware of a BMW engine computer (Siemens MS43, Infineon C167) in an emulator written in Rust, with every result checked against the official manual and two independent disassemblers.",
    tech="Rust, WebAssembly, Python, Ghidra",
    link="Public log",
)

CARDS = [
    dict(slug="brb", status="Live", name="BRB", text="Free mini-games to play solo or with friends, with rankings, daily challenges and live multiplayer.", tech="Next.js, Supabase, TypeScript", link="Play"),
    dict(slug="cauce", status="Open source", name="Cauce", text="A minimal Git client for Linux. Stage single hunks, read a clean branch graph and switch repos with Ctrl+P.", tech="Electron, React, TypeScript", link="GitHub"),
    dict(slug="nimbomail", status="Open source", name="NimboMail", text="A private email client for Linux that blocks tracking pixels, translates offline and unsubscribes in one click.", tech="Electron, React, TypeScript", link="GitHub"),
    dict(slug="tuxlens", status="Open source", name="TuxLens", text="Your phone as a Linux webcam with about 80 ms of latency, background blur and auto-framing.", tech="Python, WebCodecs, PipeWire", link="GitHub"),
    dict(slug="beacon-split", status="Open source", name="Beacon Split", text="A desktop workspace for Claude Code sessions, with a Rust daemon that keeps terminals alive.", tech="Rust, Tauri, React", link="Website"),
    dict(slug="gameboy4me", status="Personal project", name="Gameboy4me", text="A Game Boy and Game Boy Color emulator in Rust, compiled to WebAssembly to play in the browser.", tech="Rust, WebAssembly, Next.js", link="Play"),
]

BASE_CSS = """
@font-face { font-family: 'Inter Variable'; src: local('Inter Variable'), local('Inter'); font-weight: 100 900; }
* { box-sizing: border-box; margin: 0; }
html, body { background: transparent; }
body {
  width: %(w)dpx; height: %(h)dpx; padding: 8px; overflow: hidden;
  font-family: 'Inter Variable', Inter, -apple-system, 'Segoe UI', sans-serif;
  font-optical-sizing: auto; color: %(fg)s; letter-spacing: -0.011em;
  -webkit-font-smoothing: antialiased;
}
.muted { color: %(muted)s; }
"""

HERO_CSS = """
.hero { height: 100%%; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; }
h1 { font-size: 76px; font-weight: 700; letter-spacing: -0.035em; line-height: 1.02; }
.tagline { text-wrap: balance; max-width: 660px; margin-top: 18px; font-size: 27px; font-weight: 600; line-height: 1.22; letter-spacing: -0.022em; }
.status { display: inline-flex; align-items: center; gap: 9px; margin-top: 30px; padding: 8px 17px; border-radius: 999px; background: %(surface)s; font-size: 15px; font-weight: 500; }
.dot { width: 8px; height: 8px; border-radius: 50%%; background: %(accent)s; }
"""

CARD_CSS = """
.card {
  height: 100%%; padding: 28px 30px; border-radius: 24px; background: %(surface)s;
  display: flex; flex-direction: column;
}
.featured {
  background: radial-gradient(120%% 160%% at 100%% 0%%, color-mix(in srgb, %(accent)s 18%%, transparent) 0%%, transparent 55%%), %(surface)s;
}
.status { font-size: 13px; font-weight: 500; }
h2 { margin-top: 6px; font-size: 26px; font-weight: 650; letter-spacing: -0.022em; line-height: 1.15; }
.featured h2 { font-size: 36px; letter-spacing: -0.03em; }
.text { text-wrap: pretty; margin-top: 10px; font-size: 15px; line-height: 1.5; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden; }
.featured .text { max-width: 640px; font-size: 16.5px; }
.foot { margin-top: auto; display: flex; justify-content: space-between; align-items: baseline; gap: 16px; font-size: 13.5px; }
.link { color: %(accent)s; font-weight: 500; white-space: nowrap; }
.link::after { content: ' \\203A'; font-size: 1.15em; }
"""


def page(css: str, body: str) -> str:
    return f"<!doctype html><html><head><meta charset='utf-8'><style>{css}</style></head><body>{body}</body></html>"


def hero_html(theme: dict) -> str:
    w, h = 880, 380
    css = BASE_CSS % dict(w=w, h=h, **theme) + HERO_CSS % theme
    e = {k: html.escape(v) for k, v in HERO.items()}
    body = (
        f"<div class='hero'><h1>{e['name']}</h1>"
        f"<p class='tagline'>{e['role']} <span class='muted'>{e['tagline']}</span></p>"
        f"<p class='status'><span class='dot'></span>{e['status']}</p></div>"
    )
    return page(css, body), w, h


def card_html(card: dict, theme: dict, featured: bool = False) -> str:
    w, h = (880, 276) if featured else (440, 236)
    css = BASE_CSS % dict(w=w, h=h, **theme) + CARD_CSS % theme
    e = {k: html.escape(v) for k, v in card.items()}
    body = (
        f"<div class='card{' featured' if featured else ''}'>"
        f"<p class='status muted'>{e['status']}</p><h2>{e['name']}</h2>"
        f"<p class='text'>{e['text']}</p>"
        f"<p class='foot'><span class='muted'>{e['tech']}</span><span class='link'>{e['link']}</span></p></div>"
    )
    return page(css, body), w, h


def shoot(chrome: str, doc: str, w: int, h: int, out: Path, tmp: Path) -> None:
    src = tmp / f"{out.stem}.html"
    src.write_text(doc, encoding="utf-8")
    subprocess.run(
        [
            chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars",
            "--force-device-scale-factor=2", "--default-background-color=00000000",
            f"--window-size={w},{h}", f"--screenshot={out}", src.as_uri(),
        ],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    print(f"  {out.relative_to(ROOT)}")


def main() -> int:
    chrome = shutil.which("google-chrome-stable") or shutil.which("google-chrome") or shutil.which("chromium")
    if not chrome:
        print("Chrome or Chromium is required", file=sys.stderr)
        return 1
    OUT.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        for name, theme in THEMES.items():
            shoot(chrome, *hero_html(theme), OUT / f"hero-{name}.png", tmp)
            shoot(chrome, *card_html(FEATURED, theme, featured=True), OUT / f"{FEATURED['slug']}-{name}.png", tmp)
            for card in CARDS:
                shoot(chrome, *card_html(card, theme), OUT / f"{card['slug']}-{name}.png", tmp)
    return 0


if __name__ == "__main__":
    sys.exit(main())
