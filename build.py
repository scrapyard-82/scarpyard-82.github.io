#!/usr/bin/env python3
"""
BBS Notes — static site generator.

Reads Markdown files from notes/ (with arbitrary subfolders), renders them
to styled HTML pages into docs/, and copies images/ into docs/images/.

Usage:
    python3 build.py

Then commit docs/ and point GitHub Pages at the docs/ folder (or root,
see README).
"""

import json
import shutil
from pathlib import Path
from datetime import datetime

import markdown

ROOT = Path(__file__).parent.resolve()
NOTES_DIR = ROOT / "notes"
IMAGES_DIR = ROOT / "images"
OUT_DIR = ROOT / "docs"
CONFIG_PATH = ROOT / "config.json"

MD_EXTENSIONS = ["fenced_code", "tables", "toc", "sane_lists", "footnotes", "codehilite"]
MD_EXT_CONFIG = {"codehilite": {"guess_lang": False}}


def load_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def slugify_path(rel_path: Path) -> str:
    """notes/articles/example-article.md -> articles/example-article"""
    parts = list(rel_path.with_suffix("").parts)
    return "/".join(parts)


def scan_notes():
    """Return a nested tree: {'_files': [...], '_dirs': {name: subtree}}"""
    tree = {"_files": [], "_dirs": {}}
    for md_path in sorted(NOTES_DIR.rglob("*.md")):
        rel = md_path.relative_to(NOTES_DIR)
        node = tree
        for part in rel.parts[:-1]:
            node = node["_dirs"].setdefault(part, {"_files": [], "_dirs": {}})
        node["_files"].append(rel)
    return tree


def title_from_md(md_path: Path, html_body: str) -> str:
    for line in md_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
    return md_path.stem.replace("-", " ").replace("_", " ").title()


def build_css(colors: dict, effects: dict) -> str:
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

body {{
  min-height: 100vh;
  {"animation: flicker 0.15s infinite alternate;" if effects.get("flicker") else ""}
}}

@keyframes flicker {{
  0%   {{ opacity: 1; }}
  100% {{ opacity: 0.985; }}
}}

/* ---- CRT grain / scanlines overlay ---- */
.crt-overlay {{
  pointer-events: none;
  position: fixed;
  inset: 0;
  z-index: 9999;
  {"" if effects.get("scanlines") else "display:none;"}
  background: repeating-linear-gradient(
    to bottom,
    rgba(255,255,255,0.035) 0px,
    rgba(255,255,255,0.035) 1px,
    transparent 1px,
    transparent 3px
  );
  mix-blend-mode: overlay;
}}

.grain-overlay {{
  pointer-events: none;
  position: fixed;
  inset: 0;
  z-index: 9998;
  {"" if effects.get("grain") else "display:none;"}
  opacity: 0.06;
  background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='120' height='120'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/></filter><rect width='100%25' height='100%25' filter='url(%23n)'/></svg>");
  animation: grain-move 0.4s steps(4) infinite;
}}

@keyframes grain-move {{
  0%   {{ transform: translate(0,0); }}
  25%  {{ transform: translate(-2%,2%); }}
  50%  {{ transform: translate(2%,-2%); }}
  75%  {{ transform: translate(-1%,-1%); }}
  100% {{ transform: translate(1%,1%); }}
}}

/* ---- Boot screen ---- */
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
  animation: boot-fade 0.4s ease-out 1.9s forwards;
}}

@keyframes boot-fade {{
  to {{ opacity: 0; visibility: hidden; }}
}}

#boot-screen .boot-line {{
  opacity: 0;
  animation: boot-line-in 0.25s steps(1) forwards;
}}

@keyframes boot-line-in {{ to {{ opacity: 1; }} }}

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

nav.sidebar a {{
  color: var(--link);
  text-decoration: none;
}}
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

main {{
  flex: 1;
  padding: 30px 40px;
  min-width: 0;
}}

.crumbs {{
  color: var(--muted);
  font-size: 0.8em;
  margin-bottom: 20px;
}}
.crumbs a {{ color: var(--muted); }}

article h1, article h2, article h3, article h4 {{
  color: var(--heading);
  text-shadow: 0 0 5px rgba(0,255,65,0.25);
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
  filter: saturate(0.9) contrast(1.05);
  display: block;
  margin: 16px 0;
}}

article table {{
  border-collapse: collapse;
  width: 100%;
  margin: 16px 0;
}}
article th, article td {{
  border: 1px solid var(--border);
  padding: 6px 10px;
  text-align: left;
}}
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

/* ---- Mobile ---- */
.menu-toggle {{ display: none; }}

@media (max-width: 800px) {{
  .wrap {{ flex-direction: column; }}
  nav.sidebar {{
    width: 100%;
    border-right: none;
    border-bottom: 1px solid var(--border);
  }}
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


def render_boot_screen():
    lines_html = ""
    delay = 0.0
    for i, line in enumerate(BOOT_LINES):
        delay = i * 0.12
        lines_html += f'<div class="boot-line" style="animation-delay:{delay:.2f}s">{line or "&nbsp;"}</div>\n'
    return f"""<div id="boot-screen">{lines_html}</div>"""


def render_sidebar(tree, config, current_slug, depth=0, prefix=""):
    html = ""
    # files at this level
    if tree["_files"]:
        html += '<ul class="tree-files">\n'
        for rel in sorted(tree["_files"], key=lambda p: p.stem.lower()):
            slug = slugify_path(rel)
            title = FILE_TITLES.get(slug, rel.stem)
            active = "active" if slug == current_slug else ""
            html += f'<li class="{active}"><a href="/notes/{slug}.html">{title}</a></li>\n'
        html += "</ul>\n"
    # subdirectories
    for dirname, subtree in sorted(tree["_dirs"].items()):
        html += f'<div class="tree-dir">{dirname}</div>\n'
        html += render_sidebar(subtree, config, current_slug, depth + 1, prefix + dirname + "/")
    return html


FILE_TITLES = {}  # populated during build, slug -> title


PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{page_title} :: {site_title}</title>
<link rel="stylesheet" href="{base}style.css">
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
      <ul class="tree-files"><li class="{home_active}"><a href="{base}index.html">index</a></li></ul>
      {sidebar}
    </div>
  </nav>
  <main>
    <div class="crumbs">{crumbs}</div>
    {content}
    <footer>generated {timestamp} :: terminal notes v1.0</footer>
  </main>
</div>
<script>
  var t = document.getElementById('menu-toggle');
  if (t) t.addEventListener('click', function() {{
    document.getElementById('sidebar').classList.toggle('open');
  }});
</script>
</body>
</html>
"""


def build():
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    (OUT_DIR / "notes").mkdir(parents=True)
    (OUT_DIR / "images").mkdir(parents=True)

    config = load_config()
    colors = config["colors"]
    effects = config.get("effects", {})

    # CSS
    (OUT_DIR / "style.css").write_text(build_css(colors, effects), encoding="utf-8")

    # copy images
    if IMAGES_DIR.exists():
        for img in IMAGES_DIR.rglob("*"):
            if img.is_file():
                rel = img.relative_to(IMAGES_DIR)
                dest = OUT_DIR / "images" / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(img, dest)

    tree = scan_notes()

    # first pass: titles
    all_files = list(NOTES_DIR.rglob("*.md"))
    for md_path in all_files:
        rel = md_path.relative_to(NOTES_DIR)
        slug = slugify_path(rel)
        body_preview = ""
        FILE_TITLES[slug] = title_from_md(md_path, body_preview)

    boot_screen_html = render_boot_screen() if effects.get("boot_animation", True) else ""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    md = markdown.Markdown(extensions=MD_EXTENSIONS, extension_configs=MD_EXT_CONFIG)

    # render each note page
    for md_path in all_files:
        rel = md_path.relative_to(NOTES_DIR)
        slug = slugify_path(rel)
        depth = len(rel.parts) - 1  # how many dirs deep -> for relative base path
        base = "../" * (depth + 1)  # +1 because we're inside /notes/

        md.reset()
        html_body = md.convert(md_path.read_text(encoding="utf-8"))

        title = FILE_TITLES[slug]
        crumbs = ' / '.join(['<a href="{}index.html">home</a>'.format(base)] + list(rel.parts[:-1]) + [title])

        sidebar_html = render_sidebar(tree, config, slug)

        page = PAGE_TEMPLATE.format(
            page_title=title,
            site_title=config["site_title"],
            site_subtitle=config["site_subtitle"],
            base=base,
            boot_screen=boot_screen_html,
            sidebar=sidebar_html,
            crumbs=crumbs,
            content=f"<article>{html_body}</article>",
            timestamp=timestamp,
            home_active="",
        )

        out_path = OUT_DIR / "notes" / rel.with_suffix(".html")
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(page, encoding="utf-8")

    # fix image src paths: convert "/images/x.png" references to correct relative base
    # (handled by using absolute-from-root paths + copying images to docs/images,
    #  but since GitHub Pages project sites can live in a subpath, we rewrite to relative)
    fix_image_paths()

    # build index page
    build_index(tree, config, boot_screen_html, timestamp)

    # copy README/deploy helper already in root; nothing else to do
    print(f"Build complete. {len(all_files)} notes rendered into {OUT_DIR}")


def fix_image_paths():
    """Rewrite absolute /images/... and /notes/... links to relative paths
    so the site works both at the domain root and under a github.io/<repo>/ subpath."""
    for html_path in (OUT_DIR / "notes").rglob("*.html"):
        rel = html_path.relative_to(OUT_DIR / "notes")
        depth = len(rel.parts) - 1
        base = "../" * (depth + 1)
        text = html_path.read_text(encoding="utf-8")
        text = text.replace('src="/images/', f'src="{base}images/')
        text = text.replace('href="/notes/', f'href="{base}notes/')
        text = text.replace('href="/images/', f'href="{base}images/')
        html_path.write_text(text, encoding="utf-8")


def build_index(tree, config, boot_screen_html, timestamp):
    def render_index_section(subtree, heading_path):
        html = ""
        if heading_path:
            html += f"<h2>{heading_path}</h2>\n"
        if subtree["_files"]:
            html += '<ul class="index-list">\n'
            for rel in sorted(subtree["_files"], key=lambda p: p.stem.lower()):
                slug = slugify_path(rel)
                title = FILE_TITLES.get(slug, rel.stem)
                html += f'<li><a href="notes/{slug}.html">{title}</a></li>\n'
            html += "</ul>\n"
        for dirname, sub in sorted(subtree["_dirs"].items()):
            new_path = f"{heading_path}/{dirname}" if heading_path else dirname
            html += render_index_section(sub, new_path)
        return html

    banner_html = f'<pre class="ascii-banner">{ASCII_BANNER}</pre>' if config.get("ascii_banner") else ""
    body = banner_html + "<h1>Index</h1>\n" + render_index_section(tree, "")

    sidebar_html = render_sidebar(tree, config, current_slug=None)

    page = PAGE_TEMPLATE.format(
        page_title="index",
        site_title=config["site_title"],
        site_subtitle=config["site_subtitle"],
        base="",
        boot_screen=boot_screen_html,
        sidebar=sidebar_html,
        crumbs="home",
        content=f"<article>{body}</article>",
        timestamp=timestamp,
        home_active="active",
    )
    page = page.replace('src="/images/', 'src="images/')
    (OUT_DIR / "index.html").write_text(page, encoding="utf-8")


if __name__ == "__main__":
    build()
