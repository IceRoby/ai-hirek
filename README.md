# 🤖 Reggeli AI Hírek – Beállítási útmutató

## Amire szükséged lesz
- GitHub fiók (ingyenes): https://github.com
- Anthropic API kulcs (~$1 feltöltés elég hónapokra): https://platform.anthropic.com

---

## 1. lépés – GitHub repo létrehozása (5 perc)

1. Menj a https://github.com/new oldalra
2. Adj nevet: pl. `ai-hirek`
3. Legyen **Public** (ez kell a GitHub Pages-hez)
4. Kattints: **Create repository**

---

## 2. lépés – Fájlok feltöltése (5 perc)

Töltsd fel a következő fájlokat a repóba:

```
ai-hirek/
├── fetch_news.py                        ← a Python script
├── .github/
│   └── workflows/
│       └── daily-news.yml               ← az automatizmus
└── docs/
    └── index.html                       ← (ez automatikusan generálódik)
```

**Hogyan tölts fel fájlt GitHub-ra:**
1. A repó oldalán kattints: **Add file → Upload files**
2. Húzd fel a fájlokat
3. Kattints: **Commit changes**

> A `.github/workflows/` mappát kézzel kell létrehozni:
> Kattints **Add file → Create new file**, majd írd be: `.github/workflows/daily-news.yml`
> és illeszd be a tartalmát.

---

## 3. lépés – API kulcs beállítása (3 perc)

1. Menj: **Settings → Secrets and variables → Actions**
2. Kattints: **New repository secret**
3. Name: `ANTHROPIC_API_KEY`
4. Value: az Anthropic API kulcsod (pl. `sk-ant-...`)
5. Kattints: **Add secret**

---

## 4. lépés – GitHub Pages bekapcsolása (2 perc)

1. Menj: **Settings → Pages**
2. Source: **Deploy from a branch**
3. Branch: `main`, mappa: `/docs`
4. Kattints: **Save**

Néhány perc múlva a weboldalad elérhető lesz ezen a címen:
`https://[felhasználóneved].github.io/ai-hirek`

---

## 5. lépés – Első teszt futtatás (1 perc)

1. Menj: **Actions** fülre
2. Kattints: **Reggeli AI Hírek**
3. Kattints: **Run workflow → Run workflow**
4. Várd meg (~1-2 perc), majd nézd meg a weboldalt!

---

## ⏰ Időzítés

Az automatizmus **minden reggel 4:00 UTC-kor** fut (= 6:00 Budapest nyári idő, 5:00 téli idő).

Ha más időpontot szeretnél, a `daily-news.yml` fájlban módosítsd ezt a sort:
```yaml
- cron: '0 4 * * *'
```
Cron időpont generátor: https://crontab.guru

---

## 💰 Várható költség

| Elem | Ár |
|------|-----|
| GitHub Actions | Ingyenes |
| GitHub Pages | Ingyenes |
| Claude API (napi 1 hívás) | ~$0.01-0.05/nap |
| **Összesen/hó** | **~150-500 Ft** |

---

## ❓ Hibakeresés

**A workflow nem fut le:**
- Ellenőrizd az Actions fülön a hibaüzenetet
- Győződj meg róla, hogy az API kulcs helyesen van beállítva

**Az oldal nem frissül:**
- Ellenőrizd, hogy a `docs/` mappa létezik-e
- GitHub Pages beállításai rendben vannak-e

**API hiba:**
- Ellenőrizd az Anthropic fiókodban az egyenleget
- Az API kulcs érvényes-e
