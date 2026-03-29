#!/usr/bin/env python3
"""
SwissArmyPDF Test-Skript – Surgical Replacement (Seiten & XREFs)
"""

import argparse
import fitz
from pathlib import Path
from PIL import Image
import io
import sys


def parse_range(s: str) -> list[int]:
    """Parse '1,3-5,7' → [1,3,4,5,7]"""
    result = []
    for part in s.split(','):
        if '-' in part:
            start, end = map(int, part.split('-'))
            result.extend(range(start, end + 1))
        else:
            result.append(int(part))
    return result


def replace_pages(input_path: str, output_path: str, pages: list[int], dpi: int, quality: int, target_format: str):
    """Ersetzt ausgewählte Seiten durch reine JPG/PNG-Seiten."""
    if target_format.lower() not in ('jpg', 'jpeg', 'png'):
        raise ValueError("Target format muss 'jpg' oder 'png' sein")

    doc = fitz.open(input_path)
    new_doc = fitz.open()

    original_size = Path(input_path).stat().st_size
    print(f"[INFO] Original-Größe: {original_size / 1024:.1f} KB")

    for page_num in range(len(doc)):
        page = doc[page_num]

        if page_num + 1 in pages:  # 1-basiert
            print(f"[INFO] Ersetze Seite {page_num+1} → reine {target_format.upper()}-Seite ({dpi} DPI, Q={quality})")

            # Seite als Pixmap rendern (Ziel-DPI)
            zoom = dpi / 72.0
            pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))

            # In PIL laden
            img_bytes = pix.tobytes("png")  # erstmal PNG, später formatabhängig
            img = Image.open(io.BytesIO(img_bytes))

            # Format-spezifisch speichern
            buffer = io.BytesIO()
            if target_format.lower() in ('jpg', 'jpeg'):
                img.save(buffer, format="JPEG", quality=quality, optimize=True)
            else:
                img.save(buffer, format=target_format.upper(), quality=quality)

            new_bytes = buffer.getvalue()

            # Neue Seite erstellen und Bild einfügen
            new_page = new_doc.new_page(width=page.rect.width, height=page.rect.height)
            new_page.insert_image(new_page.rect, stream=new_bytes)
        else:
            # Seite unverändert kopieren
            new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)

    new_doc.save(output_path, garbage=4, clean=True, deflate=True)
    new_doc.close()
    doc.close()

    new_size = Path(output_path).stat().st_size
    print(f"[DONE] Neue Größe: {new_size / 1024:.1f} KB ({(new_size - original_size) / original_size * 100:.1f} %)")
    if new_size < original_size:
        print("[SUCCESS] Datei wurde kleiner!")
    else:
        print("[WARNING] Datei wurde nicht kleiner – Optimierung prüfen.")


def replace_xrefs(input_path: str, output_path: str, xrefs: list[int], dpi: int, quality: int, target_format: str):
    """Layer-Technik: Bilder-Layer + Text-Layer + Merge."""
    if target_format.lower() not in ('jpg', 'jpeg', 'png'):
        raise ValueError("Target format muss 'jpg', 'jpeg' oder 'png' sein")

    doc = fitz.open(input_path)
    new_doc = fitz.open()

    original_size = Path(input_path).stat().st_size
    print(f"[INFO] Original-Größe: {original_size / 1024:.1f} KB")

    for page_num in range(len(doc)):
        page = doc[page_num]
        images = page.get_images(full=True)

        page_xrefs = [img[0] for img in images]
        to_replace = [x for x in page_xrefs if x in xrefs]

        if to_replace:
            print(f"[INFO] Bearbeite Seite {page_num+1} – {len(to_replace)} Bilder ersetzen")

            # 1. Text-Layer: Original-Seite kopieren und Bilder entfernen
            temp_doc = fitz.open()
            temp_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)
            temp_page = temp_doc[0]

            # Bilder auf Temp-Seite "entfernen" (durch Bereinigung)
            for img in temp_page.get_images(full=True):
                xref = img[0]
                if xref in to_replace:
                    try:
                        temp_page.clean_contents()  # Bereinigt alte Streams
                    except:
                        pass

            # 2. Bilder-Layer: Seite rendern und nur gewünschte Bilder skalieren
            pix = page.get_pixmap(dpi=300)
            img_pil = Image.open(io.BytesIO(pix.tobytes("png")))

            for img in images:
                xref = img[0]
                if xref not in to_replace:
                    continue

                rects = page.get_image_rects(xref)
                if not rects:
                    continue
                rect = rects[0]

                base = doc.extract_image(xref)
                if base:
                    old_img = Image.open(io.BytesIO(base["image"]))

                    dpi_orig = 300
                    try:
                        dpi_w = old_img.width / (rect.width / 72)
                        dpi_h = old_img.height / (rect.height / 72)
                        dpi_orig = round((dpi_w + dpi_h) / 2)
                    except:
                        pass

                    scale = dpi / dpi_orig
                    if scale < 1:
                        new_size = (int(old_img.width * scale), int(old_img.height * scale))
                        old_img = old_img.resize(new_size, Image.Resampling.LANCZOS)
                        print(f"[INFO] XREF {xref} downsampled: {dpi_orig} → {dpi} DPI")

                    buffer = io.BytesIO()
                    save_format = 'JPEG' if target_format.lower() in ('jpg', 'jpeg') else target_format.upper()
                    save_kwargs = {'quality': quality, 'optimize': True} if save_format == 'JPEG' else {}
                    old_img.save(buffer, format=save_format, **save_kwargs)

                    # Paste auf Bilder-Layer
                    img_pil.paste(old_img, (int(rect.x0), int(rect.y0)))

            # 3. Bilder-Layer speichern
            buffer = io.BytesIO()
            save_format = 'JPEG' if target_format.lower() in ('jpg', 'jpeg') else target_format.upper()
            save_kwargs = {'quality': quality, 'optimize': True} if save_format == 'JPEG' else {}
            img_pil.save(buffer, format=save_format, **save_kwargs)

            # 4. Neue Seite erstellen
            new_page = new_doc.new_page(width=page.rect.width, height=page.rect.height)

            # 5. Bilder-Layer einfügen
            new_page.insert_image(new_page.rect, stream=buffer.getvalue())

            # 6. Text-Layer darüber einfügen
            new_doc.insert_pdf(temp_doc, from_page=0, to_page=0)
            temp_doc.close()

        else:
            new_doc.insert_pdf(doc, from_page=page_num, to_page=page_num)

    new_doc.save(output_path, garbage=4, clean=True, deflate=True)
    new_doc.close()
    doc.close()

    new_size = Path(output_path).stat().st_size
    print(f"[DONE] Neue Größe: {new_size / 1024:.1f} KB ({(new_size - original_size) / original_size * 100:.1f} %)")
    if new_size < original_size:
        print("[SUCCESS] Datei wurde kleiner!")
    else:
        print("[WARNING] Datei wurde nicht kleiner.")

def main():
    parser = argparse.ArgumentParser(description="SwissArmyPDF Test-Skript - Replace Pages or XREFs")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # replace-pages
    p = subparsers.add_parser("replace-pages")
    p.add_argument("input", type=str)
    p.add_argument("output", type=str)
    p.add_argument("--pages", type=str, required=True, help="z.B. 1,3-5,7")
    p.add_argument("--dpi", type=int, default=100)
    p.add_argument("--quality", type=int, default=75)
    p.add_argument("--format", type=str, default="jpg", choices=["jpg", "png"], help="Zielformat")

    # replace-xref
    p = subparsers.add_parser("replace-xref")
    p.add_argument("input", type=str)
    p.add_argument("output", type=str)
    p.add_argument("--xrefs", type=str, required=True, help="z.B. 17,23,45")
    p.add_argument("--dpi", type=int, default=100)
    p.add_argument("--quality", type=int, default=75)
    p.add_argument("--format", type=str, default="jpg", choices=["jpg", "png"], help="Zielformat")

    args = parser.parse_args()

    pages_or_xrefs = parse_range(args.pages if hasattr(args, 'pages') else args.xrefs)

    if args.command == "replace-pages":
        replace_pages(args.input, args.output, pages_or_xrefs, args.dpi, args.quality, args.format)
    elif args.command == "replace-xref":
        replace_xrefs(args.input, args.output, pages_or_xrefs, args.dpi, args.quality, args.format)


if __name__ == "__main__":
    main()