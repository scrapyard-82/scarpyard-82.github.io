# Terminal Notes — BBS-style Markdown notes site

Static site generator: write Markdown in `content/`, run `python3 build.py`,
get a full HTML/CSS site at the repo root — deploy straight to GitHub Pages,
no server needed.

## Folder structure

```
content/               <- your Markdown source files (NOT served directly)
  welcome.md
  articles/
    example-article.md
images/                <- your images, single canonical copy, served as-is
notes/                 <- GENERATED html pages (deleted & rebuilt every run)
index.html             <- GENERATED
style.css              <- GENERATED
config.json            <- colors + effect toggles
build.py               <- run this to (re)build the site
```

Only `content/`, `images/`, `config.json`, and `build.py` are things you
edit. Everything else (`notes/`, `index.html`, `style.css`) is regenerated
every time you run the build — don't hand-edit those.

## Writing notes

Write Markdown in `content/`. The first `# Heading` becomes the page title.
Subfolders (e.g. `content/articles/`) automatically become sections in the
sidebar and homepage — nest as deep as you like.

Reference images like this — always `/images/...`, works from any note at
any depth:

```markdown
![alt text](/images/my-photo.png)
```

## Colors

Edit `config.json` → `"colors"`. Any hex value works for `heading`, `bold`,
`italic`, `code`, etc. Re-run the build after changing.

Effects (`grain`, `scanlines`, `boot_animation`) can be toggled off there too.
The boot animation now only plays once per browser (stored via
`localStorage`), not on every page load.

## Building

```bash
pip install markdown
python3 build.py
```

## Deploying to GitHub Pages — step by step

Your repo is currently named `scarpyard-82.github.io`, but your GitHub
username is `scrapyard-82` — the letters are swapped. GitHub only auto-serves
a repo at the clean root URL (`https://scrapyard-82.github.io/`) if the repo
name is an **exact** match for `<username>.github.io`. That mismatch is why
you were getting the doubled `/scarpyard-82.github.io/scarpyard-82.github.io/`
URL.

**Fix it first:** go to the repo → Settings → rename it to exactly
`scrapyard-82.github.io` (matching your username, letter for letter). Once
renamed, the site will automatically live at `https://scrapyard-82.github.io/`.

Then, to push this project:

```bash
# 1. Unzip this project locally, cd into it
cd terminal-notes

# 2. Build the site (generates notes/, index.html, style.css)
pip install markdown
python3 build.py

# 3. Initialize git and point it at your (renamed) repo
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/scrapyard-82/scrapyard-82.github.io.git
git push -u origin main
```

If the repo already has commits (e.g. a README GitHub made for you), pull
first to avoid conflicts:

```bash
git pull origin main --allow-unrelated-histories
# resolve any conflicts, then:
git push -u origin main
```

**In GitHub repo settings → Pages:**
- Source: `Deploy from a branch`
- Branch: `main`, folder: `/ (root)`

Give it a minute or two, then visit `https://scrapyard-82.github.io/`.

### Updating the site later

Whenever you add/edit notes:

```bash
python3 build.py
git add .
git commit -m "Update notes"
git push
```

That's it — GitHub Pages redeploys automatically on every push.

## Mobile

Layout collapses to one column with a `[ menu ]` toggle below ~800px width.

## Design notes

- Pitch-black background, phosphor-colored headings/bold/italic/code (all
  configurable).
- Subtle CRT scanline overlay + light grain texture (dialed back from v1 —
  no more constant flicker).
- A short ASCII-art boot sequence plays once, the very first time someone
  visits your site in their browser, then never again (until they clear
  their browser storage).
- ASCII banner on the homepage — edit `ASCII_BANNER` in `build.py` to
  customize it.
