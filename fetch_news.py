import datetime
import os

now = datetime.datetime.utcnow().strftime("%Y. %m. %d. %H:%M:%S UTC")

html = f"""<!DOCTYPE html>
<html lang="hu">
<head><meta charset="UTF-8"><title>Teszt</title></head>
<body style="background:#0a0a0f;color:#f0f0fa;font-family:sans-serif;padding:40px">
  <h1 style="color:#c8ff00">AI Hírek – Teszt</h1>
  <p>Utoljára frissítve: <strong style="color:#c8ff00">{now}</strong></p>
  <p>Ha ezt látod, a workflow és a deploy működik!</p>
</body>
</html>"""

os.makedirs("docs", exist_ok=True)
with open("docs/index.html", "w", encoding="utf-8") as f:
    f.write(html)

print(f"✅ Teszt oldal generálva: {now}")
