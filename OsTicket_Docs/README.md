# OsTicket Docs (Production Setup)

This folder contains the MkDocs + Material configuration for the osTicket documentation site.

## Prerequisites

- Python 3.12+
- Virtual environment at `OsTicket_Docs/.venv`

## Install dependencies

Use the project virtual environment:

- `python -m pip install -U pip`
- `python -m pip install "mkdocs>=1.6.1,<2.0" "mkdocs-material>=9.7.6,<10.0"`

## Local preview (PowerShell)

Material 9.7+ may print the MkDocs 2.0 compatibility notice. To hide it locally:

- `$env:NO_MKDOCS_2_WARNING = "1"`
- `mkdocs serve --dev-addr=0.0.0.0:8001`

## Production build

- `mkdocs build --strict`

This project is configured with:

- strict mode
- link/nav validation
- explicit `not_in_nav` list for intentionally unlisted pages
- stable dependency pinning to MkDocs 1.x-compatible versions

## GitHub Pages deployment

Manual deployment:

- `mkdocs gh-deploy --force`

For CI/CD, use GitHub Actions as documented in Material for MkDocs publishing docs.

