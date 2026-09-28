import os

file_path = "apps/web-verifier/index.html"
with open(file_path, "r") as f:
    content = f.read()

# 1. Replace CSS Variables
new_css = """
    :root {
      --bg: #f8fafc;
      --surface: #ffffff;
      --surface-elevated: #f1f5f9;
      --border: #e2e8f0;
      --border-accent: #cbd5e1;
      --text: #0f172a;
      --text-muted: #475569;
      --primary: #2563eb;
      --primary-hover: #1d4ed8;
      --accent: #0284c7;
      --success: #059669;
      --danger: #ef4444;
      --warning: #f59e0b;
      --radius: 12px;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    html {
      scroll-behavior: smooth;
      scroll-padding-top: 6.5rem;
    }
    section[id],
    .card,
    [id] {
      scroll-margin-top: 6.5rem;
    }
    body {
      background-color: var(--bg);
      color: var(--text);
      font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }
    header {
      background: rgba(255, 255, 255, 0.92);
      backdrop-filter: blur(12px);
      border-bottom: 1px solid var(--border);
      padding: 1rem 2rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
      position: sticky;
      top: 0;
      z-index: 100;
      box-shadow: 0 4px 20px rgba(0,0,0,0.03);
    }
    .brand {
      display: flex;
      align-items: center;
      gap: 12px;
      text-decoration: none;
      color: inherit;
    }
    .brand-logo {
      width: 36px;
      height: 36px;
      background: linear-gradient(135deg, #2563eb, #0284c7);
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 800;
      font-size: 1.15rem;
      color: white;
      box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
    }
    .brand-name {
      font-family: 'Outfit', sans-serif;
      font-size: 1.35rem;
      font-weight: 800;
      letter-spacing: -0.01em;
      color: #0f172a;
    }
    .nav-links {
      display: flex;
      gap: 2rem;
      align-items: center;
    }
    .nav-links a {
      color: var(--text-muted);
      text-decoration: none;
      font-size: 0.95rem;
      font-weight: 600;
      transition: color 0.2s;
    }
    .nav-links a:hover { color: var(--text); }
    .badge {
      display: inline-block;
      padding: 4px 10px;
      border-radius: 6px;
      font-size: 0.78rem;
      font-family: 'JetBrains Mono', monospace;
      font-weight: 700;
    }
    .badge-pass { background: #ecfdf5; color: #059669; border: 1px solid #a7f3d0; }
    .badge-fail { background: #fef2f2; color: #dc2626; border: 1px solid #fecaca; }
    .badge-info { background: #eff6ff; color: #2563eb; border: 1px solid #bfdbfe; }

    .container {
      max-width: 960px;
      margin: 4rem auto;
      padding: 0 1.5rem;
      flex: 1;
      width: 100%;
    }
    .card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      padding: 2.5rem;
      margin-bottom: 2rem;
      box-shadow: 0 4px 6px rgba(0,0,0,0.02);
    }
    .dropzone {
      border: 2px dashed #94a3b8;
      border-radius: var(--radius);
      padding: 4rem 2rem;
      text-align: center;
      cursor: pointer;
      background: #f8fafc;
      transition: all 0.2s;
    }
    .dropzone:hover {
      border-color: var(--primary);
      background: #eff6ff;
    }
    .btn {
      padding: 10px 18px;
      border-radius: 8px;
      font-size: 0.9rem;
      font-weight: 600;
      text-decoration: none;
      transition: all 0.2s;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      border: 1px solid transparent;
    }
    .btn:focus-visible, a:focus-visible, input:focus-visible, #dropzone:focus-visible {
      outline: 2px solid var(--primary);
      outline-offset: 2px;
    }
    .btn-primary { background: var(--primary); color: white; border-color: var(--primary); box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2); }
    .btn-primary:hover { background: var(--primary-hover); transform: translateY(-1px); }
    .btn-secondary { background: #fff; color: var(--text); border-color: var(--border-accent); box-shadow: 0 2px 4px rgba(0,0,0,0.02); }
    .btn-secondary:hover { background: var(--surface-elevated); }

    .sample-controls {
      display: flex;
      gap: 1rem;
      justify-content: center;
      margin-top: 1.5rem;
      flex-wrap: wrap;
    }

    .check-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 14px 0;
      border-bottom: 1px solid var(--border);
      font-size: 0.95rem;
    }
    .check-row:last-child {
      border-bottom: none;
    }
    .limitations-box {
      background: #fffbeb;
      border: 1px solid #fde68a;
      border-radius: 8px;
      padding: 1.25rem;
      font-size: 0.85rem;
      color: #92400e;
      line-height: 1.6;
      margin-top: 2rem;
    }

    /* Light Footer */
    footer.site-footer {
      border-top: 1px solid var(--border);
      background: var(--surface);
      margin-top: auto;
      padding: 4rem 2rem 2rem 2rem;
    }
    .footer-grid {
      max-width: 1100px;
      margin: 0 auto;
      display: grid;
      grid-template-columns: 2fr 1fr 1fr 1fr;
      gap: 3rem;
      padding-bottom: 3rem;
      border-bottom: 1px solid var(--border);
    }
    .footer-col h4 {
      font-size: 0.85rem;
      font-family: 'JetBrains Mono', monospace;
      text-transform: uppercase;
      letter-spacing: 0.1em;
      color: var(--text);
      margin-bottom: 1.25rem;
      font-weight: 700;
    }
    .footer-col ul { list-style: none; }
    .footer-col ul li { margin-bottom: 0.8rem; }
    .footer-col ul li a {
      color: var(--text-muted);
      text-decoration: none;
      font-size: 0.9rem;
      font-weight: 500;
      transition: color 0.2s;
    }
    .footer-col ul li a:hover { color: var(--primary); }
    .footer-bottom {
      max-width: 1100px;
      margin: 2rem auto 0 auto;
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 0.85rem;
      color: var(--text-muted);
    }
"""

start_css = content.find(":root {")
end_css = content.find("</style>")
if start_css != -1 and end_css != -1:
    content = content[:start_css] + new_css + content[end_css:]

# 2. Replace hardcoded white texts and borders in inline styles
content = content.replace("color: #fff;", "color: #0f172a;")
content = content.replace("color: #ffffff;", "color: #0f172a;")
content = content.replace("background: #080b11;", "background: #ffffff;")
content = content.replace("border-color: rgba(239, 68, 68, 0.4); color: #f87171;", "border-color: #fecaca; color: #dc2626; background: #fef2f2;")
content = content.replace("color: #93c5fd;", "color: #2563eb;")

with open(file_path, "w") as f:
    f.write(content)

print("Retheme applied successfully!")
