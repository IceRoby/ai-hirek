# ================================================================
# HÍRGYŰJTŐ RENDSZER - FŐ SCRIPT (fetch_news.py)
# ================================================================
# Beállítások:
#   config.txt     → technikai beállítások
#   topics.txt     → témák és kulcsszavak
#   categories.txt → kategóriák
#   sources.txt    → RSS feedek
#   wordpress.txt  → WP oldalak
# ================================================================

import anthropic, json, datetime, os, re, urllib.request, traceback
import xml.etree.ElementTree as ET

# ================================================================
# HIBAKEZELÉS ÉS NAPLÓZÁS
# ================================================================
ERROR_LOG = "error.log"
MAX_LOG_SIZE = 2 * 1024 * 1024  # 2MB

def log_error(context, error, extra=None):
    """
    Részletes hibaüzenetet ír az error.log fájlba.
    Az újabb hibák mindig a fájl TETEJÉRE kerülnek.
    Ha a fájl eléri a 2MB-ot, a legrégebbi bejegyzések törlődnek.
    """
    now = (datetime.datetime.utcnow() + datetime.timedelta(hours=2)).strftime(
        "%Y.%m.%d %H:%M:%S")
    sep = "─" * 60
    lines = [
        "",
        sep,
        f"❌ HIBA: {now}",
        f"Kontextus: {context}",
        f"Hiba típusa: {type(error).__name__}",
        f"Hiba üzenet: {str(error)}",
    ]
    if extra:
        lines.append(f"Extra info: {extra}")
    tb = traceback.format_exc()
    if tb and tb.strip() != "NoneType: None":
        lines.append("Stack trace:")
        lines.append(tb)
    lines.append(sep)
    lines.append("")
    entry = "\n".join(lines)
    
    try:
        # Meglévő tartalom beolvasása
        existing = ""
        if os.path.exists(ERROR_LOG):
            with open(ERROR_LOG, "r", encoding="utf-8") as f:
                existing = f.read()
        
        # Új tartalom = új hiba + régi tartalom (legfrissebb felül)
        new_content = entry + existing
        
        # Méretkorlát: ha > 2MB, levágjuk a végét
        if len(new_content.encode("utf-8")) > MAX_LOG_SIZE:
            # Becsléssel levágjuk az utolsó 20%-ot
            cutoff = int(len(new_content) * 0.8)
            new_content = new_content[:cutoff]
            new_content += f"\n\n[...régebbi bejegyzések eltávolítva - méretkorlát ({MAX_LOG_SIZE//1024}KB) elérve...]\n"
        
        with open(ERROR_LOG, "w", encoding="utf-8") as f:
            f.write(new_content)
            
    except Exception as log_err:
        print(f"⚠️ Hibanaplózás sikertelen: {log_err}")

def log_info(message):
    """Tájékoztató üzenet az error.log-ba (nem hiba, de fontos esemény)."""
    now = (datetime.datetime.utcnow() + datetime.timedelta(hours=2)).strftime(
        "%Y.%m.%d %H:%M:%S")
    try:
        existing = ""
        if os.path.exists(ERROR_LOG):
            with open(ERROR_LOG, "r", encoding="utf-8") as f:
                existing = f.read()
        entry = f"ℹ️  {now} – {message}\n"
        with open(ERROR_LOG, "w", encoding="utf-8") as f:
            f.write(entry + existing)
    except:
        pass


# ================================================================
# FÁJL BEOLVASÓ FÜGGVÉNYEK
# ================================================================

def load_config(filename="config.txt"):
    """config.txt beolvasása → dict"""
    cfg = {}
    try:
        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"): continue
                parts = [p.strip() for p in line.split("|")]
                if len(parts) == 3 and parts[0] == "config":
                    cfg[parts[1]] = parts[2]
        print(f"config.txt: {len(cfg)} beállítás")
    except Exception as e:
        print(f"config.txt hiba: {e}")
    return cfg


def load_topics(filename="topics.txt"):
    """
    topics.txt beolvasása → dict
    Formátum: topic | kulcs | kulcsszavak | kizárt | leírás
    Visszatér: {kulcs: {kulcsszavak:[], kizart:[], leiras:str}}
    """
    topics = {}
    try:
        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"): continue
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 2 and parts[0] == "topic":
                    kulcs = parts[1].lower()
                    kulcsszavak = [k.strip() for k in parts[2].split(",") if k.strip()] if len(parts) > 2 else []
                    kizart = [k.strip() for k in parts[3].split(",") if k.strip()] if len(parts) > 3 else []
                    leiras = parts[4] if len(parts) > 4 else kulcs
                    topics[kulcs] = {
                        "kulcsszavak": kulcsszavak,
                        "kizart": kizart,
                        "leiras": leiras
                    }
        print(f"topics.txt: {len(topics)} téma betöltve")
    except Exception as e:
        print(f"topics.txt hiba: {e}")
    return topics


def load_categories(filename="categories.txt"):
    """
    categories.txt beolvasása → dict
    Formátum: category | név | tema_kulcs | wp_oldalak
    Visszatér: {tema_kulcs: [{nev, wp_oldalak:[]}]}
    """
    categories = {}  # tema_kulcs → [kategória dict]
    all_cats = []    # összes kategória listája
    try:
        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"): continue
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 2 and parts[0] == "category":
                    nev = parts[1]
                    tema = parts[2].lower() if len(parts) > 2 else "altalanos"
                    wp_oldalak_str = parts[3] if len(parts) > 3 else ""
                    wp_oldalak = [w.strip() for w in wp_oldalak_str.split(",") if w.strip()]
                    cat_adat = {"nev": nev, "tema": tema, "wp_oldalak": wp_oldalak}
                    if tema not in categories:
                        categories[tema] = []
                    categories[tema].append(cat_adat)
                    all_cats.append(cat_adat)
        print(f"categories.txt: {len(all_cats)} kategória betöltve")
    except Exception as e:
        print(f"categories.txt hiba: {e}")
    return categories, all_cats


def load_sources(filename="sources.txt"):
    """sources.txt beolvasása → (rss_feeds, domains)"""
    rss_feeds, domains = [], []
    try:
        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"): continue
                parts = [p.strip() for p in line.split("|")]
                if len(parts) != 3: continue
                typ, name, value = parts
                if typ == "rss": rss_feeds.append((name, value))
                elif typ in ("domain", "url"): domains.append((name, value))
        print(f"sources.txt: {len(rss_feeds)} RSS, {len(domains)} domain")
    except Exception as e:
        print(f"sources.txt hiba: {e}")
    return rss_feeds, domains


def load_wordpress(filename="wordpress.txt"):
    """
    wordpress.txt beolvasása → list of wp_config dicts
    """
    wp_raw = {}  # "wp1_url" → érték
    try:
        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"): continue
                parts = [p.strip() for p in line.split("|")]
                if len(parts) == 3 and parts[0] == "wp":
                    wp_raw[parts[1]] = parts[2]
        print(f"wordpress.txt: {len(wp_raw)} beállítás")
    except Exception as e:
        print(f"wordpress.txt hiba: {e}")

    # Oldalankénti csoportosítás
    wp_sites = []
    for i in range(1, 20):
        prefix = f"wp{i}_"
        url = wp_raw.get(f"{prefix}url", "")
        if not url: break
        wp_sites.append({
            "index": i,
            "url":          url,
            "user":         wp_raw.get(f"{prefix}user", ""),
            "app_password": os.environ.get(f"WP{i}_APP_PASSWORD", ""),
            "tipus":        wp_raw.get(f"{prefix}tipus", "altalanos"),
            "post_status":  wp_raw.get(f"{prefix}post_status", "publish"),
            "post_mode":    wp_raw.get(f"{prefix}post_mode", "summary"),
            "kategoria":    wp_raw.get(f"{prefix}kategoria", ""),
            "szerzo":       wp_raw.get(f"{prefix}szerzo", ""),
            "kep_url":      wp_raw.get(f"{prefix}kep_url", ""),
            "kep_kulcsszo": wp_raw.get(f"{prefix}kep_kulcsszo", ""),
        })
    print(f"wordpress.txt: {len(wp_sites)} WP oldal")
    return wp_sites


def load_last_run(filename="history.txt"):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("UTOLSO_FUTES:"):
                    return line.replace("UTOLSO_FUTES:", "").strip()
    except: pass
    return None


# ================================================================
# RSS FEED LETÖLTŐ
# ================================================================

def fetch_rss_feeds(rss_feeds):
    headlines, stats = [], []
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
                    t = (item.find("title") or item.find("{http://www.w3.org/2005/Atom}title"))
                    l = (item.find("link") or item.find("{http://www.w3.org/2005/Atom}link"))
                    title = t.text.strip() if t is not None and t.text else ""
                    link  = l.text.strip() if l is not None and l.text else (l.get("href","") if l is not None else "")
                    if title and link:
                        headlines.append(f"- {title} | {link} [{name}]")
                        count += 1
            stats.append(f"  {name:<40} OK    {count}")
        except Exception as e:
            stats.append(f"  {name:<40} HIBA  {str(e)[:45]}")
            if "403" in str(e) or "404" in str(e) or "timeout" in str(e).lower():
                pass  # Ismert hibák - nem naplózzuk
            else:
                log_error(f"RSS letöltés – {name}", e, extra=f"URL: {url[:80]}")
    return headlines, stats


# ================================================================
# AUTOMATIKUS BŐVÍTÉS (sources.txt és categories.txt)
# ================================================================

def count_active_lines(filename):
    """Megszámolja az aktív (nem komment, nem üres) sorokat."""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return sum(1 for l in f if l.strip() and not l.strip().startswith("#"))
    except:
        return 0


def find_section_end(lines, tema_kulcs, file_type="sources"):
    """
    Megkeresi a megfelelő szekció végét ahol az #auto sort be kell szúrni.
    Visszatér: az index ahol be kell szúrni (vagy -1 ha a fájl végére)
    """
    # Keressük a témához tartozó szekciót
    tema_marker = f"# {tema_kulcs.upper()}" if file_type == "categories" else None
    auto_marker = "# AI ÁLTAL AUTOMATIKUSAN"

    in_tema_section = False
    auto_section_start = -1
    last_tema_line = -1

    for i, line in enumerate(lines):
        stripped = line.strip()
        # Auto szekció kezdete
        if "AUTOMATIKUSAN FELFEDEZETT" in stripped or "AI ÁLTAL AUTO" in stripped:
            auto_section_start = i
        # Téma szekció (categories.txt-hez)
        if tema_marker and tema_marker in stripped.upper():
            in_tema_section = True
            last_tema_line = i
        if in_tema_section and stripped.startswith("category"):
            last_tema_line = i

    # Ha van auto szekció, oda szúrjuk be
    if auto_section_start >= 0:
        return auto_section_start + 1

    # Ha van téma szekció, annak a végére
    if last_tema_line >= 0:
        return last_tema_line + 1

    return -1  # fájl végére


def auto_add_source(name, url, tema_kulcs, reason="", max_sorok=80):
    """Új forrást ad a sources.txt-hez #auto jelzéssel, a megfelelő helyre szúrva be."""
    try:
        if max_sorok > 0 and count_active_lines("sources.txt") >= max_sorok:
            print(f"  #auto forrás kihagyva (max {max_sorok} sor elérve): {name}")
            return
        with open("sources.txt", "r", encoding="utf-8") as f:
            content_str = f.read()
        if url in content_str:
            return
        lines = content_str.splitlines(keepends=True)
        insert_idx = -1
        for i, line in enumerate(lines):
            if "AUTOMATIKUSAN FELFEDEZETT" in line or "ide írja az AI" in line.lower():
                insert_idx = i + 1
                break
        datum = datetime.date.today().isoformat()
        comment = f"# #auto [{datum}] – {reason}\n" if reason else f"# #auto [{datum}]\n"
        new_lines = [comment, f"#auto | rss | {name} | {url}\n"]
        if insert_idx >= 0:
            lines[insert_idx:insert_idx] = new_lines
        else:
            lines.extend(["\n"] + new_lines)
        with open("sources.txt", "w", encoding="utf-8") as f:
            f.writelines(lines)
        print(f"  ✓ #auto forrás hozzáadva: {name} [{tema_kulcs}]")
    except Exception as e:
        print(f"  #auto forrás hiba: {e}")


def auto_add_category(name, tema_kulcs, reason="", max_sorok=80):
    """Új kategóriát ad a categories.txt-hez #auto jelzéssel, a megfelelő témaszekciójába."""
    try:
        if max_sorok > 0 and count_active_lines("categories.txt") >= max_sorok:
            print(f"  #auto kategória kihagyva (max {max_sorok} sor elérve): {name}")
            return
        with open("categories.txt", "r", encoding="utf-8") as f:
            content_str = f.read()
        if f"| {name} |" in content_str:
            return
        lines = content_str.splitlines(keepends=True)
        insert_idx = -1
        tema_upper = tema_kulcs.upper()
        in_tema = False
        last_cat_in_tema = -1
        for i, line in enumerate(lines):
            stripped = line.strip()
            if tema_upper in stripped.upper() and stripped.startswith("#"):
                in_tema = True
            elif in_tema and stripped.startswith("# ==="):
                break
            elif in_tema and stripped.startswith("category"):
                last_cat_in_tema = i
            elif in_tema and "AUTOMATIKUSAN" in stripped:
                insert_idx = i + 1
                break
        if insert_idx < 0 and last_cat_in_tema >= 0:
            insert_idx = last_cat_in_tema + 1
        if insert_idx < 0:
            for i, line in enumerate(lines):
                if "AUTOMATIKUSAN FELFEDEZETT" in line or "ide írja az AI" in line.lower():
                    insert_idx = i + 1
                    break
        datum = datetime.date.today().isoformat()
        comment = f"# #auto [{datum}] – {reason}\n" if reason else f"# #auto [{datum}]\n"
        new_lines = [comment, f"#auto category | {name} | {tema_kulcs} | mind\n"]
        if insert_idx >= 0:
            lines[insert_idx:insert_idx] = new_lines
        else:
            lines.extend(["\n"] + new_lines)
        with open("categories.txt", "w", encoding="utf-8") as f:
            f.writelines(lines)
        print(f"  ✓ #auto kategória hozzáadva: {name} [{tema_kulcs}]")
    except Exception as e:
        print(f"  #auto kategória hiba: {e}")


def auto_add_topic(kulcs, kulcsszavak, kategoriak, reason="", max_sorok=25):
    """Új témát ad a topics.txt-hez #auto jelzéssel, az inaktív témák szekciójába."""
    try:
        if max_sorok > 0 and count_active_lines("topics.txt") >= max_sorok:
            print(f"  #auto téma kihagyva (max {max_sorok} sor elérve): {kulcs}")
            return
        with open("topics.txt", "r", encoding="utf-8") as f:
            content_str = f.read()
        if f"topic | {kulcs}" in content_str:
            return
        lines = content_str.splitlines(keepends=True)
        insert_idx = -1
        for i, line in enumerate(lines):
            if "AUTOMATIKUSAN FELFEDEZETT" in line or "ide írja az AI" in line.lower():
                insert_idx = i + 1
                break
        kw_str  = ", ".join(kulcsszavak[:8])
        kat_str = ", ".join(kategoriak[:5]) if kategoriak else kulcs
        datum = datetime.date.today().isoformat()
        comment = f"\n# #auto [{datum}] – {reason}\n" if reason else f"\n# #auto [{datum}]\n"
        new_lines = [comment, f"#auto topic | {kulcs} | {kw_str} | | {kat_str}\n"]
        if insert_idx >= 0:
            lines[insert_idx:insert_idx] = new_lines
        else:
            lines.extend(new_lines)
        with open("topics.txt", "w", encoding="utf-8") as f:
            f.writelines(lines)
        print(f"  ✓ #auto téma hozzáadva: {kulcs}")
    except Exception as e:
        print(f"  #auto téma hiba: {e}")


# ================================================================
# FŐ PROGRAM
# ================================================================

# Beállítások betöltése
cfg            = load_config()
topics         = load_topics()
cat_by_tema, all_cats = load_categories()
base_rss, domains     = load_sources()
wp_sites       = load_wordpress()
last_run       = load_last_run()

MODELL      = cfg.get("modell", "claude-haiku-4-5-20251001")
IDOABLAK    = cfg.get("idoablak_nap", "7")
aktiv_temak = [t.strip().lower() for t in cfg.get("aktiv_temak","ai").split(",") if t.strip()]

today    = datetime.date.today().strftime("%Y. %m. %d.")
today_iso = datetime.date.today().isoformat()
now      = (datetime.datetime.utcnow() + datetime.timedelta(hours=2)).strftime(
            "%Y. %m. %d. %H:%M:%S (Budapest)")

if last_run:
    date_filter = f"FONTOS: Csak {last_run} UTÁN megjelent híreket hozz!"
    since_text  = last_run
    print(f"Utolsó futás: {last_run}")
else:
    date_filter = f"Csak az elmúlt {IDOABLAK} napban megjelent híreket hozz!"
    since_text  = f"az elmúlt {IDOABLAK} napban"


def fetch_news_for_tema(tema_kulcs, topic_adat, kategoriak_lista,
                        rss_feeds, domains, cfg,
                        date_filter, since_text, today, client):
    """Egy témához lekéri a híreket Claude API-n keresztül."""

    MODELL      = cfg.get("modell", "claude-haiku-4-5-20251001")
    HIREK_SZAMA = cfg.get("hirek_szama", "20-25")
    NYELV       = cfg.get("nyelv", "magyar")
    FOKUSZ      = cfg.get("fokusz_regiok", "globális, magyar")
    AUTO_FORRAS = cfg.get("auto_forras_bővítés", "igen") == "igen"
    AUTO_KAT    = cfg.get("auto_kategoria_bővítés", "igen") == "igen"

    kulcsszavak = topic_adat.get("kulcsszavak", [])
    kizart      = topic_adat.get("kizart", [])
    leiras      = topic_adat.get("leiras", tema_kulcs)

    print(f"\n{'─'*55}")
    print(f"TÉMA: {tema_kulcs.upper()} – {leiras}")
    print(f"{'─'*55}")

    tema_kategoriak = [k["nev"] for k in kategoriak_lista
                      if k["tema"] in (tema_kulcs, "altalanos")]
    kategoriak_str = ", ".join(tema_kategoriak) if tema_kategoriak else \
        "Magyar, Nemzetközi, Kutatás, Trendek, Eszközök, Egyéb"

    # Google News feedek generálása
    tema_rss = list(rss_feeds)
    meglevo = {n for n, _ in tema_rss}
    if kulcsszavak:
        for kw in kulcsszavak[:3]:
            nev = f"Google News – {kw}"
            if nev not in meglevo:
                url = f"https://news.google.com/rss/search?q={kw.replace(' ','+')}&hl=en&gl=US&ceid=US:en"
                tema_rss.append((nev, url))
        hu_nev = f"Google News Magyar – {tema_kulcs}"
        if hu_nev not in meglevo:
            tema_rss.append((hu_nev,
                f"https://news.google.com/rss/search?q={tema_kulcs}+hirek&hl=hu&gl=HU&ceid=HU:hu"))

    rss_headlines, rss_stats = fetch_rss_feeds(tema_rss)
    rss_context = "\n".join(rss_headlines[:60])
    domain_list = ", ".join([v for _, v in domains])
    print(f"RSS: {len(rss_headlines)} cím")

    kereses_lista = []
    if kulcsszavak:
        kereses_lista.append(f"{' '.join(kulcsszavak[:4])} news this week")
        kereses_lista.append(f"{tema_kulcs} latest news")
    kereses_lista.append(f"{tema_kulcs} news {today}")
    kereses_lista.append(f"magyar {tema_kulcs} hirek")
    if kulcsszavak:
        kereses_lista.append(f"{kulcsszavak[0]} trends 2026")
    temak_lista = "\n".join([f"{i+1}. {t}" for i, t in enumerate(kereses_lista)])

    kizarasi = f"KIZÁRT témák: {', '.join(kizart)}" if kizart else ""

    if NYELV == "angol":
        nylv_ut = "Write all summaries in English."
        json_sema = (f'{{"date":"{today}","tema":"{tema_kulcs}",'
            f'"summary":"3-4 sentence summary",'
            f'"new_sources":[{{"name":"Source","url":"https://rss.url/feed","reason":"why useful"}}],'
            f'"new_categories":[{{"name":"Category name","reason":"why it fits"}}],'
            f'"new_topics":[{{"kulcs":"new_topic","kulcsszavak":["kw1"],"kategoriak":["Cat1"],"reason":"why interesting"}}],'
            f'"news":[{{"title":"title","date":"YYYY-MM-DD or empty",'
            f'"summary":"2-3 sentences","details":"2-3 sentences",'
            f'"personal_value":"1-2 sentences for reader",'
            f'"source":"Source","url":"https://...","category":"cat"}}]}}')
    else:
        nylv_ut = "Minden összefoglalót MAGYARUL írj, saját szavakkal."
        json_sema = (f'{{"date":"{today}","tema":"{tema_kulcs}",'
            f'"summary":"3-4 mondatos összefoglaló magyarul",'
            f'"new_sources":[{{"name":"Forrás neve","url":"https://rss.url/feed","reason":"miért hasznos"}}],'
            f'"new_categories":[{{"name":"Kategória neve","reason":"miért illik ide"}}],'
            f'"new_topics":[{{"kulcs":"uj_tema","kulcsszavak":["kw1"],"kategoriak":["Kat1"],"reason":"miért érdekes"}}],'
            f'"news":[{{"title":"hír címe magyarul",'
            f'"date":"forrás cikk dátuma ÉÉÉÉ-HH-NN formátumban vagy üres",'
            f'"summary":"2-3 mondatos összefoglaló saját szavakkal",'
            f'"details":"2-3 mondatos kifejtés: számok, nevek, összefüggések",'
            f'"personal_value":"1-2 mondat: mit jelent ez az olvasónak - konkrét haszna vagy lehetősége, kerülve kockázatos tanácsokat",'
            f'"source":"Forrás neve","url":"https://...","category":"kategória"}}]}}')

    auto_utasitas = ""
    if AUTO_FORRAS:
        auto_utasitas += (
            "\nHA találsz megbízható RSS feedet a témához, add meg a new_sources listában (max 3):"
            "\n  {\"name\": \"Forrás neve\", \"url\": \"https://rss.url/feed\", \"reason\": \"miért hasznos\"}")
    if AUTO_KAT:
        auto_utasitas += (
            f"\nHA a hírek között olyan alkategória jelenik meg ami nincs a listában ({kategoriak_str}),"
            "\nadd meg a new_categories listában (max 3):"
            "\n  {\"name\": \"Kategória neve\", \"reason\": \"miért illik ide\"}")
    if cfg.get("auto_tema_bővítés","igen") == "igen":
        auto_utasitas += (
            "\nHA teljesen új releváns témát fedezel fel, add meg a new_topics listában (max 2):"
            "\n  {\"kulcs\": \"uj_tema\", \"kulcsszavak\": [\"kw1\"], \"kategoriak\": [\"Kat1\"], \"reason\": \"miért\"}")

    oldal_cim = cfg.get("oldal_cim", leiras)

    provider = KOLTSEG_TABLA.get(MODELL, {}).get("provider", "anthropic")
    print(f"API hívás... ({provider} / {MODELL})")

    if provider == "openai":
        # OpenAI API hívás
        import urllib.request as ur, json as js
        openai_key = os.environ.get("OPENAI_API_KEY", "")
        if not openai_key:
            print("❌ OPENAI_API_KEY nincs beállítva GitHub Secrets-ben!")
            news_json = {"date": today, "tema": tema_kulcs,
                        "summary": "OpenAI API kulcs hiányzik.", "news": [],
                        "new_sources": [], "new_categories": [], "new_topics": []}
            news_json["_token_usage"] = {}
            news_json["_rss_stats"] = rss_stats
            return news_json

        payload = {
            "model": MODELL,
            "max_tokens": 16000,
            "messages": [{"role": "user", "content": None}]  # filled below
        }
        # OpenAI nem támogatja a beépített web search tool-t ugyanígy
        # Ezért az RSS kontextusra támaszkodunk
        use_web_search = False

    elif provider == "google":
        # Google Gemini API hívás
        google_key = os.environ.get("GOOGLE_API_KEY", "")
        if not google_key:
            print("❌ GOOGLE_API_KEY nincs beállítva GitHub Secrets-ben!")
            news_json = {"date": today, "tema": tema_kulcs,
                        "summary": "Google API kulcs hiányzik.", "news": [],
                        "new_sources": [], "new_categories": [], "new_topics": []}
            news_json["_token_usage"] = {}
            news_json["_rss_stats"] = rss_stats
            return news_json
        use_web_search = False

    else:
        use_web_search = True  # Anthropic - web search elérhető

    # Prompt összeállítása (minden providernél ugyanaz)
    prompt_text = None  # filled below

    response = client.messages.create(
        model=MODELL, max_tokens=16000,
        tools=[{"type": "web_search_20250305", "name": "web_search"}] if use_web_search else [],
        messages=[{"role": "user", "content":
            f"""Mai dátum: {today}

Te a(z) '{leiras}' témájú hírek szerkesztője vagy.
{nylv_ut}

{date_filter}
⚠️ SZIGORÚ DÁTUMSZŰRŐ: Minden hír "date" mezőjét töltsd ki a valódi megjelenési dátummal!
Ha egy hír {since_text} előtt jelent meg, NE vedd fel! Ellenőrizd a dátumot minden hírnél!
{kizarasi}

FÓKUSZ: {FOKUSZ}
{"KULCSSZAVAK: " + ", ".join(kulcsszavak) if kulcsszavak else ""}

Friss RSS hírcímek:
{rss_context}

Keresési témák:
{temak_lista}

Extra oldalak: {domain_list}

Gyűjts {HIREK_SZAMA} EGYEDI hírt amelyek {since_text} jelentek meg.
Régebbi vagy ismétlődő híreket NE szerepeltess.
Minden hírhez add meg a forrás cikk dátumát ha ismert!

Elérhető kategóriák: {kategoriak_str}
{auto_utasitas}

KIZÁRÓLAG valid JSON-t írj:
{json_sema}"""
        }]
    )

    # JSON kinyerése
    news_json = None
    for block in response.content:
        if block.type == "text":
            text = block.text.strip()
            text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
            try:
                news_json = json.loads(text.strip())
                print(f"OK: {len(news_json.get('news',[]))} hír ({tema_kulcs})")
                break
            except:
                m = re.search(r'\{[\s\S]*"news"\s*:\s*\[[\s\S]*?\]\s*\}', text)
                if m:
                    try:
                        news_json = json.loads(m.group())
                        print(f"OK regex: {len(news_json.get('news',[]))} hír")
                        break
                    except: pass

    if not news_json:
        err_msg = f"JSON parse sikertelen a '{tema_kulcs}' témánál"
        print(f"FALLBACK: {tema_kulcs}")
        log_error(
            f"Claude API válasz feldolgozás – téma: {tema_kulcs}",
            Exception(err_msg),
            extra=f"Modell: {MODELL} | RSS címek: {len(rss_headlines)}"
        )
        news_json = {"date": today, "tema": tema_kulcs,
                     "summary": f"A {leiras} hírek betöltése során hiba történt.",
                     "news": [], "new_sources": [], "new_categories": [], "new_topics": []}

    # Token használat
    usage = getattr(response, 'usage', None)
    if usage:
        input_tok  = getattr(usage, 'input_tokens', 0)
        output_tok = getattr(usage, 'output_tokens', 0)
        arak = KOLTSEG_TABLA.get(MODELL, {"input": 0.003, "output": 0.015})
        koltseg_usd = (input_tok / 1000 * arak["input"]) + (output_tok / 1000 * arak["output"])
        huf_rate = 385
        try:
            req = urllib.request.Request(
                "https://api.exchangerate-api.com/v4/latest/USD",
                headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                rates = json.loads(resp.read().decode())
                huf_rate = rates.get("rates", {}).get("HUF", 385)
        except: pass
        koltseg_huf = koltseg_usd * huf_rate
        news_json["_token_usage"] = {
            "input_tokens": input_tok, "output_tokens": output_tok,
            "total_tokens": input_tok + output_tok,
            "koltseg_usd": round(koltseg_usd, 6),
            "koltseg_huf": round(koltseg_huf, 2),
            "huf_rate": round(huf_rate, 1),
        }
        print(f"  Token: {input_tok:,} in + {output_tok:,} out = {input_tok+output_tok:,}")
        print(f"  Költség: ${koltseg_usd:.5f} ≈ {koltseg_huf:.1f} Ft")
    else:
        news_json["_token_usage"] = {}

    # Automatikus bővítések
    max_src = int(cfg.get("max_sources_sorok", "80"))
    max_cat = int(cfg.get("max_categories_sorok", "80"))
    max_top = int(cfg.get("max_topics_sorok", "25"))

    if AUTO_FORRAS:
        for item_src in news_json.get("new_sources", []):
            if isinstance(item_src, dict):
                url  = item_src.get("url","")
                name = item_src.get("name", f"Auto – {tema_kulcs}")
                reason = item_src.get("reason","")
            elif isinstance(item_src, str) and item_src.startswith("http"):
                url, name, reason = item_src, f"Auto – {tema_kulcs}", ""
            else: continue
            if url: auto_add_source(name, url, tema_kulcs, reason, max_src)

    if AUTO_KAT:
        for item_cat in news_json.get("new_categories", []):
            if isinstance(item_cat, dict):
                name   = item_cat.get("name","")
                reason = item_cat.get("reason","")
            elif isinstance(item_cat, str) and item_cat:
                name, reason = item_cat, ""
            else: continue
            if name: auto_add_category(name, tema_kulcs, reason, max_cat)

    if cfg.get("auto_tema_bővítés","igen") == "igen":
        for item_top in news_json.get("new_topics", []):
            if isinstance(item_top, dict):
                kulcs  = item_top.get("kulcs","")
                kw     = item_top.get("kulcsszavak",[])
                kats   = item_top.get("kategoriak",[])
                reason = item_top.get("reason","")
                if kulcs: auto_add_topic(kulcs, kw, kats, reason, max_top)

    news_json["_rss_stats"] = rss_stats
    return news_json


# ================================================================
# KÖLTSÉGBECSLÉS ÉS KONTROLL
# ================================================================

KOLTSEG_TABLA = {
    # Claude modellek (Anthropic API)
    "claude-haiku-4-5-20251001": {"input": 0.00025,  "output": 0.00125, "provider": "anthropic"},
    "claude-sonnet-4-6":         {"input": 0.003,    "output": 0.015,   "provider": "anthropic"},
    "claude-opus-4-6":           {"input": 0.005,    "output": 0.025,   "provider": "anthropic"},
    "claude-opus-4-5":           {"input": 0.005,    "output": 0.025,   "provider": "anthropic"},
    # OpenAI modellek
    "gpt-4o":                    {"input": 0.0025,   "output": 0.010,   "provider": "openai"},
    "gpt-4o-mini":               {"input": 0.00015,  "output": 0.0006,  "provider": "openai"},
    "gpt-4.1":                   {"input": 0.002,    "output": 0.008,   "provider": "openai"},
    "gpt-4.1-mini":              {"input": 0.0004,   "output": 0.0016,  "provider": "openai"},
    # Google Gemini modellek
    "gemini-2.0-flash":          {"input": 0.0001,   "output": 0.0004,  "provider": "google"},
    "gemini-2.5-pro":            {"input": 0.00125,  "output": 0.010,   "provider": "google"},
    "gemini-1.5-flash":          {"input": 0.000075, "output": 0.0003,  "provider": "google"},
}

def becsuld_koltseg(modell, temak_szama, hirek_szama_str):
    """Durva költségbecslés futás előtt."""
    arak = KOLTSEG_TABLA.get(modell, {"input": 0.003, "output": 0.015})
    # Átlagos tokenszám becslés: ~3000 input + ~4000 output témánként
    max_hirek = int(hirek_szama_str.split("-")[-1]) if "-" in hirek_szama_str else 25
    input_tok  = temak_szama * (3000 + max_hirek * 50)
    output_tok = temak_szama * (max_hirek * 200)
    return (input_tok / 1000 * arak["input"]) + (output_tok / 1000 * arak["output"])

MAX_KOLTSEG    = float(cfg.get("max_koltseg_per_futes", "0"))
FIGYELMEZTES   = float(cfg.get("figyelmeztes_kuszob", "0.05"))
HAVAI_LIMIT    = float(cfg.get("havai_limit", "0"))

becsult = becsuld_koltseg(MODELL, len(aktiv_temak), cfg.get("hirek_szama", "20-25"))

# Futás kezdete naplózva
log_info(f"Futás indul – Témák: {', '.join(aktiv_temak)} | Modell: {MODELL}")

print(f"\n{'='*60}")
print(f"INDULÁS: {now}")
print(f"Témák: {', '.join(aktiv_temak)} | Modell: {MODELL}")
print(f"Becsült költség: ~${becsult:.4f}")

if MAX_KOLTSEG > 0 and becsult > MAX_KOLTSEG:
    print(f"❌ LEÁLLÍTVA: becsült ${becsult:.4f} > max ${MAX_KOLTSEG:.4f}")
    print(f"   Módosítsd a max_koltseg_per_futes értékét a config.txt-ben")
    print(f"   vagy csökkentsd a témák számát / válts olcsóbb modellre.")
    exit(1)

if FIGYELMEZTES > 0 and becsult >= FIGYELMEZTES:
    print(f"⚠️  FIGYELMEZTETÉS: becsült költség ${becsult:.4f} (küszöb: ${FIGYELMEZTES:.4f})")

if HAVAI_LIMIT > 0:
    # Napi futások száma alapján havi becslés
    napi_futasok = 1  # alapból napi 1
    cron = "0 5 * * 1"  # alapból heti
    if "* * *" in cron:
        napi_futasok = 1
    elif "* * 1" in cron or "* * 1-5" in cron:
        napi_futasok = 1/7
    havi_becslés = becsult * napi_futasok * 30
    if havi_becslés > HAVAI_LIMIT:
        print(f"⚠️  HAVI BECSLÉS: ~${havi_becslés:.2f}/hó meghaladja a ${HAVAI_LIMIT:.2f} limitet")
    else:
        print(f"✅ Havi becslés: ~${havi_becslés:.2f}/hó (limit: ${HAVAI_LIMIT:.2f})")

print(f"{'='*60}")

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

# Minden aktív témához lekérjük a híreket
tema_hirek  = {}
all_rss_stats = []

for tema_kulcs in aktiv_temak:
    topic_adat = topics.get(tema_kulcs, {
        "kulcsszavak": [tema_kulcs], "kizart": [],
        "leiras": tema_kulcs
    })
    kategoriak_lista = cat_by_tema.get(tema_kulcs, []) + cat_by_tema.get("altalanos", [])

    try:
        news_json = fetch_news_for_tema(
            tema_kulcs, topic_adat, kategoriak_lista,
            base_rss, domains, cfg,
            date_filter, since_text, today, client
        )
    except Exception as e:
        log_error(
            f"fetch_news_for_tema – téma: {tema_kulcs}",
            e,
            extra=f"Modell: {MODELL} | Kulcsszavak: {topic_adat.get('kulcsszavak',[])} | API key megvan: {bool(os.environ.get('ANTHROPIC_API_KEY'))}"
        )
        print(f"❌ Hiba a '{tema_kulcs}' témánál: {e}")
        news_json = {"date": today, "tema": tema_kulcs,
                     "summary": f"Hiba a hírek lekérése során: {str(e)[:100]}",
                     "news": [], "new_sources": [], "new_categories": [], "new_topics": [],
                     "_token_usage": {}, "_rss_stats": []}

    tema_hirek[tema_kulcs] = news_json
    all_rss_stats.extend(news_json.pop("_rss_stats", []))

    try:
        with open(f"news_{tema_kulcs}.json", "w", encoding="utf-8") as f:
            json.dump(news_json, f, ensure_ascii=False, indent=2)
    except Exception as e:
        log_error(f"news_{tema_kulcs}.json mentése", e)


# History frissítése
try:
    history_lines = []
    try:
        with open("history.txt", "r", encoding="utf-8") as f:
            history_lines = f.readlines()
    except: pass

    history_lines = [l for l in history_lines if not l.startswith("UTOLSO_FUTES:")]
    existing = "".join(history_lines)
    runs = [r for r in re.split(r'\n--- FUTÁS:', existing) if r.strip()]
    runs = runs[-9:]

    total_hirek = sum(len(nj.get("news",[])) for nj in tema_hirek.values())
    new_entry = [
        f"\n--- FUTÁS: {now} ---\n",
        f"Témák: {', '.join(aktiv_temak)} | Modell: {MODELL} | Hírek: {total_hirek}\n",
    ] + [f"{s}\n" for s in all_rss_stats[:20]]

    with open("history.txt", "w", encoding="utf-8") as f:
        f.write(f"UTOLSO_FUTES: {today}\n")
        f.write(f"# Futási előzmények (utolsó 10 futás)\n# {'='*55}\n")
        for r in runs:
            f.write(f"\n--- FUTÁS:{r}")
        f.writelines(new_entry)
    print(f"\nhistory.txt frissítve ({len(runs)+1} bejegyzés)")
except Exception as e:
    print(f"history.txt hiba: {e}")


# ================================================================
# GITHUB PAGES HTML GENERÁLÁS
# ================================================================

elso_tema  = aktiv_temak[0]
elso_news  = tema_hirek[elso_tema]
topic_adat = topics.get(elso_tema, {"leiras": elso_tema})

OLDAL_CIM   = cfg.get("oldal_cim",    topic_adat.get("leiras", "Hírek"))
OLDAL_ALCIM = cfg.get("oldal_alcim",  "Automatikus összefoglaló")
LABLÉC      = cfg.get("labléc_szoveg","Minden héten frissül automatikusan")

# Ha több téma, összesítjük
if len(aktiv_temak) > 1:
    osszes_hir = []
    for tk in aktiv_temak:
        for item in tema_hirek[tk].get("news", []):
            item["_tema"] = tk
            osszes_hir.append(item)
    elso_news = {"date": today,
                 "summary": " | ".join([tema_hirek[tk].get("summary","")[:60]+"…" for tk in aktiv_temak]),
                 "news": osszes_hir}
    OLDAL_CIM = cfg.get("oldal_cim", "Heti Hírek")

# Összes kategória a megjelenítéshez
kategoriak_html = list(dict.fromkeys(
    k["nev"] for k in all_cats
    if k["tema"] in aktiv_temak + ["altalanos"]
))

CAT_SZINEK = ["#e63946","#457b9d","#f4a261","#2d6a4f","#9b2226","#7b2d8b",
              "#6c757d","#e9c46a","#264653","#e76f51"]
CAT_IKONOK = ["🇭🇺","🌍","💡","⚖️","🔬","🚀","🛡️","📊","🏢","🎯"]
cat_style  = {}
for i, kat in enumerate(kategoriak_html):
    cat_style[kat] = (CAT_IKONOK[i % len(CAT_IKONOK)], CAT_SZINEK[i % len(CAT_SZINEK)])
cat_style["Magyar"] = ("🇭🇺","#e63946")
cat_style["Magyar AI"] = ("🇭🇺","#e63946")
cat_style["Magyar coaching"] = ("🇭🇺","#e63946")

filter_gombok = '<button class="filter-btn active" onclick="filter(this,\'mind\')">Összes</button>\n'
for kat in kategoriak_html:
    ikon = cat_style.get(kat,("📰","#457b9d"))[0]
    filter_gombok += f'    <button class="filter-btn" onclick="filter(this,\'{kat}\')">{ikon} {kat}</button>\n'

if len(aktiv_temak) > 1:
    tema_ikonok = {"ai":"🤖","coaching":"🎯","marketing":"📣","egeszseg":"💊",
                   "penzugy":"💰","ingatlan":"🏠","tech":"💻","uzlet":"💼","sport":"⚽","jog":"⚖️"}
    filter_gombok += '\n    <div class="filter-separator"></div>\n'
    for tk in aktiv_temak:
        ikon = tema_ikonok.get(tk,"📰")
        nev  = topics.get(tk,{}).get("leiras",tk)
        filter_gombok += f'    <button class="filter-btn tema-btn" onclick="filterTema(this,\'{tk}\')">{ikon} {nev}</button>\n'

news_items_html = ""
for item in elso_news.get("news",[]):
    cat       = item.get("category", kategoriak_html[0] if kategoriak_html else "Egyéb")
    icon, color = cat_style.get(cat,("📰","#457b9d"))
    item_tema = item.get("_tema", elso_tema)
    summary   = item.get("summary","")
    details   = item.get("details","")
    pv        = item.get("personal_value","")
    source    = item.get("source","Forrás")
    url       = item.get("url","#")
    item_date = item.get("date","")

    date_html    = f'<span class="item-date">📅 {item_date}</span>' if item_date else ""
    details_html = f'<div class="card-details">{details}</div>' if details else ""
    pv_html      = (f'<div class="card-relevance">'
                   f'<span class="relevance-label">💡 Miért érdekes és mi a haszna neked?</span>'
                   f' {pv}</div>') if pv else ""

    news_items_html += f"""
    <article class="news-card" data-category="{cat}" data-tema="{item_tema}">
      <div class="card-accent" style="background:{color}"></div>
      <div class="card-body">
        <div class="card-meta">
          <span class="category-badge" style="color:{color};border-color:{color}20;background:{color}10">{icon} {cat}</span>
          {date_html}
        </div>
        <h2 class="card-title">{item.get('title','')}</h2>
        <p class="card-summary">{summary}</p>
        {details_html}
        {pv_html}
        <a href="{url}" class="card-link" target="_blank" rel="noopener nofollow">
          <span>{source}</span>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6"/>
            <polyline points="15,3 21,3 21,9"/>
            <line x1="10" y1="14" x2="21" y2="3"/>
          </svg>
        </a>
      </div>
    </article>"""

total = len(elso_news.get("news",[]))

html = f"""<!DOCTYPE html>
<html lang="hu">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{OLDAL_CIM} – {today}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400&display=swap" rel="stylesheet">
<style>
  :root{{--bg:#0a0a0f;--surface:#13131a;--border:#1e1e2e;--text:#f0f0fa;--muted:#c8c8e0;--accent:#c8ff00}}
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
  .filter-separator{{width:100%;height:1px;background:var(--border);margin:4px 0}}
  .filter-btn{{background:var(--surface);border:1px solid var(--border);color:var(--muted);padding:8px 18px;border-radius:100px;font-family:'Syne',sans-serif;font-size:.78rem;font-weight:600;letter-spacing:.05em;cursor:pointer;transition:all .2s}}
  .filter-btn:hover,.filter-btn.active{{border-color:var(--accent);color:var(--accent);background:rgba(200,255,0,.05)}}
  .tema-btn{{border-style:dashed}}
  .news-count{{font-family:'Syne',sans-serif;font-size:.8rem;color:var(--muted);margin-bottom:24px}}
  .news-count span{{color:var(--accent);font-weight:700}}
  .news-grid{{display:grid;gap:20px}}
  .news-card{{background:var(--surface);border:1px solid var(--border);border-radius:12px;overflow:hidden;display:flex;transition:transform .2s,border-color .2s;animation:fadeUp .5s ease both}}
  .news-card:hover{{transform:translateY(-2px);border-color:#2e2e42}}
  .card-accent{{width:4px;flex-shrink:0;opacity:.8}}
  .card-body{{padding:22px 26px;flex:1}}
  .card-meta{{display:flex;align-items:center;gap:12px;margin-bottom:10px;flex-wrap:wrap}}
  .category-badge{{display:inline-block;font-family:'Syne',sans-serif;font-size:.72rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;padding:3px 10px;border-radius:100px;border:1px solid}}
  .item-date{{font-size:.75rem;color:var(--muted);opacity:.8}}
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
    <h1>{OLDAL_CIM}</h1>
    <p class="timestamp">Utoljára frissítve: <strong style="color:var(--accent)">{now}</strong></p>
    <div class="summary-box">{elso_news['summary']}</div>
  </header>
  <div class="filters">{filter_gombok}</div>
  <p class="news-count">Megjelenített hírek: <span id="count">{total}</span> / {total}</p>
  <div class="news-grid" id="grid">{news_items_html}</div>
  <footer>
    <p>Generálva <strong>Claude AI</strong> által · <strong>{now}</strong> · {LABLÉC}</p>
    <div class="legal">
      <p><strong>Jogi nyilatkozat:</strong> Ez az oldal nyilvánosan elérhető hírek automatikusan generált, saját szavakkal írt összefoglalóit tartalmazza tájékoztatási céllal. Az összefoglalók mesterséges intelligencia által készített, önálló átfogalmazások – nem az eredeti cikkek másolatai. Minden hírhez feltüntetésre kerül az eredeti forrás. A szerzői jogok az eredeti szerzőket és kiadókat illetik. Tartalomeltávolítási kérelem esetén jelezze és haladéktalanul intézkedünk.</p>
      <p><strong>Legal notice:</strong> This site publishes automatically generated summaries of publicly available news articles for informational purposes. All summaries are independently rewritten and do not reproduce original articles. Each item credits and links to the original source. All copyrights remain with the respective authors and publishers. If you are a rights holder and wish to request removal, please contact us and we will act promptly.</p>
    </div>
  </footer>
</div>
<script>
let aKat='mind', aTema='mind';
function filter(btn,cat){{
  document.querySelectorAll('.filter-btn:not(.tema-btn)').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active'); aKat=cat; frissit();
}}
function filterTema(btn,tema){{
  document.querySelectorAll('.tema-btn').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active'); aTema=tema; frissit();
}}
function frissit(){{
  let v=0;
  document.querySelectorAll('.news-card').forEach(card=>{{
    const show=(aKat==='mind'||card.dataset.category===aKat)&&(aTema==='mind'||card.dataset.tema===aTema);
    card.classList.toggle('hidden',!show);
    if(show)v++;
  }});
  document.getElementById('count').textContent=v;
}}
</script>
</body>
</html>"""

os.makedirs("docs", exist_ok=True)
with open("docs/index.html","w",encoding="utf-8") as f:
    f.write(html)
print(f"\n✅ GitHub Pages: {total} hír")


# ================================================================
# WORDPRESS FELTÖLTÉS
# ================================================================

wp_feltoltve = 0
for wp in wp_sites:
    i       = wp["index"]
    wp_url  = wp["url"]
    wp_pass = wp["app_password"]
    tipus   = wp["tipus"]

    if not wp_pass:
        print(f"\nWP{i} ({wp_url}): Nincs WP{i}_APP_PASSWORD – kihagyva")
        continue

    # Melyik hírek menjenek erre az oldalra?
    if tipus == "altalanos":
        wp_news = {"date": today,
                   "summary": " ".join([tema_hirek[tk].get("summary","")[:80] for tk in aktiv_temak]),
                   "news": [item for tk in aktiv_temak for item in tema_hirek[tk].get("news",[])]}
        wp_tema = "altalanos"

    elif tipus.startswith("tema:"):
        spec = tipus.replace("tema:","").strip()
        if spec not in tema_hirek:
            print(f"\nWP{i}: '{spec}' nem aktív téma – kihagyva")
            continue
        wp_news = tema_hirek[spec]
        wp_tema = spec

    elif tipus.startswith("kategoriak:"):
        # Csak megadott kategóriájú hírek
        kat_lista = [k.strip() for k in tipus.replace("kategoriak:","").split(",")]
        szurt_hirek = [
            item for tk in aktiv_temak
            for item in tema_hirek[tk].get("news",[])
            if item.get("category","") in kat_lista
        ]
        if not szurt_hirek:
            print(f"\nWP{i}: nincs hír a megadott kategóriákban – kihagyva")
            continue
        wp_news = {"date": today, "summary": "", "news": szurt_hirek}
        wp_tema = "altalanos"

    else:
        print(f"\nWP{i}: ismeretlen típus '{tipus}' – kihagyva")
        continue

    wp_config = {**wp, "tema": wp_tema}
    oldal_cim = topics.get(wp_tema,{}).get("leiras", OLDAL_CIM)

    print(f"\nWordPress feltöltés: WP{i} {wp_url} [{tipus}]")
    try:
        import wordpress_upload
        uploaded = wordpress_upload.upload_to_wordpress(
            wp_news, wp_config,
            os.environ.get("PEXELS_API_KEY",""),
            os.environ.get("UNSPLASH_API_KEY",""),
            wp_tema, oldal_cim
        )
        if uploaded:
            wp_feltoltve += len(uploaded)
            print(f"✅ WP{i}: {len(uploaded)} post feltöltve")
    except Exception as e:
        log_error(
            f"WordPress feltöltés – WP{i} ({wp_url})",
            e,
            extra=f"Típus: {tipus} | Post mód: {wp.get('post_mode')} | User: {wp.get('user')}"
        )
        print(f"❌ WP{i} hiba: {e}")

# ================================================================
# ÖSSZESÍTETT KÖLTSÉG RIPORT
# ================================================================
print(f"\n{'='*60}")
print(f"KÉSZ: {now}")

osszes_input  = sum(nj.get("_token_usage",{}).get("input_tokens",0)  for nj in tema_hirek.values())
osszes_output = sum(nj.get("_token_usage",{}).get("output_tokens",0) for nj in tema_hirek.values())
osszes_usd    = sum(nj.get("_token_usage",{}).get("koltseg_usd",0)    for nj in tema_hirek.values())
huf_rate      = next((nj.get("_token_usage",{}).get("huf_rate",370) for nj in tema_hirek.values() if nj.get("_token_usage",{}).get("huf_rate")), 370)
osszes_huf    = osszes_usd * huf_rate

print(f"Témák: {len(aktiv_temak)} | Hírek: {sum(len(nj.get('news',[])) for nj in tema_hirek.values())} | WP: {wp_feltoltve} post")
print(f"{'─'*60}")
print(f"TOKEN HASZNÁLAT:")
print(f"  Input:  {osszes_input:>10,} token")
print(f"  Output: {osszes_output:>10,} token")
print(f"  Összes: {osszes_input+osszes_output:>10,} token")
print(f"KÖLTSÉG:")
print(f"  Modell:    {MODELL}")
print(f"  Árfolyam:  {huf_rate:.0f} Ft/USD")
print(f"  Ez a futás: ${osszes_usd:.5f} ≈ {osszes_huf:.1f} Ft")

# Havi vetítés
cron_str = "hetente"
havi_szorzo = 4  # alapból heti → 4x/hó
havi_usd = osszes_usd * havi_szorzo
havi_huf = havi_usd * huf_rate
print(f"  Havi becslés ({cron_str}): ${havi_usd:.3f} ≈ {havi_huf:.0f} Ft/hó")

# History-ba is mentjük a költséget
try:
    with open("history.txt", "r", encoding="utf-8") as f:
        htxt = f.read()
    koltseg_sor = f"Költség: ${osszes_usd:.5f} ≈ {osszes_huf:.1f} Ft | Token: {osszes_input+osszes_output:,}\n"
    temak_sor_prefix = f"Témák: {', '.join(aktiv_temak)} | Modell: {MODELL} | Hírek:"
    htxt_new = htxt
    for line in htxt.split("\n"):
        if line.startswith(temak_sor_prefix):
            htxt_new = htxt_new.replace(line + "\n", line + "\n" + koltseg_sor, 1)
            break
    with open("history.txt", "w", encoding="utf-8") as f:
        f.write(htxt_new)
except Exception as e:
    print(f"  (history.txt költség mentési hiba: {e})")

print(f"{'='*60}")
