# ================================================================
# WORDPRESS FELTÖLTŐ SCRIPT (wordpress_upload.py)
# ================================================================
# Feltölti a híreket WordPress oldalra REST API-n keresztül.
# RankMath SEO kompatibilis meta adatokkal.
# NORMÁL ESETBEN NEM KELL MÓDOSÍTANI!
# ================================================================

import json, os, re, urllib.request, urllib.parse, base64, datetime


# ================================================================
# SEGÉDFÜGGVÉNYEK
# ================================================================

def api_request(url, method="GET", data=None, headers=None, auth=None):
    if headers is None:
        headers = {}
    headers["Content-Type"] = "application/json"
    headers["Accept"] = "application/json"
    if auth:
        cred = base64.b64encode(f"{auth['user']}:{auth['password']}".encode()).decode()
        headers["Authorization"] = f"Basic {cred}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode()), resp.status
    except urllib.error.HTTPError as e:
        print(f"HTTP hiba {e.code}: {e.read().decode()[:200]}")
        return None, e.code
    except Exception as e:
        print(f"Kérés hiba: {e}")
        return None, 0


def slugify(text, max_length=60):
    """SEO-barát URL slug generálása."""
    replacements = {
        'á':'a','é':'e','í':'i','ó':'o','ö':'o','ő':'o','ú':'u','ü':'u','ű':'u',
        'Á':'a','É':'e','Í':'i','Ó':'o','Ö':'o','Ő':'o','Ú':'u','Ü':'u','Ű':'u',
    }
    for orig, repl in replacements.items():
        text = text.replace(orig, repl)
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s]+', '-', text.strip())
    text = re.sub(r'-+', '-', text)
    if len(text) > max_length:
        text = text[:max_length].rsplit('-', 1)[0]
    return text


def generate_meta_description(text, max_length=155):
    """SEO meta description, max 155 karakter."""
    if not text or len(text) <= max_length:
        return text or ""
    truncated = text[:max_length]
    last_period = truncated.rfind('.')
    if last_period > max_length * 0.7:
        return truncated[:last_period + 1]
    last_space = truncated.rfind(' ')
    if last_space > 0:
        return truncated[:last_space] + "..."
    return truncated + "..."


def generate_seo_title(title, max_length=60):
    """SEO title, max 60 karakter."""
    if len(title) <= max_length:
        return title
    return title[:max_length].rsplit(' ', 1)[0] + "..."


# ================================================================
# KÉP KEZELÉS
# ================================================================

def get_image(wp_config, pexels_key, unsplash_key):
    """
    Képet keres a prioritás sorrendben:
    1. Fix kép URL (wp_kep_url a config-ban)
    2. Pexels API
    3. Unsplash API
    Visszatér: (kép URL, attribúció) vagy (None, None)
    """
    # 1. Fix kép URL a config-ból
    fix_url = wp_config.get("kep_url", "")
    if fix_url:
        print(f"Fix kép URL használata: {fix_url[:60]}...")
        return fix_url, ""

    query = wp_config.get("kep_kulcsszo", "news")

    # 2. Pexels
    if pexels_key:
        try:
            encoded = urllib.parse.quote(query)
            url = f"https://api.pexels.com/v1/search?query={encoded}&per_page=3&orientation=landscape"
            req = urllib.request.Request(url, headers={"Authorization": pexels_key})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                photos = data.get("photos", [])
                if photos:
                    photo = photos[0]
                    img_url = photo["src"]["large2x"]
                    photographer = photo.get("photographer", "Pexels")
                    photo_url = photo.get("url", "https://www.pexels.com")
                    attribution = f'Fotó: <a href="{photo_url}">{photographer}</a> / Pexels'
                    print(f"Pexels kép: {img_url[:60]}...")
                    return img_url, attribution
        except Exception as e:
            print(f"Pexels hiba: {e}")

    # 3. Unsplash
    if unsplash_key:
        try:
            encoded = urllib.parse.quote(query)
            url = f"https://api.unsplash.com/search/photos?query={encoded}&per_page=3&orientation=landscape"
            req = urllib.request.Request(url, headers={"Authorization": f"Client-ID {unsplash_key}"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
                results = data.get("results", [])
                if results:
                    photo = results[0]
                    img_url = photo["urls"]["regular"]
                    photographer = photo["user"]["name"]
                    photo_url = photo["links"]["html"]
                    attribution = f'Fotó: <a href="{photo_url}">{photographer}</a> / Unsplash'
                    print(f"Unsplash kép: {img_url[:60]}...")
                    return img_url, attribution
        except Exception as e:
            print(f"Unsplash hiba: {e}")

    print("Nincs elérhető kép – kép nélkül tölt fel")
    return None, None


def upload_image_to_wp(img_url, wp_url, auth, alt_text="", is_fixed_url=False):
    """
    Képet tölt fel a WordPress médiatárba.
    Ha fix URL, letölti majd feltölti.
    Visszatér: media_id vagy None
    """
    try:
        req = urllib.request.Request(img_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            image_data = resp.read()
            content_type = resp.headers.get("Content-Type", "image/jpeg")

        filename = f"hirek-{datetime.date.today().strftime('%Y%m%d')}.jpg"
        cred = base64.b64encode(f"{auth['user']}:{auth['password']}".encode()).decode()

        upload_req = urllib.request.Request(
            f"{wp_url}/wp-json/wp/v2/media",
            data=image_data, method="POST",
            headers={
                "Authorization": f"Basic {cred}",
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Type": content_type,
            }
        )
        with urllib.request.urlopen(upload_req, timeout=30) as resp:
            media_data = json.loads(resp.read().decode())
            media_id = media_data.get("id")
            if media_id and alt_text:
                api_request(f"{wp_url}/wp-json/wp/v2/media/{media_id}",
                           method="POST", data={"alt_text": alt_text}, auth=auth)
            print(f"Kép feltöltve, media ID: {media_id}")
            return media_id
    except Exception as e:
        print(f"Kép feltöltési hiba: {e}")
        return None


# ================================================================
# WP KATEGÓRIA / TAG KEZELÉS
# ================================================================

def get_or_create_term(wp_url, auth, taxonomy, name):
    """Megkeres vagy létrehoz egy kategóriát/taget."""
    if not name:
        return None
    encoded = urllib.parse.quote(name)
    result, _ = api_request(f"{wp_url}/wp-json/wp/v2/{taxonomy}?search={encoded}", auth=auth)
    if result:
        for term in result:
            if term.get("name", "").lower() == name.lower():
                return term["id"]
    result, _ = api_request(f"{wp_url}/wp-json/wp/v2/{taxonomy}", method="POST",
                            data={"name": name, "slug": slugify(name)}, auth=auth)
    if result and result.get("id"):
        print(f"Új {taxonomy}: '{name}' (ID: {result['id']})")
        return result["id"]
    return None


def get_author_id(wp_url, auth, author_name):
    """Megkeresi a szerző ID-ját."""
    if not author_name:
        return None
    result, _ = api_request(
        f"{wp_url}/wp-json/wp/v2/users?search={urllib.parse.quote(author_name)}", auth=auth)
    if result and len(result) > 0:
        return result[0]["id"]
    return None


# ================================================================
# HTML TARTALOM GENERÁLÁS
# ================================================================

def generate_summary_html(news_json, attribution=""):
    """
    Összefoglaló post HTML-je (1 post = minden hír).
    ITE.hu stílusú: 1 kép felül, majd hírek egymás után.
    """
    news_items = news_json.get("news", [])
    summary = news_json.get("summary", "")

    html = f"""<!-- wp:paragraph {{"className":"lead-summary"}} -->
<p><strong>{summary}</strong></p>
<!-- /wp:paragraph -->

<!-- wp:separator -->
<hr class="wp-block-separator"/>
<!-- /wp:separator -->

"""
    for i, item in enumerate(news_items, 1):
        title   = item.get("title", "")
        date_str = item.get("date", "")
        src_sum = item.get("summary", "")
        details = item.get("details", "")
        pv      = item.get("personal_value", "")
        source  = item.get("source", "Forrás")
        url     = item.get("url", "#")

        # Forrás + dátum sor
        source_date = source
        if date_str:
            source_date += f" · {date_str}"

        html += f"""<!-- wp:heading {{"level":3}} -->
<h3>{i}. {title}</h3>
<!-- /wp:heading -->

<!-- wp:paragraph {{"className":"source-line"}} -->
<p><em>📅 {source_date}</em></p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>{src_sum}</p>
<!-- /wp:paragraph -->
"""
        if details:
            html += f"""<!-- wp:paragraph -->
<p>{details}</p>
<!-- /wp:paragraph -->
"""
        if pv:
            html += f"""<!-- wp:paragraph {{"className":"personal-value"}} -->
<p>💡 <strong>Miért érdekes és mi a haszna neked?</strong> {pv}</p>
<!-- /wp:paragraph -->
"""
        html += f"""<!-- wp:paragraph -->
<p>🔗 <a href="{url}" target="_blank" rel="noopener nofollow">{source}</a></p>
<!-- /wp:paragraph -->

<!-- wp:separator {{"className":"is-style-wide"}} -->
<hr class="wp-block-separator is-style-wide"/>
<!-- /wp:separator -->

"""
    if attribution:
        html += f"""<!-- wp:paragraph {{"className":"photo-credit"}} -->
<p><small><em>{attribution}</em></small></p>
<!-- /wp:paragraph -->
"""
    return html


def generate_individual_html(item, attribution=""):
    """Egyedi post HTML-je (1 hír = 1 post)."""
    date_str    = item.get("date", "")
    src_sum     = item.get("summary", "")
    details     = item.get("details", "")
    pv          = item.get("personal_value", "")
    source      = item.get("source", "Forrás")
    url         = item.get("url", "#")

    source_date = source
    if date_str:
        source_date += f" · {date_str}"

    html = f"""<!-- wp:paragraph {{"className":"source-line"}} -->
<p><em>📅 {source_date}</em></p>
<!-- /wp:paragraph -->

<!-- wp:paragraph -->
<p>{src_sum}</p>
<!-- /wp:paragraph -->
"""
    if details:
        html += f"""<!-- wp:paragraph -->
<p>{details}</p>
<!-- /wp:paragraph -->
"""
    if pv:
        html += f"""<!-- wp:paragraph {{"className":"personal-value"}} -->
<p>💡 <strong>Miért érdekes és mi a haszna neked?</strong> {pv}</p>
<!-- /wp:paragraph -->
"""
    html += f"""<!-- wp:paragraph -->
<p>📰 Forrás: <a href="{url}" target="_blank" rel="noopener nofollow">{source}</a></p>
<!-- /wp:paragraph -->
"""
    if attribution:
        html += f"""<!-- wp:paragraph {{"className":"photo-credit"}} -->
<p><small><em>{attribution}</em></small></p>
<!-- /wp:paragraph -->
"""
    return html


# ================================================================
# FŐ FELTÖLTŐ FÜGGVÉNY
# ================================================================

def upload_to_wordpress(news_json, wp_config, pexels_key, unsplash_key,
                        tema_kulcs, oldal_cim):
    """
    Feltölti a híreket egy WordPress oldalra.
    post_mode: summary / individual / append
    """
    wp_url      = wp_config["url"].rstrip("/")
    auth        = {"user": wp_config["user"], "password": wp_config["app_password"]}
    post_status = wp_config.get("post_status", "publish")
    post_mode   = wp_config.get("post_mode", "summary")
    kategoria   = wp_config.get("kategoria", "")
    szerzo      = wp_config.get("szerzo", "")
    today       = news_json.get("date", datetime.date.today().strftime("%Y. %m. %d."))
    news_items  = news_json.get("news", [])

    print(f"\n{'─'*50}")
    print(f"WP: {wp_url} | mód: {post_mode} | státusz: {post_status}")
    print(f"{'─'*50}")

    # Szerző és kategória
    author_id   = get_author_id(wp_url, auth, szerzo) if szerzo else None
    category_id = get_or_create_term(wp_url, auth, "categories", kategoria) if kategoria else None

    # Kép lekérése (1 kép az egész posthoz)
    img_url, attribution = get_image(wp_config, pexels_key, unsplash_key)
    media_id = None
    if img_url:
        alt_text = f"{oldal_cim} – {today}"
        media_id = upload_image_to_wp(img_url, wp_url, auth, alt_text,
                                      is_fixed_url=bool(wp_config.get("kep_url")))

    # ============================================================
    # MÓD: SUMMARY (1 összefoglaló post)
    # ============================================================
    if post_mode == "summary":
        post_title = f"{oldal_cim} – {today}"
        post_slug  = slugify(f"{tema_kulcs}-hirek-{today.replace('. ','-').replace('.','')}")
        meta_title = generate_seo_title(post_title)
        meta_desc  = generate_meta_description(news_json.get("summary", ""))
        content    = generate_summary_html(news_json, attribution)

        tag_ids = []
        for kat in list(set(i.get("category","") for i in news_items if i.get("category")))[:5]:
            tid = get_or_create_term(wp_url, auth, "tags", kat)
            if tid:
                tag_ids.append(tid)

        schema = {
            "@context":"https://schema.org","@type":"NewsArticle",
            "headline": post_title, "description": meta_desc,
            "datePublished": datetime.date.today().isoformat(),
            "dateModified":  datetime.date.today().isoformat(),
            "author": {"@type":"Organization","name": oldal_cim},
        }

        post_data = {
            "title": post_title, "slug": post_slug,
            "content": content, "status": post_status,
            "meta": {
                "rank_math_title":       meta_title,
                "rank_math_description": meta_desc,
                "rank_math_canonical_url": f"{wp_url}/{post_slug}/",
                "rank_math_schema_NewsArticle": json.dumps(schema),
            }
        }
        if media_id:    post_data["featured_media"] = media_id
        if category_id: post_data["categories"] = [category_id]
        if tag_ids:     post_data["tags"] = tag_ids
        if author_id:   post_data["author"] = author_id

        result, status = api_request(f"{wp_url}/wp-json/wp/v2/posts",
                                     method="POST", data=post_data, auth=auth)
        if result and result.get("id"):
            print(f"✅ Summary post: ID={result['id']} | {result.get('link','')}")
            return [result["id"]]
        else:
            print(f"❌ Summary post hiba! Státusz: {status}")
            return []

    # ============================================================
    # MÓD: INDIVIDUAL (minden hír külön post)
    # ============================================================
    elif post_mode == "individual":
        uploaded = []
        for i, item in enumerate(news_items, 1):
            title      = item.get("title", f"Hír #{i}")
            item_date  = item.get("date", "")
            post_slug  = slugify(title)
            meta_title = generate_seo_title(title)
            meta_desc  = generate_meta_description(
                item.get("summary",""), item.get("details",""))
            content    = generate_individual_html(item, attribution if i==1 else "")

            tag_ids = []
            if item.get("category"):
                tid = get_or_create_term(wp_url, auth, "tags", item["category"])
                if tid: tag_ids.append(tid)

            schema = {
                "@context":"https://schema.org","@type":"NewsArticle",
                "headline": title, "description": meta_desc,
                "datePublished": item_date or datetime.date.today().isoformat(),
                "author": {"@type":"Organization","name": oldal_cim},
            }

            post_data = {
                "title": title, "slug": post_slug,
                "content": content, "status": post_status,
                "meta": {
                    "rank_math_title":       meta_title,
                    "rank_math_description": meta_desc,
                    "rank_math_canonical_url": f"{wp_url}/{post_slug}/",
                    "rank_math_schema_NewsArticle": json.dumps(schema),
                }
            }
            if media_id:    post_data["featured_media"] = media_id
            if category_id: post_data["categories"] = [category_id]
            if tag_ids:     post_data["tags"] = tag_ids
            if author_id:   post_data["author"] = author_id

            result, status = api_request(f"{wp_url}/wp-json/wp/v2/posts",
                                         method="POST", data=post_data, auth=auth)
            if result and result.get("id"):
                print(f"✅ [{i}/{len(news_items)}] ID={result['id']} | {title[:40]}")
                uploaded.append(result["id"])
            else:
                print(f"❌ [{i}/{len(news_items)}] Hiba | {title[:40]}")

        print(f"Feltöltve: {len(uploaded)}/{len(news_items)}")
        return uploaded

    # ============================================================
    # MÓD: APPEND (hozzáfűz a mai napra szóló posthoz)
    # ============================================================
    elif post_mode == "append":
        # Megkeresi a mai napra már létező postot
        today_iso = datetime.date.today().isoformat()
        search_title = f"{oldal_cim} – {today}"

        result, _ = api_request(
            f"{wp_url}/wp-json/wp/v2/posts?search={urllib.parse.quote(search_title)}&per_page=5",
            auth=auth)

        existing_post = None
        if result:
            for p in result:
                if today_iso in p.get("date","") or today in p.get("title",{}).get("rendered",""):
                    existing_post = p
                    break

        # Új hírek HTML-je
        new_content = generate_summary_html(news_json, attribution)

        if existing_post:
            # Hozzáfűzés: az új hírek a TETEJÉRE kerülnek
            existing_content = existing_post.get("content",{}).get("rendered","")
            merged_content = new_content + "\n" + existing_content

            result, status = api_request(
                f"{wp_url}/wp-json/wp/v2/posts/{existing_post['id']}",
                method="POST",
                data={"content": merged_content, "date_gmt": None},
                auth=auth)

            if result and result.get("id"):
                print(f"✅ Append: ID={existing_post['id']} – {len(news_items)} hír hozzáfűzve")
                return [existing_post["id"]]
            else:
                print(f"❌ Append hiba! Státusz: {status}")
                return []
        else:
            # Nincs mai post még – létrehozzuk
            post_slug  = slugify(f"{tema_kulcs}-hirek-{today_iso}")
            meta_title = generate_seo_title(search_title)
            meta_desc  = generate_meta_description(news_json.get("summary",""))

            post_data = {
                "title": search_title, "slug": post_slug,
                "content": new_content, "status": post_status,
                "meta": {
                    "rank_math_title":       meta_title,
                    "rank_math_description": meta_desc,
                    "rank_math_canonical_url": f"{wp_url}/{post_slug}/",
                }
            }
            if media_id:    post_data["featured_media"] = media_id
            if category_id: post_data["categories"] = [category_id]
            if author_id:   post_data["author"] = author_id

            result, status = api_request(f"{wp_url}/wp-json/wp/v2/posts",
                                         method="POST", data=post_data, auth=auth)
            if result and result.get("id"):
                print(f"✅ Append (új post): ID={result['id']}")
                return [result["id"]]
            else:
                print(f"❌ Append új post hiba! Státusz: {status}")
                return []

    else:
        print(f"Ismeretlen post_mode: {post_mode}")
        return []
