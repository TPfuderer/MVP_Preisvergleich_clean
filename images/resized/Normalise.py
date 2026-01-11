from pathlib import Path
from PIL import Image

# === Haupt-Images-Ordner ===
ROOT_DIR = Path(r"C:\Users\pfudi\PycharmProjects\MVP_Preisvergleich_clean\data\images")

# === Zielgröße für ALLE Bilder ===
FINAL_SIZE = (512, 512)
BG_COLOR = (255, 255, 255)  # weiß


def normalize_image(img_path: Path):
    """Bringt ein Bild auf FINAL_SIZE, ohne Abschneiden."""
    try:
        with Image.open(img_path) as img:
            img = img.convert("RGBA")

            # Skaliere mit korrektem Seitenverhältnis (contain)
            img.thumbnail(FINAL_SIZE, Image.LANCZOS)

            # Weiße Leinwand
            new_img = Image.new("RGBA", FINAL_SIZE, BG_COLOR + (255,))
            offset_x = (FINAL_SIZE[0] - img.width) // 2
            offset_y = (FINAL_SIZE[1] - img.height) // 2

            new_img.paste(img, (offset_x, offset_y), img)
            new_img = new_img.convert("RGB")

            # FIX: echte temporäre Datei erzeugen
            tmp = img_path.with_name(img_path.stem + "_tmp.jpg")
            new_img.save(tmp, "JPEG", quality=95)

            # Original sicher ersetzen
            tmp.replace(img_path)

            print(f"  ✓ {img_path.name}")

    except Exception as e:
        print(f"  ⚠ Fehler bei {img_path.name}: {e}")


def main():
    # Rekursive Suche aller Ordner
    all_dirs = [d for d in ROOT_DIR.rglob("*") if d.is_dir()]

    print(f"📁 {len(all_dirs)} Unterordner gefunden.")
    print("🔍 Scanne nach Bildordnern...\n")

    # Bild-Endungen
    exts = ("*.jpg", "*.jpeg", "*.png", "*.webp")

    for directory in all_dirs:
        # Sammle Bilder im Ordner
        images = []
        for ext in exts:
            images.extend(directory.glob(ext))

        # Nur Ordner mit Bildern verarbeiten
        if not images:
            continue

        print(f"📂 Ordner: {directory.relative_to(ROOT_DIR)} ({len(images)} Bilder)")

        for img_file in images:
            normalize_image(img_file)

        print()

    print("\n🎉 Fertig! Alle Bilder normalisiert auf", FINAL_SIZE)



if __name__ == "__main__":
    main()
