import anthropic
import json
import datetime
import os
import re
import urllib.request
import xml.etree.ElementTree as ET

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
today = datetime.date.today().strftime("%Y. %m. %d.")
now = (datetime.datetime.utcnow() + datetime.timedelta(hours=2)).strftime("%Y. %m. %d. %H:%M:%S (Budapest)")

# =============================================================
# 1. SOURCES.TXT BEOLVASÁSA (RSS feedek + domainek)
# =============================================================
rss_feeds = []
domains = []

try:
    with open("sources.txt", "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = [p.strip() for p in line.split("|")]
            if len(parts) != 3:
                continue
            typ, name, value = parts
            if typ == "rss":
                rss_feeds.append((name, value))
            elif typ in ("domain", "url"):
                domains.append((name, value))
    print(f"sources.txt: {len(rss_feeds)} RSS feed, {len(domains)} domain betöltve")
except Exception as e:
    print(f"sources.txt hiba: {e} - alapértelmezett feedek használata")
    rss_feeds = [
        ("The Verge AI", "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml"),
        ("TechCrunch AI", "https://techcrunch.com/category/artificial-intelligence/feed/"),
        ("Google News AI", "https://news.google.com/rss/search?q=artificial+intelligence+news&hl=en&gl=US&ceid=US:en"),
    ]

# =============================================================
# 2. HISTORY.TXT BEOLVASÁSA (utolsó futás dátuma)
# =============================================================
last_run = None
try:
    with open("history.txt", "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("UTOLSO_FUTES:"):
                last_run = line.replace("UTOLSO_FUTES:", "").strip()
                break
    if last_run:
        print(f"Utolsó futás: {last_run}")
except:
    print("history.txt nem található - első futás")

if last_run:
    date_filter = f"FONTOS: Csak {last_run} UTÁN megjelent híreket hozz! Régebbi híreket NE szerepeltess!"
else:
    date_filter = "Csak az elmúlt 7 napban megjelent híreket hozz!"

since_text = last_run if last_run else "az elmúlt 7 napban"

# =============================================================
# 3. RSS GYŰJTÉS
# =============================================================
rss_headlines = []
rss_stats = []

for name, url in rss_feeds:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            tree = ET.parse(resp)
            root = tree.getroot()
            items = root.findall(".//item") or root.findall(".//{http://www.w3.org/2005/Atom}entry")
            count = 0
            for item in items[:8]:
                title_el = item.find("title") or item.find("{http://www.w3.org/2005/Atom}title")
                link_el = item.find("link") or item.find("{http://www.w3.org/2005/Atom}link")
                title = title_el.text.strip() if title_el is not None and title_el.text else ""
                link = link_el.text.strip() if link_el is not None and link_el.text else (link_el.get("href", "") if link_el is not None else "")
                if title and link:
                    rss_headlines.append(f"- {title} | {link} [{name}]")
                    count += 1
        print(f"RSS OK: {name} ({count} cikk)")
        rss_stats.append(f"  {name:<35} OK      {count} cikk")
    except Exception as e:
        short_err = str(e)[:50]
        print(f"RSS hiba: {name} - {short_err}")
        rss_stats.append(f"  {name:<35} HIBA    {short_err}")

rss_context = "\n".join(rss_headlines[:80])
domain_list = ", ".join([v for _, v in domains])
print(f"\nÖsszes RSS cím: {len(rss_headlines)}")

# =============================================================
# 4. CLAUDE API HÍVÁS
# =============================================================
response = client.messages.create(
    model="claude-haiku-4-5-20251001",
    max_tokens=16000,
    tools=[{"type": "web_search_20250305", "name": "web_search"}],
    messages=[{
        "role": "user",
        "content": f"""Mai dátum: {today}

Te egy AI hírigazgató vagy. Feladatod: friss AI híreket keresni és azokról SAJÁT SZAVAKKAL magyar összefoglalókat írni.

{date_filter}

Friss RSS címek kiindulópontként:
{rss_context}

Végezz 5 webes keresést:
1. AI news {today}
2. OpenAI Anthropic Claude news this week
3. Google Gemini DeepMind news this week
4. AI startup new model released this week
5. magyar mesterseges intelligencia hirek

Extra keresendő oldalak: {domain_list}

Gyűjts 15-20 EGYEDI hírt amelyek {since_text} jelentek meg. Régebbi vagy ismétlődő híreket NE szerepeltess. Minden hírről írj SAJÁT SZAVAKKAL magyar összefoglalót.

Válaszolj KIZÁRÓLAG valid JSON-nal, semmi mással:
{{"date":"{today}","summary":"3-4 mondatos napi összefoglaló magyarul","news":[{{"title":"hír címe magyarul","summary":"2-3 mondatos összefoglaló saját szavakkal","details":"2-3 mondatos kifejtés: számok, nevek, összefüggések","relevance":"1 mondat: miért érdekes egy átlagolvasónak","source":"pl. TechCrunch","url":"https://...","category":"Nagy cégek"}}]}}

Kategóriák: Magyar, Nagy cégek, Startupok, Szabályozás, Tudomány, Alkalmazások, Biztonság
CSAK JSON-t írj, semmit előtte vagy utána!"""
    }]
)

# Debug
print("=== RESPONSE BLOCKS ===")
for i, block in enumerate(response.content):
    print(f"Block {i}: type={block.type}")
    if block.type == "text":
        print(f"TEXT PREVIEW: {repr(block.text[:400])}")
print("=== END ===")

# JSON extraction
news_json = None
for block in response.content:
    if block.type == "text":
        text = block.text.strip()
        text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        text = text.strip()
        try:
            news_json = json.loads(text)
            print(f"OK direct: {len(news_json.get('news', []))} hír")
            break
        except Exception as e:
            print(f"Direct parse failed: {e}")
        m = re.search(r'\{[\s\S]*"news"\s*:\s*\[[\s\S]*?\]\s*\}', text)
        if m:
            try:
                news_json = json.loads(m.group())
                print(f"OK regex: {len(news_json.get('news', []))} hír")
                break
            except Exception as e:
                print(f"Regex failed: {e}")

if not news_json:
    print("FALLBACK")
    news_json = {"date": today, "summary": "A hírek betöltése során hiba történt.", "news": []}

# =============================================================
# 5. HISTORY.TXT FRISSÍTÉSE
# =============================================================
try:
    # Meglévő history beolvasása
    history_lines = []
    try:
        with open("history.txt", "r", encoding="utf-8") as f:
            history_lines = f.readlines()
    except:
        pass

    # Régi UTOLSO_FUTES sor törlése
    history_lines = [l for l in history_lines if not l.startswith("UTOLSO_FUTES:")]

    # Új bejegyzés összeállítása
    new_entry = [
        f"\n--- FUTÁS: {now} ---\n",
        f"Hírek: {len(news_json.get('news', []))} db | RSS címek: {len(rss_headlines)} db\n",
    ] + [f"{s}\n" for s in rss_stats]

    # Régi bejegyzések megtartása (max 7)
    existing_entries = "".join(history_lines)
    runs = re.split(r'\n--- FUTÁS:', existing_entries)
    runs = [r for r in runs if r.strip()]
    runs = runs[-9:] if len(runs) >= 9 else runs  # max 9 régi + 1 új = 10

    # Visszaírás
    with open("history.txt", "w", encoding="utf-8") as f:
        f.write(f"UTOLSO_FUTES: {today}\n")
        f.write(f"# AI Hírek - Futási előzmények (utolsó 7 futás)\n")
        f.write(f"# Formátum: Forrás neve | OK/HIBA | cikk száma\n")
        f.write(f"# {'='*55}\n")
        for r in runs:
            f.write(f"\n--- FUTÁS:{r}")
        f.writelines(new_entry)

    print(f"history.txt frissítve ({len(runs)+1} bejegyzés)")
except Exception as e:
    print(f"history.txt írási hiba: {e}")

# =============================================================
# 6. HTML GENERÁLÁS
# =============================================================
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
    details_html = f'<div class="card-details">{item.get("details","")}</div>' if item.get("details") else ""
    relevance_html = f'<div class="card-relevance"><span class="relevance-label">💡 Miért érdekes?</span> {item.get("relevance","")}</div>' if item.get("relevance") else ""
    news_items_html += f"""
    <article class="news-card" data-category="{cat}">
      <div class="card-accent" style="background:{color}"></div>
      <div class="card-body">
        <span class="category-badge" style="color:{color};border-color:{color}20;background:{color}10">{icon} {cat}</span>
        <h2 class="card-title">{item.get('title','')}</h2>
        <p class="card-summary">{item.get('summary','')}</p>
        {details_html}
        {relevance_html}
        <a href="{item.get('url','#')}" class="card-link" target="_blank" rel="noopener nofollow">
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
  :root {{--bg:#0a0a0f;--surface:#13131a;--border:#1e1e2e;--text:#f0f0fa;--muted:#c8c8e0;--accent:#c8ff00}}
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{background:var(--bg);color:var(--text);font-family:'DM Sans',sans-serif;font-weight:300;min-height:100vh;overflow-x:hidden}}
  body::before{{content:'';position:fixed;inset:0;background-image:linear-gradient(rgba(200,255,0,0.03) 1px,transparent 1px),linear-gradient(90deg,rgba(200,255,0,0.03) 1px,transparent 1px);background-size:60px 60px;pointer-events:none;z-index:0}}
  .container{{max-width:960px;margin:0 auto;padding:0 24px;position:relative;z-index:1}}
  header{{padding:60px 0 40px;border-bottom:1px solid var(--border);margin-bottom:48px;animation:fadeDown .6s ease both}}
  .header-tag{{font-family:'Syne',sans-serif;font-size:11px;font-weight:600;letter-spacing:.2em;text-transform:uppercase;color:var(--accent);margin-bottom:16px;display:flex;align-items:center;gap:8px}}
  .header-tag::before{{content:'';display:inline-block;width:6px;height:6px;background:var(--accent);border-radius:50%;animation:pulse 2s ease infinite}}
  h1{{font-family:'Syne',sans-serif;font-size:clamp(2.2rem,5vw,3.4rem);font-weight:800;line-height:1.05;letter-spacing:-.03em;margin-bottom:8px}}
  h1 em{{font-style:normal;color:var(--accent)}}
  .timestamp{{color:var(--muted);font-size:.85rem;margin-top:6px}}
  .summary-box{{background:var(--surface);border:1px solid var(--border);border-left:3px solid var(--accent);padding:20px 24px;border-radius:0 8px 8px 0;color:#d0d0e8;line-height:1.7;font-size:.95rem;margin-top:24px}}
  .filters{{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:20px;animation:fadeUp .6s .2s ease both}}
  .filter-btn{{background:var(--surface);border:1px solid var(--border);color:var(--muted);padding:8px 18px;border-radius:100px;font-family:'Syne',sans-serif;font-size:.78rem;font-weight:600;letter-spacing:.05em;cursor:pointer;transition:all .2s}}
  .filter-btn:hover,.filter-btn.active{{border-color:var(--accent);color:var(--accent);background:rgba(200,255,0,.05)}}
  .news-count{{font-family:'Syne',sans-serif;font-size:.8rem;color:var(--muted);margin-bottom:24px}}
  .news-count span{{color:var(--accent);font-weight:700}}
  .news-grid{{display:grid;gap:20px}}
  .news-card{{background:var(--surface);border:1px solid var(--border);border-radius:12px;overflow:hidden;display:flex;transition:transform .2s,border-color .2s;animation:fadeUp .5s ease both}}
  .news-card:hover{{transform:translateY(-2px);border-color:#2e2e42}}
  .card-accent{{width:4px;flex-shrink:0;opacity:.8}}
  .card-body{{padding:22px 26px;flex:1}}
  .category-badge{{display:inline-block;font-family:'Syne',sans-serif;font-size:.72rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;padding:3px 10px;border-radius:100px;border:1px solid;margin-bottom:12px}}
  .card-title{{font-family:'Syne',sans-serif;font-size:1.15rem;font-weight:700;line-height:1.35;margin-bottom:10px;color:var(--text)}}
  .card-summary{{font-size:.95rem;line-height:1.7;color:var(--muted);margin-bottom:12px}}
  .card-details{{font-size:.9rem;line-height:1.75;color:#b8b8d8;margin-bottom:12px;padding:12px 16px;background:rgba(255,255,255,0.03);border-radius:8px;border-left:2px solid rgba(200,255,0,0.2)}}
  .card-relevance{{font-size:.85rem;line-height:1.6;color:#a0c8a0;margin-bottom:14px;padding:8px 12px;background:rgba(200,255,0,0.04);border-radius:6px}}
  .relevance-label{{font-family:'Syne',sans-serif;font-weight:700;font-size:.75rem;margin-right:4px}}
  .card-link{{display:inline-flex;align-items:center;gap:6px;font-family:'Syne',sans-serif;font-size:.78rem;font-weight:600;letter-spacing:.05em;color:var(--accent);text-decoration:none;opacity:.8;transition:opacity .2s}}
  .card-link:hover{{opacity:1}}
  footer{{margin-top:64px;padding:32px 0;border-top:1px solid var(--border);text-align:center;color:var(--muted);font-size:.8rem}}
  footer p{{margin-bottom:10px}}
  footer strong{{color:var(--accent)}}
  .legal{{margin-top:20px;padding:16px 20px;background:rgba(255,255,255,0.03);border:1px solid var(--border);border-radius:8px;font-size:.75rem;line-height:1.6;color:#888;text-align:left;max-width:800px;margin-left:auto;margin-right:auto}}
  .legal strong{{color:#aaa}}
  @keyframes fadeDown{{from{{opacity:0;transform:translateY(-20px)}}to{{opacity:1;transform:translateY(0)}}}}
  @keyframes fadeUp{{from{{opacity:0;transform:translateY(16px)}}to{{opacity:1;transform:translateY(0)}}}}
  @keyframes pulse{{0%,100%{{opacity:1;transform:scale(1)}}50%{{opacity:.5;transform:scale(.7)}}}}
  .hidden{{display:none}}
</style>
</head>
<body>
<div class="container">
  <header>
    <div class="header-tag">Automatikus összefoglaló</div>
    <h1>Reggeli<br><em>AI Hírek</em></h1>
    <p class="timestamp">Utoljára frissítve: <strong style="color:var(--accent)">{now}</strong></p>
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
  <footer>
    <p>Generálva <strong>Claude AI</strong> által · Utoljára frissítve: <strong>{now}</strong></p>
    <div class="legal">
      <p><strong>Jogi nyilatkozat:</strong> Ez az oldal nyilvánosan elérhető AI-vonatkozású hírek automatikusan generált, saját szavakkal írt összefoglalóit tartalmazza tájékoztatási céllal. Az összefoglalók mesterséges intelligencia által készített, önálló átfogalmazások – nem az eredeti cikkek másolatai vagy reprodukciói. Minden hírhez feltüntetésre kerül az eredeti forrás és annak közvetlen hivatkozása. A hivatkozott cikkek szerzői jogai kizárólag az eredeti szerzőket és kiadókat illetik. Amennyiben tartalomeltávolítási kérelme van, kérjük jelezze és haladéktalanul intézkedünk.</p>
      <p><strong>Legal notice:</strong> This site publishes AI-generated summaries of publicly available news articles for informational purposes. All summaries are independently rewritten by an AI model and do not reproduce the original articles. Each item credits and links to the original source. All copyrights remain with the respective authors and publishers. This service operates under fair use principles of commentary and news aggregation. If you are a rights holder and wish to request removal of a summary, please contact us and we will act promptly.</p>
    </div>
  </footer>
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
