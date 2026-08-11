# Terminal Notes — BBS-style Markdown notes site

A static site generator for a personal notes/articles site with an old-school
BBS/CRT-terminal look: pitch black background, phosphor colors, scanlines,
VHS-style grain, and a little boot-up animation. Runs entirely as a Python
build step — the output is plain HTML/CSS, so it hosts perfectly on
`github.io` with zero server-side code.

## Folder structure

```
notes/                 <- your Markdown notes
  welcome.md
  articles/             <- subfolders become sections ("subnotes")
    example-article.md
    2026/
      some-deep-note.md
images/                <- images referenced from your notes
config.json             <- colors + effect toggles
build.py                <- generator, run this to rebuild
docs/                   <- generated output (this is what GitHub Pages serves)
```

## Writing notes

Just write Markdown in `notes/`. The first `# Heading` in the file becomes
its page title (falls back to the filename otherwise).

Reference images like this (always use `/images/...`, the build step rewrites
it correctly no matter how deep the note is nested):

```markdown
![alt text](/images/my-photo.png)
```

Any subfolder under `notes/` (e.g. `notes/articles/`, `notes/articles/2026/`)
is automatically picked up as a section and shown in the sidebar tree and on
the homepage index — no extra config needed.

## Customizing colors

Edit `config.json`:

```json
"colors": {
  "background": "#000000",
  "heading": "#00ff41",
  "bold": "#ffb000",
  "italic": "#00e5ff",
  "code": "#ff2079",
  ...
}
```

Any valid hex color works. Re-run the build afterward.

You can also toggle effects (grain, scanlines, boot animation, flicker) under
`"effects"` in the same file.

## Building

```bash
pip install markdown
python3 build.py
```

This regenerates the entire `docs/` folder from scratch based on the current
contents of `notes/`, `images/`, and `config.json`.

## Deploying to GitHub Pages

1. Create a new GitHub repo, e.g. `my-notes`.
2. Push this whole project (including the generated `docs/` folder) to the
   repo's `main` branch.
3. In the repo settings → **Pages**, set:
   - Source: `Deploy from a branch`
   - Branch: `main`, folder: `/docs`
4. Your site will be live at `https://<username>.github.io/my-notes/`
   (or `https://<username>.github.io/` if the repo is named
   `<username>.github.io`).

Whenever you add or edit notes, just run `python3 build.py` again, commit,
and push — the site rebuilds instantly (no CI needed, though you could add a
GitHub Action to run `build.py` automatically on push if you want to skip the
manual step).

## Mobile

The layout collapses to a single column with a `[ menu ]` toggle for the
sidebar below ~800px width. Fully usable on phones.

## Notes on the aesthetic

- Pitch-black background (`#000`) with phosphor-green (customizable) text glow.
- CRT scanline overlay + animated VHS-style grain (pure CSS, no images).
- A short ASCII-art boot sequence plays once on every page load, then fades
  into the actual page.
- ASCII banner on the homepage (edit `ASCII_BANNER` in `build.py` to change it).

Everything is static HTML/CSS/minimal JS (just a mobile menu toggle) — no
frameworks, no build tools beyond Python + the `markdown` package.
