"""
core/steganography.py — LSB стеганографія для BMP
Алгоритм: кожен біт повідомлення → молодший біт байту пікселя.
Маркери HEADER/FOOTER для надійного пошуку.
"""
import struct

# 4-байтові маркери початку та кінця
_HEADER = b"\xAB\xCD\xEF\x01"
_FOOTER = b"\x01\xFE\xDC\xBA"


def _read_bmp_pixels(path: str) -> tuple:
    """Повертає (header_bytes, pixel_bytearray)."""
    with open(path, "rb") as f:
        raw = f.read()
    if len(raw) < 54 or raw[:2] != b"BM":
        raise ValueError("Файл не є BMP.")
    pixel_offset = struct.unpack_from("<I", raw, 10)[0]
    return raw[:pixel_offset], bytearray(raw[pixel_offset:])


def embed_message(src: str, dst: str, message: str):
    """
    Вкладає повідомлення у BMP-файл.
    src  — вихідний BMP
    dst  — куди зберегти результат
    """
    payload = _HEADER + message.encode("utf-8") + _FOOTER

    # Кожен байт → 8 бітів (старший спочатку)
    bits = []
    for byte in payload:
        for shift in range(7, -1, -1):
            bits.append((byte >> shift) & 1)

    header, pixels = _read_bmp_pixels(src)

    if len(bits) > len(pixels):
        raise ValueError(
            f"Повідомлення занадто велике для цього BMP!\n"
            f"Потрібно {len(bits)} байт пікселів, "
            f"доступно {len(pixels)}."
        )

    for i, bit in enumerate(bits):
        pixels[i] = (pixels[i] & 0xFE) | bit

    with open(dst, "wb") as f:
        f.write(header)
        f.write(pixels)


def extract_message(src: str) -> str:
    """
    Витягує повідомлення з BMP-файлу.
    Повертає порожній рядок якщо повідомлення не знайдено.
    """
    _, pixels = _read_bmp_pixels(src)

    # Збираємо байти з молодших бітів пікселів
    extracted = bytearray()
    acc = 0
    for i, px_byte in enumerate(pixels):
        bit = px_byte & 1
        acc = (acc << 1) | bit
        if (i + 1) % 8 == 0:
            extracted.append(acc)
            acc = 0

            # Перевіряємо чи вже є і заголовок і кінцівка
            if len(extracted) >= len(_HEADER) + len(_FOOTER):
                raw = bytes(extracted)
                start = raw.find(_HEADER)
                end   = raw.find(_FOOTER)
                if start != -1 and end != -1 and end > start:
                    payload = raw[start + len(_HEADER):end]
                    try:
                        return payload.decode("utf-8")
                    except UnicodeDecodeError:
                        return ""

    return ""
