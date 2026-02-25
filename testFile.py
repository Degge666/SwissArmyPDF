import sys
import pikepdf
from pikepdf import Pdf, Name

def get_dpi(file_path, target_page):
    pdf = Pdf.open(file_path)
    page = pdf.pages[target_page - 1]
    
    print(f"\n--- Analyse Seite {target_page} ---")
    
    # Durchsuche die Ressourcen der Seite nach Bildern
    if '/Resources' in page and '/XObject' in page.Resources:
        for name, xobj in page.Resources.XObject.items():
            if xobj.get('/Subtype') == '/Image':
                # Pixel-Maße des Bildes
                width_px = xobj.get('/Width')
                height_px = xobj.get('/Height')
                
                # Tatsächliche Maße auf der Seite (in Points, 1 Point = 1/72 Inch)
                # Wir suchen nach der MediaBox oder dem Image Rect
                # Vereinfacht nehmen wir die Standard-Seitengröße, falls das Bild füllend ist
                page_width_inch = float(page.MediaBox[2]) / 72
                page_height_inch = float(page.MediaBox[3]) / 72
                
                dpi_w = width_px / page_width_inch
                dpi_h = height_px / page_height_inch
                
                print(f"Bild gefunden: {width_px}x{height_px} Pixel")
                print(f"Effektive Auflösung: ~{int(dpi_w)}x{int(dpi_h)} DPI")
                
                if dpi_w > 300:
                    print("-> Tipp: Die Auflösung ist recht hoch. 150 DPI reichen oft.")
    else:
        print("Keine eingebetteten Bilder auf dieser Seite gefunden.")

if __name__ == "__main__":
    path = sys.argv[1]
    page_num = int(sys.argv[2])
    get_dpi(path, page_num)
