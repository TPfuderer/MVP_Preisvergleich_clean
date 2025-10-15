from pathlib import Path
from PIL import Image
import os

# 🔹 Pfade definieren
BASE_DIR = Path(r"C:\Users\pfudi\PycharmProjects\PythonProject\Application\images")
IMG_DIR = BASE_DIR / "originals"   # hier liegen deine neuen Bilder
OUT_DIR = BASE_DIR / "resized"     # hier speichert das Skript die verkleinerten Bilder
OUT_DIR.mkdir(exist_ok=True)

TARGET_SIZE = (400, 400)  # Zielgröße (Breite, Höhe)

# 🔄 Alle JPG- oder PNG-Bilder durchgehen
for img_path in IMG_DIR.glob("*.*"):
    if img_path.suffix.lower() not in [".jpg", ".jpeg", ".png"]:
        continue  # andere Dateitypen ignorieren

    out_path = OUT_DIR / (img_path.stem + ".jpg")  # immer als JPG speichern

    # ⏩ Überspringen, wenn resized-Version existiert und gleich alt oder neuer ist
    if out_path.exists() and os.path.getmtime(out_path) >= os.path.getmtime(img_path):
        print(f"⏩ Übersprungen: {img_path.name} (bereits aktuell)")
        continue

    try:
        # 🖼️ Bild laden und konvertieren
        img = Image.open(img_path).convert("RGB")
        img.thumbnail(TARGET_SIZE, Image.Resampling.LANCZOS)

        # 🧱 Weißes quadratisches Canvas für einheitliche Größe
        bg = Image.new("RGB", TARGET_SIZE, (255, 255, 255))
        offset = ((TARGET_SIZE[0] - img.width) // 2, (TARGET_SIZE[1] - img.height) // 2)
        bg.paste(img, offset)

        # 💾 Speichern
        bg.save(out_path, "JPEG", quality=90)
        print(f"✅ Neu resized: {img_path.name} → {out_path.name}")

    except Exception as e:
        print(f"❌ Fehler bei {img_path.name}: {e}")

print("\n🏁 Resize-Vorgang abgeschlossen.")

