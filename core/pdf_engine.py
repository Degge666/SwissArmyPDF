# core/pdf_engine.py
import fitz
import hashlib
import sqlite3
import os
from pathlib import Path


class SwissArmyPDFEngine:
    def __init__(self, db_path="project_data.spdf"):
        self.db_path = db_path
        self.current_pdf = None
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Erweitertes Dokumenten-Verzeichnis
            cursor.execute("""CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, path TEXT)""")

            cursor.execute("""CREATE TABLE IF NOT EXISTS pages (
                id INTEGER PRIMARY KEY AUTOINCREMENT, doc_id INTEGER, page_num INTEGER)""")

            # Die Image-Tabelle enthält nun alle forensischen Metadaten inkl. DPI
            cursor.execute("""CREATE TABLE IF NOT EXISTS images (
                img_hash TEXT PRIMARY KEY, 
                width INTEGER, height INTEGER, 
                filter TEXT, bpc INTEGER,
                colorspace TEXT, 
                subsampling TEXT,
                object_type TEXT,
                has_alpha INTEGER DEFAULT 0,
                transparency_analyzed INTEGER DEFAULT 0,
                uses_transparency INTEGER DEFAULT 0)""")

            cursor.execute("""CREATE TABLE IF NOT EXISTS occurrences (
                id INTEGER PRIMARY KEY AUTOINCREMENT, doc_id INTEGER, page_id INTEGER, 
                img_hash TEXT, xref INTEGER, size_kb REAL, dpi TEXT)""")
            conn.commit()

    def run_full_scan(self, path, progress_callback=None):
        self.current_pdf = path
        doc = fitz.open(path)
        total_pages = len(doc)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM documents WHERE path = ?", (path,))
            row = cursor.fetchone()

            if row:
                doc_id = row[0]
                cursor.execute("DELETE FROM occurrences WHERE doc_id = ?", (doc_id,))
                cursor.execute("DELETE FROM pages WHERE doc_id = ?", (doc_id,))
            else:
                cursor.execute("INSERT INTO documents (name, path) VALUES (?, ?)", (Path(path).name, path))
                doc_id = cursor.lastrowid

            for page_num in range(total_pages):
                page = doc[page_num]
                cursor.execute("INSERT INTO pages (doc_id, page_num) VALUES (?, ?)", (doc_id, page_num + 1))
                page_id = cursor.lastrowid

                # DPI Infos der Seite vorab sammeln
                img_info_list = page.get_image_info()

                for img in page.get_images():
                    xref = img[0]
                    base = doc.extract_image(xref)
                    if not base: continue

                    h = hashlib.md5(base["image"]).hexdigest()

                    # --- FIX START ---
                    # 1. Colorspace Mapping
                    raw_cs = base.get("colorspace", 0)
                    cs_map = {1: "Grayscale", 3: "RGB", 4: "CMYK"}
                    cspace = cs_map.get(raw_cs, f"Unknown ({raw_cs})")

                    # 2. Subsampling & Alpha
                    subsampling = self._get_chroma_subsampling(base)
                    # Hier lag der Fehler: Die Variable muss definiert sein!
                    has_alpha = 1 if "alpha" in base or base.get("smask", 0) > 0 else 0
                    # --- FIX END ---

                    # DPI Berechnung
                    dpi_str = "N/A"
                    for info in img_info_list:
                        if info.get('xref') == xref:
                            bbox = info['bbox']
                            w_in, h_in = (bbox[2] - bbox[0]) / 72, (bbox[3] - bbox[1]) / 72
                            if w_in > 0:
                                dpi_str = f"{round(base['width'] / w_in)}x{round(base['height'] / h_in)}"
                            break

                    cursor.execute("""
                                        INSERT OR IGNORE INTO images 
                                        (img_hash, width, height, filter, bpc, colorspace, subsampling, object_type, has_alpha) 
                                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                                    """, (h, base["width"], base["height"], base.get("filter", "None"),
                                          base.get("bpc", 8), cspace, subsampling, "Image", has_alpha))

                    cursor.execute("""
                                        INSERT INTO occurrences (doc_id, page_id, img_hash, xref, size_kb, dpi) 
                                        VALUES (?, ?, ?, ?, ?, ?)
                                    """, (doc_id, page_id, h, xref, len(base["image"]) / 1024, dpi_str))
                if progress_callback:
                    progress_callback(int(((page_num + 1) / total_pages) * 100))

            conn.commit()
            doc.close()
            return doc_id

    def _get_chroma_subsampling(self, base):
        # Wenn es kein JPG ist, ist die Info nicht applikabel
        if base["ext"].lower() not in ["jpg", "jpeg"]:
            return "N/A"

        # Versuche Sampling Faktoren zu finden
        # fitz liefert diese nicht standardmäßig im 'base' dict.
        # Ein '-' signalisiert: JPG vorhanden, aber Faktoren (noch) nicht extrahiert.
        samples = base.get("samples")  # Platzhalter für zukünftiges Header-Parsing
        if not samples:
            return "-"

        return str(samples)


    # --- Inspector Hilfsmethoden (REPARATUR) ---
    def get_page_preview(self, page_num, zoom=1.0):
        """Rendert eine PDF-Seite als Bild-Daten (PNG)."""
        if not self.current_pdf: return None
        try:
            doc = fitz.open(self.current_pdf)
            # Seite ist 1-basiert in der DB, aber 0-basiert in fitz
            page = doc[page_num - 1]
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            data = pix.tobytes("png")
            doc.close()
            return data
        except Exception as e:
            print(f"Error rendering page {page_num}: {e}")
            return None

    def get_pixmap(self, xref):
        """Extrahiert ein spezifisches Bild-Objekt via XREF."""
        if not self.current_pdf: return None
        try:
            doc = fitz.open(self.current_pdf)
            base = doc.extract_image(xref)
            doc.close()
            return base["image"] if base else None
        except Exception as e:
            print(f"Error extracting XREF {xref}: {e}")
            return None

    # Lazy-Analysis für Transparenz
    def analyze_transparency(self, img_hash):
        """Prüft, ob ein Bild mit Alpha-Kanal tatsächlich transparente Pixel nutzt."""
        # TODO: Implementierung mittels PIL oder numpy für Pixel-Scan
        pass