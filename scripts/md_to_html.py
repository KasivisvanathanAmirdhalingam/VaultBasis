#!/usr/bin/env python3
"""
VaultBasis — minimal Markdown-to-HTML renderer (stdlib only).
Single rendering source of truth for normative docs served as pages:
used by scripts/build_public_web.js (Vercel bundle) and edge/api/app.py
(local Edge dashboard). Supports the subset used by docs/*: h1-h3,
bold, inline code, links, ordered/unordered lists (one nesting level),
horizontal rules, paragraphs. No third-party dependencies.
"""
import html
import re
import sys
from pathlib import Path


def _inline(text: str) -> str:
    text = html.escape(text, quote=False)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
    return text


def render_body(md_text: str) -> str:
    lines = md_text.splitlines()
    out = []
    in_ul = in_ol = in_sub = False

    def close_lists():
        nonlocal in_ul, in_ol, in_sub
        if in_sub:
            out.append("</ul>")
            in_sub = False
        if in_ul:
            out.append("</ul>")
            in_ul = False
        if in_ol:
            out.append("</ol>")
            in_ol = False

    for raw in lines:
        line = raw.rstrip()
        if not line.strip():
            close_lists()
            continue
        if re.match(r"^---+\s*$", line.strip()):
            close_lists()
            out.append("<hr>")
            continue
        m = re.match(r"^(#{1,3})\s+(.*)$", line.strip())
        if m:
            close_lists()
            level = len(m.group(1))
            out.append(f"<h{level}>{_inline(m.group(2))}</h{level}>")
            continue
        m = re.match(r"^(\s*)(\d+)\.\s+(.*)$", line)
        if m:
            indent = len(m.group(1).replace("\t", "  "))
            if indent >= 2:
                if not in_sub:
                    if not in_ol:
                        out.append("<ol>")
                        in_ol = True
                    out.append("<ul class='sub'>")
                    in_sub = True
                out.append(f"<li>{_inline(m.group(3))}</li>")
            else:
                if in_sub:
                    out.append("</ul>")
                    in_sub = False
                if not in_ol:
                    close_lists()
                    out.append("<ol>")
                    in_ol = True
                out.append(f"<li>{_inline(m.group(3))}</li>")
            continue
        m = re.match(r"^(\s*)[*-]\s+(.*)$", line)
        if m:
            indent = len(m.group(1).replace("\t", "  "))
            if indent >= 2:
                if not in_sub:
                    if not in_ul:
                        out.append("<ul>")
                        in_ul = True
                    out.append("<ul class='sub'>")
                    in_sub = True
                out.append(f"<li>{_inline(m.group(2))}</li>")
            else:
                if in_sub:
                    out.append("</ul>")
                    in_sub = False
                if not in_ul:
                    close_lists()
                    out.append("<ul>")
                    in_ul = True
                out.append(f"<li>{_inline(m.group(2))}</li>")
            continue
        close_lists()
        # hard line break: two trailing spaces
        if raw.endswith("  "):
            out.append(f"<p>{_inline(line.strip())}</p>")
        else:
            out.append(f"<p>{_inline(line.strip())}</p>")

    close_lists()
    return "\n".join(out)


PAGE_CSS = """
:root{--bg:#f8fafc;--surface:#fff;--text:#0f172a;--muted:#475569;--primary:#2563eb;--border:#e2e8f0}
*{box-sizing:border-box}body{background:var(--bg);color:var(--text);font-family:'Plus Jakarta Sans',-apple-system,'Segoe UI',sans-serif;line-height:1.75;margin:0}
.wrap{max-width:780px;margin:0 auto;padding:2.5rem 1.5rem 4rem}nav.top{margin-bottom:2rem;font-size:.9rem}nav.top a{color:var(--primary);text-decoration:none}
.card{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:2.25rem 2.5rem;box-shadow:0 1px 3px rgba(15,23,42,.06)}
.doc-title{font-size:1.75rem;font-weight:700;margin:0 0 .35rem;color:var(--text)}
.doc-meta{font-size:.85rem;color:var(--muted);margin:0 0 1.5rem;line-height:1.6}
h2{font-size:1.2rem;font-weight:700;margin:2rem 0 .6rem;padding-top:1.25rem;border-top:1px solid var(--border);color:var(--text)}
h3{font-size:1rem;font-weight:600;margin:1.25rem 0 .4rem}
p{margin:.6rem 0;color:#1e293b}
ul{padding-left:1.4rem;margin:.5rem 0}
ul ul{margin:.25rem 0}
li{margin:.4rem 0;color:#1e293b}
li ul li{margin:.25rem 0;color:#334155}
code{background:#f1f5f9;border:1px solid var(--border);border-radius:4px;padding:1px 6px;font-family:'JetBrains Mono',monospace;font-size:.84em}
hr{border:none;border-top:1px solid var(--border);margin:1.75rem 0}a{color:var(--primary)}
footer{margin-top:2.5rem;font-size:.8rem;color:var(--muted);text-align:center}
"""


def render_page(md_text: str, title: str, back_href: str = "/", back_label: str = "← VaultBasis Home") -> str:
    # Strip the h1 and any leading bold key:value meta lines from the body —
    # they are rendered as a styled header block instead.
    lines = md_text.splitlines()
    meta_lines = []
    body_start = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("# "):
            body_start = i + 1
            continue
        if re.match(r"^\*\*[^*]+:\*\*", stripped) and i <= body_start + 4:
            # Extract the value after the bold label
            m = re.match(r"^\*\*([^*]+):\*\*\s*(.*)", stripped)
            if m:
                meta_lines.append(f"{html.escape(m.group(1))}: {html.escape(m.group(2))}")
            body_start = i + 1
        elif stripped == "" and i == body_start:
            body_start = i + 1
        elif stripped == "---" and i == body_start:
            body_start = i + 1
            break
        elif i > body_start + 5:
            break

    remaining_md = "\n".join(lines[body_start:])
    body = render_body(remaining_md)

    meta_html = ""
    if meta_lines:
        meta_html = f'<p class="doc-meta">{" &nbsp;·&nbsp; ".join(meta_lines)}</p>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)}</title>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>{PAGE_CSS}</style></head>
<body><div class="wrap">
<nav class="top"><a href="{back_href}">{html.escape(back_label)}</a></nav>
<div class="card">
<h1 class="doc-title">{html.escape(title)}</h1>
{meta_html}
{body}
</div>
<footer>© 2026 VaultBasis. All rights reserved.</footer>
</div></body></html>"""


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: md_to_html.py <input.md> <output.html>", file=sys.stderr)
        return 2
    src, dst = Path(sys.argv[1]), Path(sys.argv[2])
    md = src.read_text(encoding="utf-8")
    title = next((l.strip("# ").strip() for l in md.splitlines() if l.startswith("# ")), src.stem)
    dst.write_text(render_page(md, title), encoding="utf-8")
    print(f"rendered {src} -> {dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
