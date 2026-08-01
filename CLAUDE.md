# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

LaTeX source for William E Fondrie's CV. A Python script renders a Jinja2 template
into `fondrie_cv.tex`, which `pdflatex` turns into the committed `fondrie_cv.pdf`.

## Commands

```sh
make              # build.py -> fondrie_cv.tex -> fondrie_cv.pdf (runs pdflatex twice)
python build.py   # regenerate fondrie_cv.tex only
make clean        # remove *.aux, *.log, *.out, auto/
```

`build.py` needs `jinja2` and `pybtex`. There is no dependency manifest; the base
`mambaforge` env on this machine has both, and the Makefile's bare `python` resolves
there. `uv run --with jinja2 --with pybtex python build.py` also works.

No tests, no linter config.

## Architecture

Three inputs feed one template:

- `pubs.bib` — Zotero/Better BibTeX export of publications.
- `presentations.json` — list of talk objects (`kind` is `invited` or `talk`).
- `fondrie_cv.template.tex` — the actual CV; everything except publication and
  talk lists is hand-written LaTeX here.

`build.py` parses the first two into `Reference` / `Presentation` dataclasses, sorts
each group newest-first, renders each into a `\item ...` APA-style string, and injects
the joined blocks into the template as `articles`, `preprints`, `dissertation`,
`invited`, and `talks`.

### Editing rules

- **Never edit `fondrie_cv.tex`** — it is generated and gitignored. Edit the template.
- Adding a paper = append a BibTeX entry to `pubs.bib`. Adding a talk = append an
  object to `presentations.json`. Everything else (education, employment, awards,
  patents, grants, software, teaching, service, blog posts) is edited directly in
  `fondrie_cv.template.tex`.
- Jinja uses default `{{ }}` / `{% %}` delimiters, so LaTeX `\newcommand` bodies
  containing `#1` sit inside a `{% raw %}` block (template lines 40–61). Any new
  macro definitions must go inside that block or get their own raw block.
- Commit the regenerated `fondrie_cv.pdf` — it is the tracked deliverable.

### Classification quirks in `build.py`

- `COFIRST` maps DOI -> number of leading co-first authors; those names get a `*`.
  New co-first papers must be added there manually.
- `citation_type` routes an entry to preprints if its journal is in
  `PREPRINT_SERVERS`, and to the dissertation section by matching the title prefix
  `"biological insight from mass"`.
- `format_person` bolds any author whose last name is `Fondrie`.
- Entries missing `journal` fall back to `publisher` / `booktitle`, or to `bioRxiv`
  when `type = Preprint`.
- Months come from BibTeX macros and are parsed with `%B`, so a non-full-month value
  will raise at build time.

### Makefile note

The `bibtex` step in the pattern rule never fires — citations are inlined as literal
`\item` text, so the `.aux` contains no `\citation` entries.
