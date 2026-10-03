# AGENTS.md

## Project Overview
BookBot is a simple Python CLI script that reads a text file (`books/frankenstein.txt`) and prints a word/character frequency report. There are no third-party dependencies — it uses only the Python standard library.

## Running in Base44
- The web preview is served by `server.py`, a stdlib-only HTTP server (port 3000) that imports the analysis functions from `main.py` and renders the report as HTML.
- `main.py` has an `if __name__ == "__main__"` guard so its functions can be imported by `server.py` without auto-executing.
- `docker-compose.base44.yml` runs `python3 server.py` from a `python:3.12-slim` image with the repo bind-mounted.

## Notes
- `books/` is gitignored. `books/frankenstein.txt` must be present for the app to work — it was downloaded from Project Gutenberg (ebook #84) during setup and lives outside git.
- No external credentials or secrets are needed.
- No package manager or dependency installation step is required.
