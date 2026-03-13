import anthropic
import json
import datetime
import os

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

today = datetime.date.today().strftime("%Y. %m. %d.")

response = client.messages.create(
    model="claude-opus-4-5",
    max_tokens=4000,
    tools=[{
        "type": "web_search_20250305",
        "name": "web_search"
    }],
    messages=[{
        "role": "user",
        "content": f"""Mai dátum: {today}

Keress rá a legfrissebb AI hírekre az alábbi témakörökben:
1. Magyar AI hírek (pl. hazai fejlesztések, szabályozás, vállalatok)
2. Nemzetközi nagy AI fejlesztések (OpenAI, Google, Anthropic, Meta, stb.)
3. AI szabályozás és etika
4. Érdekes/futurisztikus AI alkalmazások

Keress legalább 8-10 friss hírt a mai napról vagy az elmúlt 24 órából.

Majd adj vissza KIZÁRÓLAG egy valid JSON objektumot, semmi mást, ebben a formátumban:
{{
  "date": "{today}",
  "summary": "2-3 mondatos összefoglaló magyarul a mai AI hírekről",
  "news": [
    {{
      "title": "Hír címe magyarul",
      "summary": "2-3 mondatos összefoglaló magyarul",
      "source": "Forrás neve",
      "url": "https://...",
      "category": "Magyar" | "Nemzetközi" | "Szabályozás" | "Alkalmazások"
    }}
  ]
}}

Fontos: csak JSON-t adj vissza, markdown kód blokkot se használj!"""
    }]
)

# Extract JSON from response
news_json = None
for block in response.content:
    if block.type == "text":
        text = block.text.strip()
        # Remove markdown code blocks if present
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1])
        try:
            news_json = json.loads(text)
            break
        except json.JSONDecodeError:
            # Try to find JSON within the text
            import re
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                try:
                    news_json = json.loads(match.group())
                    break
                except:
                    pass

if not news_json:
    # Fallback
    news_json = {
        "date": today,
        "summary": "A hírek betöltése során hiba történt. Kérjük, próbálja újra később.",
        "news": []
    }

# Category colors and icons
cat_style = {
    "Magyar": ("🇭🇺", "#e63946"),
    "Nemzetközi": ("🌍", "#457b9d"),
    "Szabályozás": ("⚖️", "#2d6a4f"),
    "Alkalmazások": ("🚀", "#7b2d8b"),
}

news_items_html = ""
for item in news_json.get("news", []):
    cat = item.get("category", "Nemzetközi")
    icon, color = cat_style.get(cat, ("📰", "#457b9d"))
    news_items_html += f"""
    <article class="news-card" data-category="{cat}">
      <div class="card-accent" style="background:{color}"></div>
      <div class="card-body">
        <span class="category-badge" style="color:{color}; border-color:{color}20; background:{color}10">{icon} {cat}</span>
        <h2 class="card-title">{item.get('title','')}</h2>
        <p class="card-summary">{item.get('summary','')}</p>
        <a href="{item.get('url','#')}" class="card-link" target="_blank" rel="noopener">
          <span>{item.get('source','Forrás')}</span>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6"/><polyline points="15,3 21,3 21,9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
        </a>
      </div>
    </article>"""

html = f"""<!DOCTYPE html>
<html lang="hu">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI Hírek – {news_json['date']}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:ital,wght@0,300;0,400;1,300&display=swap" rel="stylesheet">
<style>
  :root {{
    --bg: #0a0a0f;
    --surface: #13131a;
    --border: #1e1e2e;
    --text: #e8e8f0;
    --muted: #6b6b8a;
    --accent: #c8ff00;
  }}

  * {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    background: var(--bg);
    color: var(--text);
    font-family: 'DM Sans', sans-serif;
    font-weight: 300;
    min-height: 100vh;
    overflow-x: hidden;
  }}

  /* Animated grid background */
  body::before {{
    content: '';
    position: fixed;
    inset: 0;
    background-image:
      linear-gradient(rgba(200,255,0,0.03) 1px, transparent 1px),
      linear-gradient(90deg, rgba(200,255,0,0.03) 1px, transparent 1px);
    background-size: 60px 60px;
    pointer-events: none;
    z-index: 0;
  }}

  .container {{
    max-width: 900px;
    margin: 0 auto;
    padding: 0 24px;
    position: relative;
    z-index: 1;
  }}

  /* Header */
  header {{
    padding: 60px 0 40px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 48px;
    animation: fadeDown 0.6s ease both;
  }}

  .header-tag {{
    font-family: 'Syne', sans-serif;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: var(--accent);
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 8px;
  }}

  .header-tag::before {{
    content: '';
    display: inline-block;
    width: 6px;
    height: 6px;
    background: var(--accent);
    border-radius: 50%;
    animation: pulse 2s ease infinite;
  }}

  h1 {{
    font-family: 'Syne', sans-serif;
    font-size: clamp(2.2rem, 5vw, 3.4rem);
    font-weight: 800;
    line-height: 1.05;
    letter-spacing: -0.03em;
    margin-bottom: 20px;
  }}

  h1 em {{
    font-style: normal;
    color: var(--accent);
  }}

  .summary-box {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-left: 3px solid var(--accent);
    padding: 20px 24px;
    border-radius: 0 8px 8px 0;
    color: var(--muted);
    line-height: 1.7;
    font-size: 0.95rem;
    margin-top: 24px;
  }}

  /* Filter buttons */
  .filters {{
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    margin-bottom: 36px;
    animation: fadeUp 0.6s 0.2s ease both;
  }}

  .filter-btn {{
    background: var(--surface);
    border: 1px solid var(--border);
    color: var(--muted);
    padding: 8px 18px;
    border-radius: 100px;
    font-family: 'Syne', sans-serif;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    cursor: pointer;
    transition: all 0.2s;
  }}

  .filter-btn:hover, .filter-btn.active {{
    border-color: var(--accent);
    color: var(--accent);
    background: rgba(200,255,0,0.05);
  }}

  /* News grid */
  .news-grid {{
    display: grid;
    gap: 16px;
  }}

  .news-card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    overflow: hidden;
    display: flex;
    transition: transform 0.2s, border-color 0.2s;
    animation: fadeUp 0.5s ease both;
  }}

  .news-card:hover {{
    transform: translateY(-2px);
    border-color: #2e2e42;
  }}

  .card-accent {{
    width: 4px;
    flex-shrink: 0;
    opacity: 0.8;
  }}

  .card-body {{
    padding: 20px 24px;
    flex: 1;
  }}

  .category-badge {{
    display: inline-block;
    font-family: 'Syne', sans-serif;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    padding: 3px 10px;
    border-radius: 100px;
    border: 1px solid;
    margin-bottom: 10px;
  }}

  .card-title {{
    font-family: 'Syne', sans-serif;
    font-size: 1.05rem;
    font-weight: 700;
    line-height: 1.3;
    margin-bottom: 10px;
    color: var(--text);
  }}

  .card-summary {{
    font-size: 0.88rem;
    line-height: 1.65;
    color: var(--muted);
    margin-bottom: 16px;
  }}

  .card-link {{
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-family: 'Syne', sans-serif;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    color: var(--accent);
    text-decoration: none;
    opacity: 0.8;
    transition: opacity 0.2s;
  }}

  .card-link:hover {{ opacity: 1; }}

  .card-link svg {{ opacity: 0.6; }}

  /* Footer */
  footer {{
    margin-top: 64px;
    padding: 32px 0;
    border-top: 1px solid var(--border);
    text-align: center;
    color: var(--muted);
    font-size: 0.8rem;
    animation: fadeUp 0.6s ease both;
  }}

  footer strong {{ color: var(--accent); }}

  /* Animations */
  @keyframes fadeDown {{
    from {{ opacity: 0; transform: translateY(-20px); }}
    to {{ opacity: 1; transform: translateY(0); }}
  }}

  @keyframes fadeUp {{
    from {{ opacity: 0; transform: translateY(16px); }}
    to {{ opacity: 1; transform: translateY(0); }}
  }}

  @keyframes pulse {{
    0%, 100% {{ opacity: 1; transform: scale(1); }}
    50% {{ opacity: 0.5; transform: scale(0.7); }}
  }}

  .news-card:nth-child(1) {{ animation-delay: 0.05s; }}
  .news-card:nth-child(2) {{ animation-delay: 0.1s; }}
  .news-card:nth-child(3) {{ animation-delay: 0.15s; }}
  .news-card:nth-child(4) {{ animation-delay: 0.2s; }}
  .news-card:nth-child(5) {{ animation-delay: 0.25s; }}
  .news-card:nth-child(6) {{ animation-delay: 0.3s; }}
  .news-card:nth-child(7) {{ animation-delay: 0.35s; }}
  .news-card:nth-child(8) {{ animation-delay: 0.4s; }}

  .hidden {{ display: none; }}
</style>
</head>
<body>
<div class="container">
  <header>
    <div class="header-tag">Automatikus napi összefoglaló</div>
    <h1>Reggeli<br><em>AI Hírek</em></h1>
    <p style="color:var(--muted); font-size:0.9rem; margin-top:8px;">{news_json['date']}</p>
    <div class="summary-box">{news_json['summary']}</div>
  </header>

  <div class="filters">
    <button class="filter-btn active" onclick="filter('mind')">Összes</button>
    <button class="filter-btn" onclick="filter('Magyar')">🇭🇺 Magyar</button>
    <button class="filter-btn" onclick="filter('Nemzetközi')">🌍 Nemzetközi</button>
    <button class="filter-btn" onclick="filter('Szabályozás')">⚖️ Szabályozás</button>
    <button class="filter-btn" onclick="filter('Alkalmazások')">🚀 Alkalmazások</button>
  </div>

  <div class="news-grid" id="grid">
    {news_items_html}
  </div>

  <footer>
    Generálva <strong>Claude AI</strong> által · {news_json['date']} · Minden reggel 6:00-kor frissül
  </footer>
</div>

<script>
function filter(cat) {{
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  event.target.classList.add('active');
  document.querySelectorAll('.news-card').forEach(card => {{
    if (cat === 'mind' || card.dataset.category === cat) {{
      card.classList.remove('hidden');
    }} else {{
      card.classList.add('hidden');
    }}
  }});
}}
</script>
</body>
</html>"""

os.makedirs("docs", exist_ok=True)
with open("docs/index.html", "w", encoding="utf-8") as f:
    f.write(html)

print("✅ Sikeresen generálva: docs/index.html")
print(f"📰 Hírek száma: {len(news_json.get('news', []))}")
