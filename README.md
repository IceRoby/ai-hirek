# 🤖 AI Hírek - Automatikus Hírgyűjtő Rendszer

Automatikusan gyűjt és összefoglal híreket Claude AI segítségével,
majd feltölti GitHub Pages-re és WordPress oldalakra.

## Fájlok

| Fájl | Leírás |
|------|--------|
| `fetch_news.py` | Fő script - hírgyűjtés és HTML generálás |
| `wordpress_upload.py` | WordPress feltöltő modul |
| `config.txt` | Technikai beállítások |
| `topics.txt` | Témák és kulcsszavak |
| `categories.txt` | Kategóriák és WP hozzárendelés |
| `sources.txt` | RSS feedek és domainek |
| `wordpress.txt` | WordPress oldalak beállításai |
| `history.txt` | Futási előzmények (automatikusan frissül) |
| `docs/index.html` | Generált weboldal (automatikusan frissül) |
| `.github/workflows/daily-news.yml` | GitHub Actions ütemezés |

## Beállítás

Lásd: `SETUP.md` és `SETUP_WP.md`

## Szükséges GitHub Secrets

- `ANTHROPIC_API_KEY` - Claude API kulcs (kötelező)
- `PEXELS_API_KEY` - Pexels képek (opcionális)
- `UNSPLASH_API_KEY` - Unsplash képek (opcionális)
- `WP1_APP_PASSWORD` - WordPress 1. oldal (opcionális)
- `WP2_APP_PASSWORD` - WordPress 2. oldal (opcionális)
