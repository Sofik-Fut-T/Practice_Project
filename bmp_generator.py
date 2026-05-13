"""
core/bmp_generator.py — генерація 24-бітних BMP-файлів
  3 методи: Мандельброт, Плазма, Концентричні хвилі
  3 палітри: Веселка, Вогонь, Океан
"""
import struct
import math


# ════════════════════════════════════════════════
#   КОЛЬОРОВІ ПАЛІТРИ
# ════════════════════════════════════════════════

def palette_rainbow(t: float) -> tuple:
    """RGB-веселка через синуси, t ∈ [0, 1]"""
    r = int(abs(math.sin(t * math.pi))              * 255)
    g = int(abs(math.sin(t * math.pi + 2.094))      * 255)
    b = int(abs(math.sin(t * math.pi + 4.189))      * 255)
    return (r, g, b)


def palette_fire(t: float) -> tuple:
    """Вогняна палітра (чорний→червоний→жовтий→білий)"""
    if t < 0.33:
        s = t / 0.33
        return (int(s * 255), 0, 0)
    elif t < 0.66:
        s = (t - 0.33) / 0.33
        return (255, int(s * 200), 0)
    else:
        s = (t - 0.66) / 0.34
        return (255, int(200 + s * 55), int(s * 200))


def palette_ocean(t: float) -> tuple:
    """Океанська палітра (темно-синій→блакитний→білий)"""
    if t < 0.5:
        s = t / 0.5
        return (0, int(s * 100), int(50 + s * 200))
    else:
        s = (t - 0.5) / 0.5
        return (int(s * 200), int(100 + s * 155), 255)


PALETTES = {
    "rainbow": ("🌈 Веселка",  palette_rainbow),
    "fire":    ("🔥 Вогонь",   palette_fire),
    "ocean":   ("🌊 Океан",    palette_ocean),
}


# ════════════════════════════════════════════════
#   МЕТОДИ ГЕНЕРАЦІЇ
# ════════════════════════════════════════════════

def method_mandelbrot(x: int, y: int, w: int, h: int, pal) -> tuple:
    """
    Метод 1 — Фрактал Мандельброта
    Колір залежить від швидкості виходу за межі кола радіуса 2.
    """
    MAX = 80
    cx = x / w * 3.5 - 2.5
    cy = y / h * 2.5 - 1.25
    zx = zy = 0.0
    for i in range(MAX):
        if zx * zx + zy * zy > 4.0:
            # Плавне забарвлення (smooth coloring)
            smooth = i - math.log2(math.log2(zx*zx + zy*zy + 1e-10))
            return pal(max(0.0, min(1.0, smooth / MAX)))
        zx, zy = zx*zx - zy*zy + cx, 2*zx*zy + cy
    return (0, 0, 0)


def method_plasma(x: int, y: int, w: int, h: int, pal) -> tuple:
    """
    Метод 2 — Плазмовий ефект
    Суперпозиція чотирьох синусоїд → органічний, психоделічний патерн.
    """
    v = (
        math.sin(x / 9.0) +
        math.sin(y / 9.0) +
        math.sin((x + y) / 12.0) +
        math.sin(math.sqrt(x * x + y * y + 1) / 7.0)
    )
    t = (v + 4.0) / 8.0  # нормалізація до [0, 1]
    return pal(t)


def method_waves(x: int, y: int, w: int, h: int, pal) -> tuple:
    """
    Метод 3 — Концентричні хвилі (кільця на воді)
    Колір залежить від відстані до центру зображення.
    """
    cx, cy = w / 2.0, h / 2.0
    dist = math.sqrt((x - cx) ** 2 + (y - cy) ** 2)
    t = (math.sin(dist / 7.0) + 1.0) / 2.0
    return pal(t)


METHODS = {
    "mandelbrot": ("🔮 Фрактал Мандельброта", method_mandelbrot),
    "plasma":     ("✨ Плазмовий ефект",       method_plasma),
    "waves":      ("💧 Концентричні хвилі",    method_waves),
}


# ════════════════════════════════════════════════
#   ЧИТАННЯ / ЗАПИС BMP
# ════════════════════════════════════════════════

def read_bmp_info(path: str) -> dict:
    """
    Зчитує заголовок BMP.
    Повертає: width, height (завжди > 0), raw_header (54 байти).
    Кидає ValueError якщо файл не є 24-бітним BMP.
    """
    with open(path, "rb") as f:
        hdr = f.read(54)

    if len(hdr) < 54 or hdr[:2] != b"BM":
        raise ValueError("Файл не є BMP.")

    bits = struct.unpack_from("<H", hdr, 28)[0]
    if bits != 24:
        raise ValueError(
            f"Підтримується лише 24-бітний BMP.\n"
            f"Обраний файл: {bits}-бітний."
        )

    w = struct.unpack_from("<i", hdr, 18)[0]
    h = struct.unpack_from("<i", hdr, 22)[0]
    return {"width": abs(w), "height": abs(h), "raw_header": bytearray(hdr)}


def generate_bmp(src: str, dst: str, method_key: str, palette_key: str):
    """
    Генерує новий BMP на основі розмірів src,
    зберігає у dst.
    """
    info = read_bmp_info(src)
    w, h = info["width"], info["height"]
    _, method_fn  = METHODS[method_key]
    _, palette_fn = PALETTES[palette_key]

    # BMP рядок вирівнюється до 4 байтів
    pad = (4 - (w * 3) % 4) % 4

    rows = []
    for y in range(h):
        row = bytearray()
        for x in range(w):
            r, g, b = method_fn(x, y, w, h, palette_fn)
            row += bytes([
                max(0, min(255, b)),
                max(0, min(255, g)),
                max(0, min(255, r)),
            ])  # BMP = BGR
        row += b"\x00" * pad
        rows.append(bytes(row))

    # BMP зберігається знизу вгору
    pixel_data = b"".join(reversed(rows))

    header = info["raw_header"]
    struct.pack_into("<I", header, 2,  54 + len(pixel_data))  # filesize
    struct.pack_into("<I", header, 34, len(pixel_data))        # imagesize
    # Виправляємо висоту на позитивне (bottom-up)
    struct.pack_into("<i", header, 22, h)

    with open(dst, "wb") as f:
        f.write(bytes(header))
        f.write(pixel_data)
