#!/usr/bin/env python3
"""
SwissArmyPDF Diagnose-Tool
Zeigt alle XREFs (Bilder) mit Position, DPI, Größe und Layer-Reihenfolge
"""

import fitz
import sys
from pathlib import Path

def diagnose_pdf(pdf_path: str, title: str = "PDF"):
    print(f"\n=== {title} === {pdf_path} ===")
    doc = fitz.open(pdf_path)

    for page_num in range(len(doc)):
        page = doc[page_num]
        page_rect = page.rect
        print(f"\nSeite {page_num+1:2d} | Größe: {page_rect.width:.1f} × {page_rect.height:.1f} pt")

        images = page.get_images(full=True)
        if not images:
            print("   Keine Bilder")
            continue

        for img in images:
            xref = img[0]
            base = doc.extract_image(xref)
            if not base:
                continue

            w, h = base["width"], base["height"]
            rects = page.get_image_rects(xref)
            rect = rects[0] if rects else None

            # DPI schätzen
            dpi = "N/A"
            if rect:
                try:
                    dpi_w = w / ((rect[2] - rect[0]) / 72)
                    dpi_h = h / ((rect[3] - rect[1]) / 72)
                    dpi = round((dpi_w + dpi_h) / 2)
                except:
                    pass

            print(f"   XREF {xref:3d} | {w:4d}×{h:4d}px | DPI ~{dpi:3} | "
                  f"Pos: ({rect.x0:.1f}, {rect.y0:.1f}) – ({rect.x1:.1f}, {rect.y1:.1f}) | "
                  f"Format: {base['ext'].upper()}")

    doc.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python diagnose_pdf.py <pdf1> [pdf2]")
        sys.exit(1)

    diagnose_pdf(sys.argv[1], "Original")

    if len(sys.argv) > 2:
        diagnose_pdf(sys.argv[2], "Target / Output")