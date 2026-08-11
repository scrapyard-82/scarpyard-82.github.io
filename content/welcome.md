# Welcome to the Terminal

This is your **personal notes system**, styled like an old *BBS terminal* from the days
of dial-up modems and green phosphor screens.

## How it works

- Write notes as plain Markdown in the `notes/` folder.
- Put images in the `images/` folder and reference them like `![alt](/images/foo.png)`.
- Subfolders (like `notes/articles/`) become sections, shown in the sidebar tree.
- Run `python build.py` to regenerate the static site into `docs/`.
- Push to GitHub, enable Pages on the `docs/` folder, done.

## Styling

Colors for `headings`, **bold**, *italic*, and `inline code` are all controlled from
`config.json` — no need to touch the CSS unless you want to.

> Blockquotes look like old terminal system messages.

```python
def hello():
    print("this is a code block")
```

Check out the [example article](/notes/articles/example-article.html) for a demo with an image.
