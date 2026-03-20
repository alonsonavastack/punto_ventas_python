#!/usr/bin/env python3
"""Script standalone para generar logo_ascii.txt desde el logo actual."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

LOGO_DIR  = os.path.join("assets", "images")
LOGO_PATH = None
for ext in ("png", "jpg", "jpeg", "gif"):
    p = os.path.join(LOGO_DIR, f"logo.{ext}")
    if os.path.exists(p):
        LOGO_PATH = p; break

if not LOGO_PATH:
    print("[ERROR] No hay logo en assets/images/")
    sys.exit(1)

OUT_PATH = os.path.join(LOGO_DIR, "logo_ascii.txt")
COLS     = 42
FILAS    = 12
CHARS    = "@%#*+=-:. "

try:
    from PIL import Image
except ImportError:
    print("Instalando Pillow..."); os.system("pip install Pillow -q")
    from PIL import Image

img = Image.open(LOGO_PATH).convert("RGBA")
img = img.resize((COLS * 2, FILAS), Image.LANCZOS)
lineas = []
for y in range(FILAS):
    fila = ""
    for x in range(COLS * 2):
        r, g, b, a = img.getpixel((x, y))
        if a < 30:
            fila += " "
        else:
            lum = int(0.299*r + 0.587*g + 0.114*b)
            idx = int(lum / 255 * (len(CHARS) - 1))
            fila += CHARS[idx]
    lineas.append(fila[:COLS])

with open(OUT_PATH, "w", encoding="utf-8") as f:
    f.write("\n".join(lineas))

print(f"✅ Generado: {OUT_PATH}")
print("=" * COLS)
for l in lineas: print(l)
print("=" * COLS)
