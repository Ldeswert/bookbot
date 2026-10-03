"""Minimal web server that renders the BookBot report in the browser.

Uses only the Python standard library so no pip install is needed.
Imports the analysis functions from main.py rather than duplicating logic.
"""

import html
import os
from http.server import HTTPServer, BaseHTTPRequestHandler

from main import get_book_text, get_num_words, get_chars_dict, chars_dict_to_sorted_list

BOOK_PATH = os.environ.get("BOOK_PATH", "books/frankenstein.txt")


def build_report_html():
    text = get_book_text(BOOK_PATH)
    num_words = get_num_words(text)
    chars_dict = get_chars_dict(text)
    chars_sorted_list = chars_dict_to_sorted_list(chars_dict)

    rows = []
    max_num = max(item["num"] for item in chars_sorted_list if item["char"].isalpha())
    for item in chars_sorted_list:
        if not item["char"].isalpha():
            continue
        pct = int(item["num"] / max_num * 100)
        rows.append(
            f"<tr><td class='char'>{html.escape(item['char'])}</td>"
            f"<td>{item['num']:,}</td>"
            f"<td><div class='bar' style='width:{pct}%'></div></td></tr>"
        )

    rows_html = "\n".join(rows)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>BookBot Report</title>
<style>
  :root {{
    --bg: #1a1a2e;
    --card: #16213e;
    --accent: #0f3460;
    --text: #e0e0e0;
    --highlight: #e94560;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
    display: flex;
    justify-content: center;
    padding: 2rem 1rem;
  }}
  .container {{ max-width: 700px; width: 100%; }}
  h1 {{ color: var(--highlight); margin-bottom: 0.25rem; }}
  .subtitle {{ color: #8899aa; margin-bottom: 2rem; font-size: 0.95rem; }}
  .stat {{
    display: inline-block;
    background: var(--card);
    border: 1px solid var(--accent);
    border-radius: 12px;
    padding: 1rem 1.5rem;
    margin-bottom: 2rem;
  }}
  .stat .num {{ font-size: 2rem; font-weight: 700; color: var(--highlight); }}
  .stat .label {{ font-size: 0.85rem; color: #8899aa; }}
  table {{ width: 100%; border-collapse: collapse; }}
  th {{
    text-align: left;
    padding: 0.5rem 0.5rem 0.75rem;
    color: #8899aa;
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    border-bottom: 1px solid var(--accent);
  }}
  td {{ padding: 0.4rem 0.5rem; border-bottom: 1px solid #1a2744; }}
  td.char {{
    font-family: 'Courier New', monospace;
    font-weight: 700;
    font-size: 1.1rem;
    color: var(--highlight);
    width: 2rem;
  }}
  .bar {{
    height: 18px;
    border-radius: 4px;
    background: linear-gradient(90deg, var(--highlight), #c73652);
    min-width: 2px;
  }}
</style>
</head>
<body>
<div class="container">
  <h1>📚 BookBot</h1>
  <p class="subtitle">Report of <code>{html.escape(BOOK_PATH)}</code></p>
  <div class="stat">
    <div class="num">{num_words:,}</div>
    <div class="label">words found</div>
  </div>
  <table>
    <thead><tr><th>Char</th><th>Count</th><th style="width:60%">Frequency</th></tr></thead>
    <tbody>
{rows_html}
    </tbody>
  </table>
</div>
</body>
</html>"""


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = build_report_html().encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        print(fmt % args)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"BookBot server listening on 0.0.0.0:{port}")
    server.serve_forever()
