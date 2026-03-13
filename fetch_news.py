import anthropic
import json
import datetime
import os
import re

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
today = datetime.date.today().strftime("%Y. %m. %d.")
now = (datetime.datetime.utcnow() + datetime.timedelta(hours=2)).strftime("%Y. %m. %d. %H:%M:%S (Budapest)")

response = client.messages.create(
    model="claude-haiku-4-5-20251001",
    max_tokens=8000,
    tools=[{"type": "web_search_20250305", "name": "web_search"}],
    messages=[{
        "role": "user",
        "content": f"""Mai dátum: {today}

Végezz pontosan 8 keresést az alábbi témákban, majd gyűjts össze 40-60 friss AI hírt az elmúlt 48 órából:
1. AI news today
2. OpenAI Google Anthropic Meta AI news
3. Microsoft Apple Amazon NVIDIA AI news
4. AI startup funding new model released
5. EU AI regulation policy government
6. AI research science medical breakthrough
7. AI robotics applications business
8. magyar mesterséges intelligencia

Fontos források: TechCrunch, The Verge, Reuters, Bloomberg, Wired, Ars Technica, VentureBeat, openai.com/blog, anthropic.com/news, index.hu, hvg.hu

A válaszod KIZÁRÓLAG egy JSON objektum legyen, semmi más, így:
{{"date":"{today}","summary":"összefoglaló magyarul","news":[{{"title":"cím magyarul","summary":"összefoglaló magyarul","source":"forrás neve","url":"https://...","category":"Nagy cégek"}}]}}

Kategóriák csak ezek lehetnek: Magyar, Nagy cégek, Startupok, Szabályozás, Tudomány, Alkalmazások, Biztonság
NE használj markdown-t, NE írj semmit a JSON elé vagy után!"""
    }]
)

# Debug output
print("=== RESPONSE BLOCKS ===")
for i, block in enumerate(response.content):
    print(f"Block {i}: type={block.type}")
    if block.type == "text":
        print(f"TEXT PREVIEW: {repr(block.text[:600])}")
print("=== END ===")

# Robust JSON extraction
news_json = None
for block in response.content:
    if block.type == "text":
        text = block.text.strip()
        # Strip markdown fences
        text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        text = text.strip()
        # Try direct parse
        try:
            news_json = json.loads(text)
            print(f"OK: {len(news_json.get('news', []))} hir")
            break
        except Exception as e:
            print(f"Direct parse failed: {e}")
        # Try regex extraction
        m = re.search(r'\{[\s\S]*"news"\s*:\s*\[[\s\S]*?\]\s*\}', text)
        if m:
            try:
                news_json = json.loads(m.group())
                print(f"OK regex: {len(news_json.get('news', []))} hir")
                break
            except Exception as e:
                print(f"Regex parse failed: {e}")
                print(f"Snippet: {m.group()[:400]}")

if not news_json:
    print("FALLBACK: JSON not found")
    news_json = {
        "date": today,
        "summary": "A hírek betöltése során hiba történt.",
        "news": []
    }

# Category styles
cat_style = {
    "Magyar":       ("🇭🇺", "#e63946"),
    "Nagy cégek":   ("🏢", "#457b9d"),
    "Startupok":    ("💡", "#f4a261"),
    "Szabályozás":  ("⚖️", "#2d6a4f"),
    "Tudomány":     ("🔬", "#9b2226"),
    "Alkalmazások": ("🚀", "#7b2d8b"),
    "Biztonság":    ("🛡️", "#6c757d"),
    "Nemzetközi":   ("🌍", "#457b9d"),
}

news_items_html = ""
for item in news_json.get("news", []):
    cat = item.get("category", "Nagy cégek")
    icon, color = cat_style.get(cat, ("📰", "#457b9d"))
    news_items_html += f"""
    <article class="news-card" data-category="{cat}">
      <div class="card-accent" style="background:{color}"></div>
      <div class="card-body">
        <span class="category-badge" style="color:{color};border-color:{color}20;background:{color}10">{icon} {cat}</span>
        <h2 class="card-title">{item.get('title','')}</h2>
        <p class="card-summary">{item.get('summary','')}</p>
        <a href="{item.get('url','#')}" class="card-link" target="_blank" rel="noopener">
          <span>{item.get('source','Forrás')}</span>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6"/><polyline points="15,3 21,3 21,9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
        </a>
      </div>
    </article>"""

total = len(news_json.get('news', []))

html = f"""<!DOCTYPE html>
<html lang="hu">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI Hírek – {news_json['date']}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400&display=swap" rel="stylesheet">
<style>
  :root {{
    --bg:#0a0a0f; --surface:#13131a; --border:#1e1e2e;
    --text:#f0f0fa; --muted:#a0a0c0; --accent:#c8ff00;
  }}
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{background:var(--bg);color:var(--text);font-family:'DM Sans',sans-serif;font-weight:300;min-height:100vh;overflow-x:hidden}}
  body::before{{content:'';position:fixed;inset:0;background-image:linear-gradient(rgba(200,255,0,0.03) 1px,transparent 1px),linear-gradient(90deg,rgba(200,255,0,0.03) 1px,transparent 1px);background-size:60px 60px;pointer-events:none;z-index:0}}
  .container{{max-width:900px;margin:0 auto;padding:0 24px;position:relative;z-index:1}}
  header{{padding:60px 0 40px;border-bottom:1px solid var(--border);margin-bottom:48px;animation:fadeDown .6s ease both}}
  .header-tag{{font-family:'Syne',sans-serif;font-size:11px;font-weight:600;letter-spacing:.2em;text-transform:uppercase;color:var(--accent);margin-bottom:16px;display:flex;align-items:center;gap:8px}}
  .header-tag::before{{content:'';display:inline-block;width:6px;height:6px;background:var(--accent);border-radius:50%;animation:pulse 2s ease infinite}}
  h1{{font-family:'Syne',sans-serif;font-size:clamp(2.2rem,5vw,3.4rem);font-weight:800;line-height:1.05;letter-spacing:-.03em;margin-bottom:20px}}
  h1 em{{font-style:normal;color:var(--accent)}}
  .summary-box{{background:var(--surface);border:1px solid var(--border);border-left:3px solid var(--accent);padding:20px 24px;border-radius:0 8px 8px 0;color:#b8b8d8;line-height:1.7;font-size:.95rem;margin-top:24px}}
  .filters{{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:20px;animation:fadeUp .6s .2s ease both}}
  .filter-btn{{background:var(--surface);border:1px solid var(--border);color:var(--muted);padding:8px 18px;border-radius:100px;font-family:'Syne',sans-serif;font-size:.78rem;font-weight:600;letter-spacing:.05em;cursor:pointer;transition:all .2s}}
  .filter-btn:hover,.filter-btn.active{{border-color:var(--accent);color:var(--accent);background:rgba(200,255,0,.05)}}
  .news-count{{font-family:'Syne',sans-serif;font-size:.8rem;color:var(--muted);margin-bottom:24px}}
  .news-count span{{color:var(--accent);font-weight:700}}
  .news-grid{{display:grid;gap:16px}}
  .news-card{{background:var(--surface);border:1px solid var(--border);border-radius:12px;overflow:hidden;display:flex;transition:transform .2s,border-color .2s;animation:fadeUp .5s ease both}}
  .news-card:hover{{transform:translateY(-2px);border-color:#2e2e42}}
  .card-accent{{width:4px;flex-shrink:0;opacity:.8}}
  .card-body{{padding:20px 24px;flex:1}}
  .category-badge{{display:inline-block;font-family:'Syne',sans-serif;font-size:.72rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;padding:3px 10px;border-radius:100px;border:1px solid;margin-bottom:10px}}
  .card-title{{font-family:'Syne',sans-serif;font-size:1.05rem;font-weight:700;line-height:1.3;margin-bottom:10px;color:var(--text)}}
  .card-summary{{font-size:.88rem;line-height:1.65;color:var(--muted);margin-bottom:16px}}
  .card-link{{display:inline-flex;align-items:center;gap:6px;font-family:'Syne',sans-serif;font-size:.78rem;font-weight:600;letter-spacing:.05em;color:var(--accent);text-decoration:none;opacity:.8;transition:opacity .2s}}
  .card-link:hover{{opacity:1}}
  footer{{margin-top:64px;padding:32px 0;border-top:1px solid var(--border);text-align:center;color:var(--muted);font-size:.8rem}}
  footer strong{{color:var(--accent)}}
  @keyframes fadeDown{{from{{opacity:0;transform:translateY(-20px)}}to{{opacity:1;transform:translateY(0)}}}}
  @keyframes fadeUp{{from{{opacity:0;transform:translateY(16px)}}to{{opacity:1;transform:translateY(0)}}}}
  @keyframes pulse{{0%,100%{{opacity:1;transform:scale(1)}}50%{{opacity:.5;transform:scale(.7)}}}}
  .hidden{{display:none}}
</style>
</head>
<body>
<div class="container">
  <header>
    <div class="header-tag">Automatikus napi összefoglaló</div>
    <h1>Reggeli<br><em>AI Hírek</em></h1>
    <p style="color:var(--muted);font-size:.9rem;margin-top:8px">{news_json['date']}</p>
    <div class="summary-box">{news_json['summary']}</div>
  </header>
  <div class="filters">
    <button class="filter-btn active" onclick="filter(this,'mind')">Összes</button>
    <button class="filter-btn" onclick="filter(this,'Magyar')">🇭🇺 Magyar</button>
    <button class="filter-btn" onclick="filter(this,'Nagy cégek')">🏢 Nagy cégek</button>
    <button class="filter-btn" onclick="filter(this,'Startupok')">💡 Startupok</button>
    <button class="filter-btn" onclick="filter(this,'Tudomány')">🔬 Tudomány</button>
    <button class="filter-btn" onclick="filter(this,'Szabályozás')">⚖️ Szabályozás</button>
    <button class="filter-btn" onclick="filter(this,'Alkalmazások')">🚀 Alkalmazások</button>
    <button class="filter-btn" onclick="filter(this,'Biztonság')">🛡️ Biztonság</button>
  </div>
  <p class="news-count">Megjelenített hírek: <span id="count">{total}</span> / {total}</p>
  <div class="news-grid" id="grid">{news_items_html}</div>
  <footer>Generálva <strong>Claude AI</strong> által · Utoljára frissítve: <strong>{now}</strong> · Minden reggel 6:00-kor frissül</footer>
</div>
<script>
function filter(btn,cat){{
  document.querySelectorAll('.filter-btn').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');
  let v=0;
  document.querySelectorAll('.news-card').forEach(card=>{{
    const show=cat==='mind'||card.dataset.category===cat;
    card.classList.toggle('hidden',!show);
    if(show)v++;
  }});
  document.getElementById('count').textContent=v;
}}
</script>
</body>
</html>"""

os.makedirs("docs", exist_ok=True)
with open("docs/index.html", "w", encoding="utf-8") as f:
    f.write(html)

print(f"✅ Kész: docs/index.html")
print(f"📰 Hírek: {total}")
