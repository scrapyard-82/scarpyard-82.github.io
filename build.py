#!/usr/bin/env python3
"""
BBS Notes — static site generator (v2).

Deploys FLAT at repo root (no /docs subfolder needed). Layout:

  content/     <- your Markdown source files (NOT served directly)
  images/      <- your images, served as-is at /images/... (single copy, canonical)
  notes/       <- GENERATED html pages (safe to delete, rebuilt every time)
  index.html   <- GENERATED
  style.css    <- GENERATED

Run:
    python3 build.py

Then commit everything and push to the repo's default branch, with GitHub
Pages source set to "root" (see README).
"""

import json
import shutil
from pathlib import Path
from datetime import datetime

import markdown

ROOT = Path(__file__).parent.resolve()
CONTENT_DIR = ROOT / "content"
IMAGES_DIR = ROOT / "images"        # canonical, single copy, lives at repo root
NOTES_OUT = ROOT / "notes"          # generated, wiped & rebuilt each time
CONFIG_PATH = ROOT / "config.json"

MD_EXTENSIONS = ["fenced_code", "tables", "toc", "sane_lists", "footnotes", "codehilite"]
MD_EXT_CONFIG = {"codehilite": {"guess_lang": False}}

FILE_TITLES = {}


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def slugify_path(rel_path: Path) -> str:
    return "/".join(rel_path.with_suffix("").parts)


def scan_notes():
    tree = {"_files": [], "_dirs": {}}
    for md_path in sorted(CONTENT_DIR.rglob("*.md")):
        rel = md_path.relative_to(CONTENT_DIR)
        node = tree
        for part in rel.parts[:-1]:
            node = node["_dirs"].setdefault(part, {"_files": [], "_dirs": {}})
        node["_files"].append(rel)
    return tree


def title_from_md(md_path: Path) -> str:
    for line in md_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
    return md_path.stem.replace("-", " ").replace("_", " ").title()


def build_css(colors: dict, effects: dict) -> str:
    grain_block = ""
    if effects.get("grain", True):
        grain_block = """
.grain-overlay {
  pointer-events: none;
  position: fixed;
  inset: 0;
  z-index: 9998;
  opacity: 0.035;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='100' height='100'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='2'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
  background-repeat: repeat;
}
"""
    scanline_block = ""
    if effects.get("scanlines", True):
        scanline_block = """
.crt-overlay {
  pointer-events: none;
  position: fixed;
  inset: 0;
  z-index: 9999;
  background: repeating-linear-gradient(
    to bottom,
    rgba(255,255,255,0.025) 0px,
    rgba(255,255,255,0.025) 1px,
    transparent 1px,
    transparent 3px
  );
}
"""

    return f"""
:root {{
  --bg: {colors['background']};
  --bg-alt: {colors['background_alt']};
  --text: {colors['text']};
  --heading: {colors['heading']};
  --bold: {colors['bold']};
  --italic: {colors['italic']};
  --code: {colors['code']};
  --link: {colors['link']};
  --link-visited: {colors['link_visited']};
  --border: {colors['border']};
  --muted: {colors['muted']};
}}

* {{ box-sizing: border-box; }}

html, body {{
  margin: 0;
  padding: 0;
  background: var(--bg);
  color: var(--text);
  font-family: "Courier New", Consolas, Menlo, monospace;
  line-height: 1.6;
  font-size: 16px;
}}

{grain_block}
{scanline_block}

/* ---- Boot screen (first visit only, see boot.js) ---- */
#boot-screen {{
  position: fixed;
  inset: 0;
  background: #000;
  color: var(--heading);
  z-index: 10000;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  font-family: monospace;
  white-space: pre;
  text-align: center;
}}
#boot-screen.hidden {{ display: none; }}
#boot-screen .boot-line {{
  opacity: 0;
  animation: boot-line-in 0.2s steps(1) forwards;
}}
@keyframes boot-line-in {{ to {{ opacity: 1; }} }}
#boot-screen.fade-out {{
  animation: boot-fade 0.4s ease-out forwards;
}}
@keyframes boot-fade {{ to {{ opacity: 0; visibility: hidden; }} }}

/* ---- Layout ---- */
.wrap {{
  display: flex;
  min-height: 100vh;
  max-width: 1200px;
  margin: 0 auto;
}}

nav.sidebar {{
  width: 260px;
  flex-shrink: 0;
  border-right: 1px solid var(--border);
  padding: 20px 16px;
  background: var(--bg-alt);
}}

nav.sidebar .site-title {{
  color: var(--heading);
  font-weight: bold;
  font-size: 1.1em;
  text-shadow: 0 0 6px var(--heading);
  margin-bottom: 2px;
}}

nav.sidebar .site-subtitle {{
  color: var(--muted);
  font-size: 0.75em;
  margin-bottom: 20px;
  border-bottom: 1px dashed var(--border);
  padding-bottom: 14px;
}}

nav.sidebar a {{ color: var(--link); text-decoration: none; }}
nav.sidebar a:hover {{ text-decoration: underline; text-shadow: 0 0 5px var(--link); }}

.tree-dir {{
  margin: 10px 0 4px 0;
  color: var(--bold);
  font-size: 0.8em;
  text-transform: uppercase;
  letter-spacing: 1px;
}}
.tree-dir::before {{ content: "▸ "; }}

.tree-files {{ list-style: none; padding-left: 12px; margin: 0 0 8px 0; }}
.tree-files li {{ margin: 3px 0; font-size: 0.9em; }}
.tree-files li::before {{ content: "· "; color: var(--muted); }}
.tree-files li.active a {{ color: var(--bold); text-shadow: 0 0 6px var(--bold); }}

main {{ flex: 1; padding: 30px 40px; min-width: 0; }}

.crumbs {{ color: var(--muted); font-size: 0.8em; margin-bottom: 20px; }}
.crumbs a {{ color: var(--muted); }}

article h1, article h2, article h3, article h4 {{
  color: var(--heading);
  text-shadow: 0 0 5px rgba(0,255,65,0.2);
  border-bottom: 1px solid var(--border);
  padding-bottom: 6px;
}}
article strong {{ color: var(--bold); }}
article em {{ color: var(--italic); }}
article code {{
  color: var(--code);
  background: var(--bg-alt);
  padding: 2px 5px;
  border-radius: 2px;
  border: 1px solid var(--border);
  font-size: 0.9em;
}}
article pre {{
  background: var(--bg-alt);
  border: 1px solid var(--border);
  padding: 14px;
  overflow-x: auto;
  border-radius: 3px;
}}
article pre code {{ border: none; background: none; padding: 0; }}
article a {{ color: var(--link); }}
article a:visited {{ color: var(--link-visited); }}
article blockquote {{
  border-left: 3px solid var(--heading);
  margin: 16px 0;
  padding: 4px 16px;
  color: var(--muted);
  background: var(--bg-alt);
}}
article img {{
  max-width: 100%;
  height: auto;
  border: 1px solid var(--border);
  display: block;
  margin: 16px 0;
}}
article table {{ border-collapse: collapse; width: 100%; margin: 16px 0; }}
article th, article td {{ border: 1px solid var(--border); padding: 6px 10px; text-align: left; }}
article th {{ color: var(--heading); }}

hr {{ border: none; border-top: 1px dashed var(--border); margin: 24px 0; }}

.ascii-banner {{
  color: var(--heading);
  font-size: 10px;
  line-height: 1.1;
  white-space: pre;
  text-shadow: 0 0 4px var(--heading);
  margin-bottom: 16px;
  overflow-x: auto;
}}

.index-list {{ list-style: none; padding: 0; }}
.index-list h2 {{ color: var(--heading); margin-top: 28px; }}
.index-list li {{ margin: 6px 0; }}

footer {{
  margin-top: 60px;
  padding-top: 14px;
  border-top: 1px dashed var(--border);
  color: var(--muted);
  font-size: 0.75em;
}}

.menu-toggle {{ display: none; }}

@media (max-width: 800px) {{
  .wrap {{ flex-direction: column; }}
  nav.sidebar {{ width: 100%; border-right: none; border-bottom: 1px solid var(--border); }}
  main {{ padding: 20px; }}
  .ascii-banner {{ font-size: 7px; }}
  nav.sidebar .tree {{ display: none; }}
  nav.sidebar.open .tree {{ display: block; }}
  .menu-toggle {{
    display: inline-block;
    margin-top: 10px;
    background: var(--bg);
    border: 1px solid var(--border);
    color: var(--heading);
    padding: 6px 10px;
    cursor: pointer;
    font-family: inherit;
  }}
}}
"""


ASCII_BANNER = r"""
 _____                   _             _
|_   _|__ _ __ _ __ ___ (_)_ __   __ _| |
  | |/ _ \ '__| '_ ` _ \| | '_ \ / _` | |
  | |  __/ |  | | | | | | | | | | (_| | |
  |_|\___|_|  |_| |_| |_|_|_| |_|\__,_|_|
        :: N O T E S   T E R M I N A L ::
"""

BOOT_LINES = [
    "BIOS v2.6 ... OK",
    "LOADING KERNEL ... OK",
    "MOUNTING /notes ... OK",
    "MOUNTING /images ... OK",
    "INITIALIZING DISPLAY ... OK",
    "",
    "WELCOME, USER.",
]

BOOT_JS = """
(function() {
  var el = document.getElementById('boot-screen');
  if (!el) return;
  if (localStorage.getItem('bbs_booted')) {
    el.classList.add('hidden');
    return;
  }
  localStorage.setItem('bbs_booted', '1');
  setTimeout(function() {
    el.classList.add('fade-out');
    setTimeout(function() { el.classList.add('hidden'); }, 450);
  }, 1600);
})();
"""


def render_boot_screen():
    lines_html = ""
    for i, line in enumerate(BOOT_LINES):
        delay = i * 0.12
        lines_html += f'<div class="boot-line" style="animation-delay:{delay:.2f}s">{line or "&nbsp;"}</div>\n'
    return f'<div id="boot-screen">{lines_html}</div>'


def render_sidebar(tree, current_slug):
    html = ""
    if tree["_files"]:
        html += '<ul class="tree-files">\n'
        for rel in sorted(tree["_files"], key=lambda p: p.stem.lower()):
            slug = slugify_path(rel)
            title = FILE_TITLES.get(slug, rel.stem)
            active = "active" if slug == current_slug else ""
            html += f'<li class="{active}"><a href="/notes/{slug}.html">{title}</a></li>\n'
        html += "</ul>\n"
    for dirname, subtree in sorted(tree["_dirs"].items()):
        html += f'<div class="tree-dir">{dirname}</div>\n'
        html += render_sidebar(subtree, current_slug)
    return html


PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{page_title} :: {site_title}</title>
<link rel="stylesheet" href="/style.css">
</head>
<body>
{boot_screen}
<div class="crt-overlay"></div>
<div class="grain-overlay"></div>
<div class="wrap">
  <nav class="sidebar" id="sidebar">
    <div class="site-title">{site_title}</div>
    <div class="site-subtitle">{site_subtitle}</div>
    <button class="menu-toggle" id="menu-toggle">[ menu ]</button>
    <div class="tree">
      <ul class="tree-files"><li class="{home_active}"><a href="/index.html">index</a></li></ul>
      {sidebar}
    </div>
  </nav>
  <main>
    <div class="crumbs">{crumbs}</div>
    {content}
    <footer>generated {timestamp} :: terminal notes v2.0</footer>
  </main>
</div>
<script>
{boot_js}
var t = document.getElementById('menu-toggle');
if (t) t.addEventListener('click', function() {{
  document.getElementById('sidebar').classList.toggle('open');
}});
</script>
</body>
</html>
"""


def build():
    if NOTES_OUT.exists():
        shutil.rmtree(NOTES_OUT)
    NOTES_OUT.mkdir(parents=True)

    if not IMAGES_DIR.exists():
        IMAGES_DIR.mkdir(parents=True)

    config = load_config()
    colors = config["colors"]
    effects = config.get("effects", {})

    (ROOT / "style.css").write_text(build_css(colors, effects), encoding="utf-8")

    tree = scan_notes()
    all_files = list(CONTENT_DIR.rglob("*.md"))
    for md_path in all_files:
        rel = md_path.relative_to(CONTENT_DIR)
        FILE_TITLES[slugify_path(rel)] = title_from_md(md_path)

    boot_screen_html = render_boot_screen() if effects.get("boot_animation", True) else ""
    boot_js = BOOT_JS if effects.get("boot_animation", True) else ""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    md = markdown.Markdown(extensions=MD_EXTENSIONS, extension_configs=MD_EXT_CONFIG)

    for md_path in all_files:
        rel = md_path.relative_to(CONTENT_DIR)
        slug = slugify_path(rel)
        md.reset()
        html_body = md.convert(md_path.read_text(encoding="utf-8"))
        title = FILE_TITLES[slug]
        crumbs = " / ".join(['<a href="/index.html">home</a>'] + list(rel.parts[:-1]) + [title])
        sidebar_html = render_sidebar(tree, slug)

        page = PAGE_TEMPLATE.format(
            page_title=title,
            site_title=config["site_title"],
            site_subtitle=config["site_subtitle"],
            boot_screen=boot_screen_html,
            boot_js=boot_js,
            sidebar=sidebar_html,
            crumbs=crumbs,
            content=f"<article>{html_body}</article>",
            timestamp=timestamp,
            home_active="",
        )
        out_path = NOTES_OUT / rel.with_suffix(".html")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(page, encoding="utf-8")

    build_index(tree, config, boot_screen_html, boot_js, timestamp)
    print(f"Build complete. {len(all_files)} notes rendered.")


def build_index(tree, config, boot_screen_html, boot_js, timestamp):
    def render_section(subtree, heading_path):
        html = ""
        if heading_path:
            html += f"<h2>{heading_path}</h2>\n"
        if subtree["_files"]:
            html += '<ul class="index-list">\n'
            for rel in sorted(subtree["_files"], key=lambda p: p.stem.lower()):
                slug = slugify_path(rel)
                title = FILE_TITLES.get(slug, rel.stem)
                html += f'<li><a href="/notes/{slug}.html">{title}</a></li>\n'
            html += "</ul>\n"
        for dirname, sub in sorted(subtree["_dirs"].items()):
            new_path = f"{heading_path}/{dirname}" if heading_path else dirname
            html += render_section(sub, new_path)
        return html

    banner_html = f'<pre class="ascii-banner">{ASCII_BANNER}</pre>' if config.get("ascii_banner") else ""
    body = banner_html + "<h1>Index</h1>\n" + render_section(tree, "")
    sidebar_html = render_sidebar(tree, current_slug=None)

    page = PAGE_TEMPLATE.format(
        page_title="index",
        site_title=config["site_title"],
        site_subtitle=config["site_subtitle"],
        boot_screen=boot_screen_html,
        boot_js=boot_js,
        sidebar=sidebar_html,
        crumbs="home",
        content=f"<article>{body}</article>",
        timestamp=timestamp,
        home_active="active",
    )
    (ROOT / "index.html").write_text(page, encoding="utf-8")


if __name__ == "__main__":
    build()
