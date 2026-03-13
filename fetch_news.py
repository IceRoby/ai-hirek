# ================================================================
# AI HÍREK - FŐ SCRIPT (fetch_news.py)
# ================================================================
# NORMÁL ESETBEN NEM KELL MÓDOSÍTANI EZT A FÁJLT!
# Minden beállítás a config.txt-ben és sources.txt-ben van.
# ================================================================

import anthropic
import json
import datetime
import os
import re
import urllib.request
import xml.etree.ElementTree as ET


# ================================================================
# TÉMÁK ADATBÁZISA
# ================================================================
# Ha a config.txt-ben beírsz egy témát, innen veszi ki automatikusan
# a keresési kifejezéseket, oldal címét, és Google News URL-eket.
#
# ÚJ TÉMA HOZZÁADÁSÁHOZ:
# Másold le egy meglévő blokkot és írd felül az értékeket.
# A kulcs legyen rövid, ékezet nélküli (pl. "fitness", "crypto")

TEMAK_DB = {

    "ai": {
        "cim":    "Reggeli AI Hírek",
        "alcim":  "Automatikus AI összefoglaló",
        "labléc": "Minden héten frissül automatikusan",
        "kereses": [
            "OpenAI Anthropic Claude news",
            "Google Gemini DeepMind news",
            "AI startup new model released",
            "EU AI regulation policy",
            "AI research science breakthrough",
            "magyar mesterseges intelligencia hirek",
        ],
        "google_news": [
            ("Google News AI EN",     "artificial+intelligence+news"),
            ("Google News OpenAI",    "OpenAI+ChatGPT"),
            ("Google News Anthropic", "Anthropic+Claude"),
            ("Google News Google AI", "Google+Gemini+DeepMind"),
            ("Google News Meta AI",   "Meta+AI+Llama"),
            ("Google News Magyar AI", "mesterseges+intelligencia"),
        ],
        "kategoriak": ["Magyar", "Nagy cégek", "Startupok", "Szabályozás",
                       "Tudomány", "Alkalmazások", "Biztonság"],
    },

    "coaching": {
        "cim":    "Heti Coaching Hírek",
        "alcim":  "Coaching és személyes fejlődés összefoglaló",
        "labléc": "Minden héten frissül automatikusan",
        "kereses": [
            "coaching leadership news this week",
            "executive coaching trends 2026",
            "personal development life coaching",
            "leadership skills management news",
            "mindfulness wellbeing workplace",
            "magyar coaching vezetes fejlodes hirek",
        ],
        "google_news": [
            ("Google News Coaching EN",  "coaching+leadership+news"),
            ("Google News Leadership",   "executive+leadership+development"),
            ("Google News Mindset",      "personal+development+growth+mindset"),
            ("Google News Management",   "management+workplace+trends"),
            ("Google News Magyar",       "coaching+vezetes+fejlodes"),
        ],
        "kategoriak": ["Magyar", "Leadership", "Személyes fejlődés",
                       "Workplace", "Eszközök", "Kutatás", "Inspiráció"],
    },

    "marketing": {
        "cim":    "Heti Marketing Hírek",
        "alcim":  "Digitális marketing összefoglaló",
        "labléc": "Minden héten frissül automatikusan",
        "kereses": [
            "digital marketing news this week",
            "SEO algorithm update Google",
            "social media marketing trends",
            "content marketing strategy 2026",
            "email marketing automation news",
            "magyar digitalis marketing hirek",
        ],
        "google_news": [
            ("Google News Marketing",    "digital+marketing+news"),
            ("Google News SEO",          "SEO+Google+algorithm+update"),
            ("Google News Social Media", "social+media+marketing+trends"),
            ("Google News Content",      "content+marketing+strategy"),
            ("Google News Magyar",       "marketing+seo+kozossegi+media"),
        ],
        "kategoriak": ["Magyar", "SEO", "Social Media", "Content",
                       "Email", "Analytics", "Eszközök"],
    },

    "egeszseg": {
        "cim":    "Heti Egészség Hírek",
        "alcim":  "Egészség és wellness összefoglaló",
        "labléc": "Minden héten frissül automatikusan",
        "kereses": [
            "health wellness news this week",
            "medical research breakthrough 2026",
            "nutrition diet science news",
            "mental health psychology news",
            "fitness exercise health trends",
            "magyar egeszseg orvostudomany hirek",
        ],
        "google_news": [
            ("Google News Health EN",  "health+wellness+news"),
            ("Google News Medical",    "medical+research+breakthrough"),
            ("Google News Nutrition",  "nutrition+diet+science"),
            ("Google News Mental",     "mental+health+psychology"),
            ("Google News Magyar",     "egeszseg+orvostudomany+wellness"),
        ],
        "kategoriak": ["Magyar", "Orvostudomány", "Táplálkozás",
                       "Mentális egészség", "Fitness", "Kutatás", "Megelőzés"],
    },

    "penzugy": {
        "cim":    "Heti Pénzügyi Hírek",
        "alcim":  "Pénzügy és befektetés összefoglaló",
        "labléc": "Minden héten frissül automatikusan",
        "kereses": [
            "finance investment news this week",
            "stock market economy news",
            "cryptocurrency bitcoin news",
            "personal finance savings tips",
            "startup funding venture capital",
            "magyar penzugy gazdasag befektetes hirek",
        ],
        "google_news": [
            ("Google News Finance",  "finance+investment+news"),
            ("Google News Markets",  "stock+market+economy"),
            ("Google News Crypto",   "cryptocurrency+bitcoin+news"),
            ("Google News Startup",  "startup+funding+venture+capital"),
            ("Google News Magyar",   "penzugy+gazdasag+befektetes"),
        ],
        "kategoriak": ["Magyar", "Befektetés", "Gazdaság", "Kripto",
                       "Személyes pénzügy", "Startupok", "Szabályozás"],
    },

    "ingatlan": {
        "cim":    "Heti Ingatlan Hírek",
        "alcim":  "Ingatlanpiac összefoglaló",
        "labléc": "Minden héten frissül automatikusan",
        "kereses": [
            "real estate market news this week",
            "housing market trends 2026",
            "property investment news",
            "commercial real estate news",
            "mortgage interest rates news",
            "magyar ingatlanpiac lakasarak hirek",
        ],
        "google_news": [
            ("Google News Real Estate", "real+estate+market+news"),
            ("Google News Housing",     "housing+market+trends"),
            ("Google News Property",    "property+investment+news"),
            ("Google News Mortgage",    "mortgage+interest+rates"),
            ("Google News Magyar",      "ingatlan+lakaspiac+befektetes"),
        ],
        "kategoriak": ["Magyar", "Lakáspiac", "Befektetés", "Kereskedelmi",
                       "Jelzálog", "Fejlesztés", "Szabályozás"],
    },

    "tech": {
        "cim":    "Heti Tech Hírek",
        "alcim":  "Technológiai összefoglaló",
        "labléc": "Minden héten frissül automatikusan",
        "kereses": [
            "technology news this week",
            "Apple Google Microsoft news",
            "startup tech funding news",
            "cybersecurity data breach news",
            "gadget product launch 2026",
            "magyar technologia it hirek",
        ],
        "google_news": [
            ("Google News Tech EN",  "technology+news"),
            ("Google News BigTech",  "Apple+Google+Microsoft+news"),
            ("Google News Security", "cybersecurity+data+breach"),
            ("Google News Gadgets",  "gadget+product+launch+tech"),
            ("Google News Magyar",   "technologia+informatika+hirek"),
        ],
        "kategoriak": ["Magyar", "Nagy cégek", "Startupok", "Biztonság",
                       "Termékek", "Kutatás", "Szabályozás"],
    },

    "uzlet": {
        "cim":    "Heti Üzleti Hírek",
        "alcim":  "Üzleti világ összefoglaló",
        "labléc": "Minden héten frissül automatikusan",
        "kereses": [
            "business news this week",
            "entrepreneurship startup news",
            "corporate strategy management news",
            "ecommerce retail business trends",
            "remote work future of work news",
            "magyar uzlet vallalkozas hirek",
        ],
        "google_news": [
            ("Google News Business",  "business+news"),
            ("Google News Startup",   "entrepreneurship+startup+news"),
            ("Google News Corporate", "corporate+strategy+management"),
            ("Google News Ecommerce", "ecommerce+retail+trends"),
            ("Google News Magyar",    "uzlet+vallalkozas+gazdasag"),
        ],
        "kategoriak": ["Magyar", "Vállalati", "Startupok", "E-commerce",
                       "Vezetés", "Trendek", "Szabályozás"],
    },

    "sport": {
        "cim":    "Heti Sport Hírek",
        "alcim":  "Sportviiág összefoglaló",
        "labléc": "Minden héten frissül automatikusan",
        "kereses": [
            "sports news this week",
            "football soccer news",
            "NBA NFL sports results",
            "athlete transfer news",
            "sports technology fitness news",
            "magyar sport foci hirek",
        ],
        "google_news": [
            ("Google News Sports",   "sports+news"),
            ("Google News Football", "football+soccer+news"),
            ("Google News NBA NFL",  "NBA+NFL+sports"),
            ("Google News Transfer", "athlete+transfer+signing"),
            ("Google News Magyar",   "magyar+sport+foci+eredmenyek"),
        ],
        "kategoriak": ["Magyar", "Labdarúgás", "Kosárlabda", "Egyéb sport",
                       "Átigazolás", "Technológia", "Eredmények"],
    },

    "jog": {
        "cim":    "Heti Jogi Hírek",
        "alcim":  "Jogi és szabályozási összefoglaló",
        "labléc": "Minden héten frissül automatikusan",
        "kereses": [
            "law legal news this week",
            "EU regulation legislation news",
            "supreme court ruling news",
            "data privacy GDPR news",
            "intellectual property copyright news",
            "magyar jog szabalyozas hirek",
        ],
        "google_news": [
            ("Google News Law",      "law+legal+news"),
            ("Google News EU Law",   "EU+regulation+legislation"),
            ("Google News Privacy",  "data+privacy+GDPR+news"),
            ("Google News IP",       "intellectual+property+copyright"),
            ("Google News Magyar",   "jog+szabalyozas+torveny"),
        ],
        "kategoriak": ["Magyar", "EU szabályozás", "Adatvédelem",
                       "Szellemi tulajdon", "Büntetőjog", "Üzleti jog", "Döntések"],
    },
}

# Ha a téma nem szerepel az adatbázisban, ezt használja
TEMA_ALAPERTELMEZETT = {
    "cim":    "Heti Hírek",
    "alcim":  "Automatikus összefoglaló",
    "labléc": "Minden héten frissül automatikusan",
    # A keresési kifejezéseket a téma nevéből generálja
    "kereses": [],
    "google_news": [],
    "kategoriak": ["Magyar", "Nemzetközi", "Kutatás", "Trendek",
                   "Eszközök", "Vélemény", "Egyéb"],
}


# ================================================================
# 1. CONFIG.TXT BEOLVASÁSA
# ================================================================

def load_config(filename):
    cfg = {}
    try:
        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = [p.strip() for p in line.split("|")]
                if len(parts) == 3 and parts[0] == "config":
                    cfg[parts[1]] = parts[2]
        print(f"{filename}: {len(cfg)} beállítás betöltve")
    except Exception as e:
        print(f"{filename} hiba: {e} - alapértelmezett értékek")
    return cfg

cfg = load_config("config.txt")

# Alap beállítások
MODELL       = cfg.get("modell", "claude-haiku-4-5-20251001")
HIREK_SZAMA  = cfg.get("hirek_szama", "25-35")
IDOABLAK_NAP = cfg.get("idoablak_nap", "7")
NYELV        = cfg.get("nyelv", "magyar")

# Téma kiválasztása és adatok betöltése
TEMA_KULCS = cfg.get("tema", "ai").lower().strip()
tema_adat  = TEMAK_DB.get(TEMA_KULCS, TEMA_ALAPERTELMEZETT)

print(f"Téma: {TEMA_KULCS}")

# Oldal szövegek: config.txt felülírhatja a témából jövőket
OLDAL_CIM   = cfg.get("oldal_cim",   tema_adat["cim"])
OLDAL_ALCIM = cfg.get("oldal_alcim", tema_adat["alcim"])
LABLÉC      = cfg.get("labléc_szoveg", tema_adat["labléc"])

# --- Téma kulcsszavak (config.txt 1b szekció) ---
# Ezek pontosítják a keresést - bekerülnek a keresési kifejezések közé
TEMA_KULCSSZAVAK = []
if cfg.get("tema_kulcsszavak"):
    TEMA_KULCSSZAVAK = [k.strip() for k in cfg["tema_kulcsszavak"].split(",") if k.strip()]
    print(f"Téma kulcsszavak: {', '.join(TEMA_KULCSSZAVAK)}")

# --- Kizárt kulcsszavak (config.txt 1c szekció) ---
KIZART_KULCSSZAVAK = []
if cfg.get("kizart_kulcsszavak"):
    KIZART_KULCSSZAVAK = [k.strip() for k in cfg["kizart_kulcsszavak"].split(",") if k.strip()]
    print(f"Kizárt kulcsszavak: {', '.join(KIZART_KULCSSZAVAK)}")

# --- Fókusz régiók (config.txt 1d szekció) ---
FOKUSZ_REGIOK = cfg.get("fokusz_regiok", "globális, magyar")

# --- Keresési kifejezések összeállítása ---
if cfg.get("kereses_feluliras"):
    # 1. Kézi felülírás a config.txt-ből (1e szekció)
    KERESES_LISTA = [t.strip() for t in cfg["kereses_feluliras"].split(",") if t.strip()]
    print(f"Keresési témák: manuálisan megadva ({len(KERESES_LISTA)} db)")
elif tema_adat["kereses"]:
    # 2. Automatikus a témából + kulcsszavak hozzáadása
    KERESES_LISTA = tema_adat["kereses"].copy()
    # Ha vannak kulcsszavak, egy extra keresést generálunk belőlük
    if TEMA_KULCSSZAVAK:
        kulcsszavak_str = " ".join(TEMA_KULCSSZAVAK[:4])  # max 4 szó
        KERESES_LISTA.append(f"{kulcsszavak_str} news this week")
    print(f"Keresési témák: automatikus + kulcsszavak ({len(KERESES_LISTA)} db)")
else:
    # 3. Ismeretlen téma: generálás a kulcsszóból + kulcsszavakból
    KERESES_LISTA = [
        f"{TEMA_KULCS} news this week",
        f"{TEMA_KULCS} trends 2026",
        f"latest {TEMA_KULCS} developments",
        f"magyar {TEMA_KULCS} hirek",
    ]
    if TEMA_KULCSSZAVAK:
        kulcsszavak_str = " ".join(TEMA_KULCSSZAVAK[:3])
        KERESES_LISTA.append(f"{kulcsszavak_str} news")
    print(f"Keresési témák: generált ({len(KERESES_LISTA)} db)")

# Kategóriák a témából
KATEGORIAK = tema_adat.get("kategoriak",
    ["Magyar", "Nemzetközi", "Kutatás", "Trendek", "Eszközök", "Egyéb"])

# Kizárási szöveg a prompthoz (ha van kizárt kulcsszó)
if KIZART_KULCSSZAVAK:
    KIZARASI_UTASITAS = f"KIZÁRT TÉMÁK: Az alábbi kulcsszavakkal kapcsolatos híreket NE vedd fel: {', '.join(KIZART_KULCSSZAVAK)}"
else:
    KIZARASI_UTASITAS = ""

print(f"Modell: {MODELL} | Hírek: {HIREK_SZAMA} | Nyelv: {NYELV} | Régiók: {FOKUSZ_REGIOK}")


# ================================================================
# 2. SOURCES.TXT BEOLVASÁSA
# ================================================================

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
    print(f"sources.txt: {len(rss_feeds)} RSS feed, {len(domains)} domain")
except Exception as e:
    print(f"sources.txt hiba: {e}")
    rss_feeds = []

# Google News feedek automatikus hozzáadása a témából
# (csak azokat adja hozzá amiket a sources.txt NEM tartalmaz még)
if tema_adat.get("google_news"):
    meglevo_nevek = {n for n, _ in rss_feeds}
    for nev, kulcsszo in tema_adat["google_news"]:
        if nev not in meglevo_nevek:
            url = (f"https://news.google.com/rss/search?"
                   f"q={kulcsszo}&hl=en&gl=US&ceid=US:en")
            rss_feeds.append((nev, url))
    print(f"Google News feedek hozzáadva a témából: {len(tema_adat['google_news'])} db")


# ================================================================
# 3. HISTORY.TXT BEOLVASÁSA
# ================================================================

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
    print(f"history.txt nem található - az elmúlt {IDOABLAK_NAP} nap")

if last_run:
    date_filter = f"FONTOS: Csak {last_run} UTÁN megjelent híreket hozz!"
    since_text = last_run
else:
    date_filter = f"Csak az elmúlt {IDOABLAK_NAP} napban megjelent híreket hozz!"
    since_text = f"az elmúlt {IDOABLAK_NAP} napban"


# ================================================================
# 4. DÁTUM ÉS IDŐ
# ================================================================

today = datetime.date.today().strftime("%Y. %m. %d.")
now = (datetime.datetime.utcnow() + datetime.timedelta(hours=2)).strftime(
    "%Y. %m. %d. %H:%M:%S (Budapest)")


# ================================================================
# 5. RSS FEEDEK LETÖLTÉSE
# ================================================================

rss_headlines = []
rss_stats = []

for name, url in rss_feeds:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            tree = ET.parse(resp)
            root = tree.getroot()
            items = (root.findall(".//item") or
                    root.findall(".//{http://www.w3.org/2005/Atom}entry"))
            count = 0
            for item in items[:8]:
                title_el = (item.find("title") or
                           item.find("{http://www.w3.org/2005/Atom}title"))
                link_el = (item.find("link") or
                          item.find("{http://www.w3.org/2005/Atom}link"))
                title = (title_el.text.strip()
                        if title_el is not None and title_el.text else "")
                link = (link_el.text.strip()
                       if link_el is not None and link_el.text
                       else (link_el.get("href", "")
                            if link_el is not None else ""))
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
print(f"Összes RSS cím: {len(rss_headlines)} db")


# ================================================================
# 6. NYELVI BEÁLLÍTÁSOK ÉS JSON SABLON
# ================================================================

kategoriak_str = ", ".join(KATEGORIAK)

if NYELV == "angol":
    nyelv_utasitas = "Write all summaries in English."
    json_sema = (
        f'{{"date":"{today}",'
        f'"summary":"3-4 sentence summary",'
        f'"news":[{{"title":"title","summary":"2-3 sentences",'
        f'"details":"2-3 sentence details",'
        f'"relevance":"1 sentence why interesting",'
        f'"source":"Source name","url":"https://...",'
        f'"category":"category"}}]}}'
    )
elif NYELV == "magyar+angol":
    nyelv_utasitas = "Write in BOTH Hungarian and English (summary + summary_en, details + details_en)."
    json_sema = (
        f'{{"date":"{today}",'
        f'"summary":"összefoglaló magyarul","summary_en":"summary in English",'
        f'"news":[{{"title":"cím magyarul","summary":"magyarul",'
        f'"summary_en":"in English","details":"magyarul",'
        f'"details_en":"in English","relevance":"1 mondat",'
        f'"source":"Forrás","url":"https://...","category":"kategória"}}]}}'
    )
else:  # magyar
    nyelv_utasitas = "Minden összefoglalót MAGYARUL írj, saját szavakkal."
    json_sema = (
        f'{{"date":"{today}",'
        f'"summary":"3-4 mondatos összefoglaló magyarul",'
        f'"news":[{{"title":"hír címe magyarul",'
        f'"summary":"2-3 mondatos összefoglaló",'
        f'"details":"2-3 mondatos kifejtés: számok, nevek",'
        f'"relevance":"1 mondat: miért érdekes",'
        f'"source":"Forrás neve","url":"https://...",'
        f'"category":"kategória"}}]}}'
    )

temak_lista = "\n".join([f"{i+1}. {t}" for i, t in enumerate(KERESES_LISTA)])


# ================================================================
# 7. CLAUDE API HÍVÁS
# ================================================================

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
print(f"\nClaude API hívás... (modell: {MODELL})")

response = client.messages.create(
    model=MODELL,
    max_tokens=16000,
    tools=[{"type": "web_search_20250305", "name": "web_search"}],
    messages=[{
        "role": "user",
        "content": f"""Mai dátum: {today}

Te egy {OLDAL_CIM} szerkesztője vagy. {nyelv_utasitas}

{date_filter}
{KIZARASI_UTASITAS}

FÓKUSZ RÉGIÓK: Elsősorban {FOKUSZ_REGIOK} híreket keress.
{"EXTRA KULCSSZAVAK amelyekre különösen figyelj: " + ", ".join(TEMA_KULCSSZAVAK) if TEMA_KULCSSZAVAK else ""}

Friss RSS hírcímek kiindulópontként:
{rss_context}

Végezz webes keresést ezekre a témákra:
{temak_lista}

Extra keresendő oldalak: {domain_list}

Gyűjts {HIREK_SZAMA} EGYEDI hírt amelyek {since_text} jelentek meg.
Régebbi vagy ismétlődő híreket NE szerepeltess.

Kategóriák amiket használhatsz: {kategoriak_str}

Válaszolj KIZÁRÓLAG valid JSON-nal, semmi mással:
{json_sema}

CSAK JSON-t írj, semmit előtte vagy utána!"""
    }]
)


# ================================================================
# 8. VÁLASZ FELDOLGOZÁSA
# ================================================================

print("=== RESPONSE BLOCKS ===")
for i, block in enumerate(response.content):
    print(f"Block {i}: type={block.type}")
    if block.type == "text":
        print(f"TEXT PREVIEW: {repr(block.text[:400])}")
print("=== END ===")

news_json = None
for block in response.content:
    if block.type == "text":
        text = block.text.strip()
        text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        text = text.strip()
        try:
            news_json = json.loads(text)
            print(f"OK (közvetlen): {len(news_json.get('news', []))} hír")
            break
        except Exception as e:
            print(f"Közvetlen parse sikertelen: {e}")
        m = re.search(r'\{[\s\S]*"news"\s*:\s*\[[\s\S]*?\]\s*\}', text)
        if m:
            try:
                news_json = json.loads(m.group())
                print(f"OK (regex): {len(news_json.get('news', []))} hír")
                break
            except Exception as e:
                print(f"Regex parse sikertelen: {e}")

if not news_json:
    print("FALLBACK: JSON parse sikertelen")
    news_json = {
        "date": today,
        "summary": "A hírek betöltése során hiba történt.",
        "news": []
    }


# ================================================================
# 9. HISTORY.TXT FRISSÍTÉSE
# ================================================================

try:
    history_lines = []
    try:
        with open("history.txt", "r", encoding="utf-8") as f:
            history_lines = f.readlines()
    except:
        pass

    history_lines = [l for l in history_lines if not l.startswith("UTOLSO_FUTES:")]
    existing = "".join(history_lines)
    runs = re.split(r'\n--- FUTÁS:', existing)
    runs = [r for r in runs if r.strip()]
    runs = runs[-9:] if len(runs) >= 9 else runs

    new_entry = [
        f"\n--- FUTÁS: {now} ---\n",
        f"Téma: {TEMA_KULCS} | Modell: {MODELL} | "
        f"Hírek: {len(news_json.get('news', []))} db | RSS: {len(rss_headlines)} cím\n",
    ] + [f"{s}\n" for s in rss_stats]

    with open("history.txt", "w", encoding="utf-8") as f:
        f.write(f"UTOLSO_FUTES: {today}\n")
        f.write(f"# Futási előzmények (utolsó 10 futás)\n")
        f.write(f"# {'='*55}\n")
        for r in runs:
            f.write(f"\n--- FUTÁS:{r}")
        f.writelines(new_entry)

    print(f"history.txt frissítve ({len(runs)+1} bejegyzés)")
except Exception as e:
    print(f"history.txt hiba: {e}")


# ================================================================
# 10. HTML GENERÁLÁS
# ================================================================

# Kategória ikonok és színek
# Az adatbázisból jövő kategóriákat alapszínekkel látja el
CAT_SZINEK = [
    "#e63946", "#457b9d", "#f4a261", "#2d6a4f",
    "#9b2226", "#7b2d8b", "#6c757d", "#e9c46a",
    "#264653", "#e76f51",
]
CAT_IKONOK = ["🇭🇺", "🌍", "💡", "⚖️", "🔬", "🚀", "🛡️", "📊", "🏢", "🎯"]

# Kategória stílus dinamikusan generálva
cat_style = {}
for i, kat in enumerate(KATEGORIAK):
    cat_style[kat] = (
        CAT_IKONOK[i % len(CAT_IKONOK)],
        CAT_SZINEK[i % len(CAT_SZINEK)]
    )
# Magyar mindig piros zászlóval
cat_style["Magyar"] = ("🇭🇺", "#e63946")

# Szűrő gombok HTML-je dinamikusan a kategóriákból
filter_gombok = '<button class="filter-btn active" onclick="filter(this,\'mind\')">Összes</button>\n'
for kat in KATEGORIAK:
    ikon = cat_style.get(kat, ("📰", "#457b9d"))[0]
    filter_gombok += f'    <button class="filter-btn" onclick="filter(this,\'{kat}\')">{ikon} {kat}</button>\n'

# Hírkártyák HTML-je
news_items_html = ""
for item in news_json.get("news", []):
    cat = item.get("category", KATEGORIAK[0] if KATEGORIAK else "Egyéb")
    icon, color = cat_style.get(cat, ("📰", "#457b9d"))

    summary = item.get("summary") or item.get("summary_en", "")
    details = item.get("details") or item.get("details_en", "")
    relevance = item.get("relevance", "")

    summary_extra = ""
    if NYELV == "magyar+angol" and item.get("summary_en"):
        summary_extra = (
            f'<p class="card-summary" style="margin-top:8px;'
            f'font-style:italic;opacity:.8">{item.get("summary_en","")}</p>'
        )

    details_html = f'<div class="card-details">{details}</div>' if details else ""
    relevance_html = (
        f'<div class="card-relevance">'
        f'<span class="relevance-label">💡 Miért érdekes?</span> {relevance}</div>'
        if relevance else ""
    )

    news_items_html += f"""
    <article class="news-card" data-category="{cat}">
      <div class="card-accent" style="background:{color}"></div>
      <div class="card-body">
        <span class="category-badge" style="color:{color};border-color:{color}20;background:{color}10">{icon} {cat}</span>
        <h2 class="card-title">{item.get('title','')}</h2>
        <p class="card-summary">{summary}</p>
        {summary_extra}
        {details_html}
        {relevance_html}
        <a href="{item.get('url','#')}" class="card-link" target="_blank" rel="noopener nofollow">
          <span>{item.get('source','Forrás')}</span>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6"/>
            <polyline points="15,3 21,3 21,9"/>
            <line x1="10" y1="14" x2="21" y2="3"/>
          </svg>
        </a>
      </div>
    </article>"""

total = len(news_json.get('news', []))

html = f"""<!DOCTYPE html>
<html lang="hu">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{OLDAL_CIM} – {news_json['date']}</title>
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
    <div class="header-tag">{OLDAL_ALCIM}</div>
    <h1>{OLDAL_CIM.replace(' ', '<br>', 1) if len(OLDAL_CIM) > 12 else OLDAL_CIM}</h1>
    <p class="timestamp">Utoljára frissítve: <strong style="color:var(--accent)">{now}</strong></p>
    <div class="summary-box">{news_json['summary']}</div>
  </header>
  <div class="filters">
    {filter_gombok}
  </div>
  <p class="news-count">Megjelenített hírek: <span id="count">{total}</span> / {total}</p>
  <div class="news-grid" id="grid">{news_items_html}</div>
  <footer>
    <p>Generálva <strong>Claude AI</strong> által · Utoljára frissítve: <strong>{now}</strong> · {LABLÉC}</p>
    <div class="legal">
      <p><strong>Jogi nyilatkozat:</strong> Ez az oldal nyilvánosan elérhető hírek automatikusan generált, saját szavakkal írt összefoglalóit tartalmazza tájékoztatási céllal. Az összefoglalók mesterséges intelligencia által készített, önálló átfogalmazások – nem az eredeti cikkek másolatai. Minden hírhez feltüntetésre kerül az eredeti forrás. A szerzői jogok az eredeti szerzőket és kiadókat illetik. Tartalomeltávolítási kérelem esetén jelezze és haladéktalanul intézkedünk.</p>
      <p><strong>Legal notice:</strong> This site publishes AI-generated summaries of publicly available articles for informational purposes. All summaries are independently rewritten and do not reproduce original articles. Each item credits and links to the original source. All copyrights remain with the respective authors and publishers. If you wish to request removal, please contact us and we will act promptly.</p>
    </div>
  </footer>
</div>
<script>
function filter(btn, cat) {{
  document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  let v = 0;
  document.querySelectorAll('.news-card').forEach(card => {{
    const show = cat === 'mind' || card.dataset.category === cat;
    card.classList.toggle('hidden', !show);
    if (show) v++;
  }});
  document.getElementById('count').textContent = v;
}}
</script>
</body>
</html>"""

os.makedirs("docs", exist_ok=True)
with open("docs/index.html", "w", encoding="utf-8") as f:
    f.write(html)

print(f"\n✅ Kész: docs/index.html")
print(f"📰 Összesen {total} hír | Téma: {TEMA_KULCS} | Modell: {MODELL}")
