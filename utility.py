import io
from PIL import Image


def get_bpp_color(bpp):
    """Gibt den bpp-Wert als formatierten String zurück (Rot wenn < 1.0)."""
    color_red = "\033[91m"
    color_reset = "\033[0m"

    if bpp < 1.0:
        return f"{color_red}{bpp:4.2f}{color_reset}"
    return f"{bpp:4.2f}"

def calculate_bpp(width, height, data_size_bytes):
    """Berechnet Bits per Pixel."""
    if width == 0 or height == 0:
        return 0
    total_bits = data_size_bytes * 8
    return total_bits / (width * height)

def analyze_compression(img_bytes, width, height, img_format):
    """Analysiert die Kompression eines Bildes.
    Berechnet bpp und versucht bei JPEGs die Qualitätsstufe zu schätzen."""
    # 1. BPP Berechnung (immer verfügbar)
    if width > 0 and height > 0:
        bpp = (len(img_bytes) * 8) / (width * height)
    else:
        bpp = 0

    quality_str = "-" # Default, falls keine Schätzung möglich

    # 2. JPEG Qualitäts-Schätzung (Deep Dive)
    if img_format == "JPEG":
        try:
            # Wir laden die Bytes in Pillow
            img_io = io.BytesIO(img_bytes)
            with Image.open(img_io) as img:
                # Pillow extrahiert bei JPEGs oft die Quantisierungstabellen
                # Eine Schätzung der Qualität basiert auf diesen Tabellen
                # 'quantization' ist ein Dictionary
                # In utility.py -> analyze_compression
                if hasattr(img, "quantization"):
                    q_tables = img.quantization
                    if q_tables:
                        first_table = q_tables[0]
                        avg_q = sum(first_table) / len(first_table)
                        est_quality = int(max(0, min(100, 100 - (avg_q - 2) * 2)))

                        # FIX: Wenn die Schätzung 0 ergibt oder unplausibel ist
                        quality_str = f"{est_quality}%" if est_quality > 0 else "n/a"
                    else:
                        quality_str = "n/a"
        except:
            quality_str = "err"

    return f"{quality_str};≈{bpp:.2f}"