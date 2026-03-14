# WordPress Integráció - Beállítási Útmutató

## Szükséges lépések (egyszer kell elvégezni)

---

### 1. WordPress Application Password létrehozása

Az Application Password egy speciális jelszó amit csak az API-hoz használunk.
**Nem a rendes WP jelszavad!**

1. Menj a WP Adminba → **Felhasználók → Profil**
2. Görgess le az **"Application Passwords"** szekcióhoz
3. "New Application Password Name" mezőbe írj: `Hirek Bot`
4. Kattints: **"Add New Application Password"**
5. **MÁSOLD KI az egyszeri jelszót** (pl. `xxxx xxxx xxxx xxxx xxxx xxxx`)
6. Ezt a jelszót rakod a GitHub Secrets-be

> ⚠️ Ha nem látod az Application Passwords szekciót:
> Settings → Permalinks → mentsd el → próbáld újra

---

### 2. GitHub Secrets beállítása

A GitHub Secrets biztonságosan tárolja az érzékeny adatokat.

1. Menj a GitHub repódra
2. **Settings → Secrets and variables → Actions**
3. Kattints: **"New repository secret"**
4. Add hozzá az alábbi secreteket:

| Secret neve | Értéke | Kötelező? |
|-------------|--------|-----------|
| `ANTHROPIC_API_KEY` | Claude API kulcs | ✅ Igen |
| `WP1_APP_PASSWORD` | 1. WP oldal App Password | Ha használod |
| `WP2_APP_PASSWORD` | 2. WP oldal App Password | Ha van 2. oldal |
| `PEXELS_API_KEY` | Pexels API kulcs | Ajánlott |
| `UNSPLASH_API_KEY` | Unsplash API kulcs | Ajánlott |

---

### 3. Pexels API kulcs (ingyenes)

1. Menj: https://www.pexels.com/api/
2. Kattints: **"Get Started"**
3. Regisztrálj (ingyenes)
4. Az API kulcsot add hozzá GitHub Secrets-hez: `PEXELS_API_KEY`

---

### 4. Unsplash API kulcs (ingyenes, de jóváhagyás kell)

1. Menj: https://unsplash.com/developers
2. Kattints: **"Register as a developer"**
3. Hozz létre egy új alkalmazást
4. Az "Access Key"-t add hozzá: `UNSPLASH_API_KEY`
5. ⚠️ Demo módban 50 kérés/óra – bőven elég napi/heti futáshoz

---

### 5. RankMath beállítása WordPress-ben

A script automatikusan beállítja a RankMath SEO mezőket.
Nem kell külön semmit konfigurálni, de ellenőrizd:

1. RankMath telepítve és aktiválva legyen
2. **RankMath → Általános beállítások → REST API** legyen engedélyezve

---

### 6. config.txt frissítése

Nyisd meg a `config.txt` fájlt a repóban és távolítsd el a `#` karaktert
a WP beállítások elől, majd töltsd ki az adatokat:

```
config | wp1_url          | https://sajatoldalad.hu
config | wp1_user         | admin
config | wp1_post_status  | publish
config | wp1_post_mode    | summary
config | wp1_kategoria    | AI Hírek
config | wp1_szerzo       | Admin
config | wp1_kep_kulcsszo | artificial intelligence
```

---

### 7. Tesztelés

1. Menj az **Actions** fülre
2. Kattints: **"Reggeli AI Hírek"**
3. Kattints: **"Run workflow"**
4. Nézd meg a logot – a WP feltöltés eredménye ott látható
5. Ellenőrizd a WP Admin → Posts szekcióban hogy megjelent-e

---

## Hibaelhárítás

**"401 Unauthorized"** → Rossz felhasználónév vagy App Password

**"404 Not Found"** → Rossz WP URL, vagy REST API ki van kapcsolva

**"Cannot find RankMath"** → RankMath nincs telepítve/aktiválva

**Nincs kép** → Ellenőrizd a PEXELS_API_KEY Secret-et

**Post nem jelenik meg** → Ellenőrizd a `wp1_post_status` értékét
