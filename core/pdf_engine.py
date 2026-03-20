# core/pdf_engine.py
import fitz
import hashlib
import sqlite3
import os
from pathlib import Path
from typing import Optional


class SwissArmyPDFEngine:
    def __init__(self, db_path="project_data.spdf"):
        self.db_path = db_path
        self.current_pdf = None
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # === VOLLES SCHEMA ===
            cursor.execute("""CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                path TEXT UNIQUE,
                parent_doc_id INTEGER,
                parent_path TEXT,
                color_hex TEXT,
                orphan INTEGER DEFAULT 0,
                aliases TEXT DEFAULT '[]',
                imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""")

            cursor.execute("""CREATE TABLE IF NOT EXISTS pages (
                id INTEGER PRIMARY KEY AUTOINCREMENT, doc_id INTEGER, page_num INTEGER
            )""")

            cursor.execute("""CREATE TABLE IF NOT EXISTS images (
                img_hash TEXT PRIMARY KEY, width INTEGER, height INTEGER, 
                filter TEXT, bpc INTEGER, colorspace TEXT, subsampling TEXT,
                object_type TEXT, has_alpha INTEGER DEFAULT 0,
                transparency_analyzed INTEGER DEFAULT 0,
                uses_transparency INTEGER DEFAULT 0
            )""")

            cursor.execute("""CREATE TABLE IF NOT EXISTS occurrences (
                id INTEGER PRIMARY KEY AUTOINCREMENT, doc_id INTEGER, page_id INTEGER, 
                img_hash TEXT, xref INTEGER, size_kb REAL, dpi TEXT
            )""")

            # Migration (sicher für alte DBs)
            cursor.execute("PRAGMA table_info(documents)")
            cols = [row[1] for row in cursor.fetchall()]
            for col in ["parent_doc_id", "parent_path", "color_hex", "orphan", "aliases"]:
                if col not in cols:
                    typ = "TEXT" if col in ("parent_path", "color_hex", "aliases") else "INTEGER"
                    cursor.execute(f"ALTER TABLE documents ADD COLUMN {col} {typ}")

            cursor.execute("UPDATE documents SET orphan = 0, aliases = '[]' WHERE orphan IS NULL")
            conn.commit()

    def run_full_scan(self, path: str, progress_callback=None, parent_doc_id: Optional[int] = None) -> int:
        """Scan a PDF file and register/update it in the database.

        If parent_doc_id is provided, the document is registered as derived from that parent.
        Uses INSERT OR REPLACE on path to handle re-scans gracefully.
        Returns the document ID or -1 on fatal error.
        """
        self.current_pdf = path

        try:
            doc = fitz.open(path)
        except Exception as e:
            print(f"Error opening PDF {path}: {e}")
            return -1

        total_pages = len(doc)

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # Check if document already exists
                cursor.execute("SELECT id FROM documents WHERE path = ?", (path,))
                row = cursor.fetchone()

                if row:
                    doc_id = row[0]
                    # Clear old analysis data before re-scanning
                    cursor.execute("DELETE FROM occurrences WHERE doc_id = ?", (doc_id,))
                    cursor.execute("DELETE FROM pages WHERE doc_id = ?", (doc_id,))
                else:
                    doc_id = None  # will be assigned after INSERT

                # Insert or replace document metadata
                # Check if document already exists
                cursor.execute("SELECT id FROM documents WHERE path = ?", (path,))
                row = cursor.fetchone()

                if row:
                    doc_id = row[0]
                    cursor.execute("DELETE FROM occurrences WHERE doc_id = ?", (doc_id,))
                    cursor.execute("DELETE FROM pages WHERE doc_id = ?", (doc_id,))
                else:
                    doc_id = None

                # Insert or replace
                cursor.execute("""
                            INSERT OR REPLACE INTO documents 
                            (name, path, parent_doc_id, parent_path, color_hex, orphan, aliases, imported_at)
                            VALUES (?, ?, ?, ?, ?, 0, '[]', CURRENT_TIMESTAMP)
                        """, (
                    Path(path).name,
                    path,
                    parent_doc_id,
                    None,
                    None
                ))

                if doc_id is None:
                    doc_id = cursor.lastrowid

                # ─── DEBUG ────────────────────────────────────────────────────────
                cursor.execute("SELECT parent_doc_id FROM documents WHERE id = ?", (doc_id,))
                after_parent = cursor.fetchone()[0]
                print(f"[DEBUG] Nach Scan gespeichert: doc_id={doc_id}, parent_doc_id={after_parent!r}")
                # ─────────────────────────────────────────────────────────────────

                # Jetzt Seiten und Bilder scannen...
                for page_num in range(total_pages):
                    page = doc[page_num]
                    cursor.execute("INSERT INTO pages (doc_id, page_num) VALUES (?, ?)",
                                   (doc_id, page_num + 1))
                    page_id = cursor.lastrowid

                    # DPI Infos der Seite vorab sammeln (optional, aber nützlich)
                    img_info_list = page.get_image_info()

                    for img in page.get_images():
                        xref = img[0]
                        base = doc.extract_image(xref)
                        if not base:
                            continue

                        img_data = base["image"]
                        img_size_bits = len(img_data) * 8
                        pixel_count = base["width"] * base["height"]
                        dynamic_bbp = round(img_size_bits / pixel_count, 2) if pixel_count > 0 else 0

                        h = hashlib.md5(img_data).hexdigest()

                        # Colorspace & Alpha-Logik (unverändert)
                        bpc_per_channel = base.get("bpc", 8)
                        raw_cs = base.get("colorspace", 0)
                        cs_map = {1: "Grayscale", 3: "RGB", 4: "CMYK"}

                        if isinstance(raw_cs, int):
                            cspace_text = cs_map.get(raw_cs, f"Other ({raw_cs} channels)")
                            num_channels = raw_cs
                        else:
                            cspace_text = str(raw_cs)
                            num_channels = 3

                        has_alpha = 1 if "alpha" in base or base.get("smask", 0) > 0 else 0
                        if has_alpha and "Alpha" not in cspace_text:
                            cspace_text += " + Alpha"

                        subsampling = self._get_chroma_subsampling(base)

                        # DPI-Berechnung V2.0 (unverändert)
                        dpi_str = "N/A"
                        try:
                            rect_list = page.get_image_rects(xref)
                            if rect_list:
                                r = rect_list[0]
                                w_inch = (r[2] - r[0]) / 72.0
                                h_inch = (r[3] - r[1]) / 72.0
                                if w_inch > 0.01 and h_inch > 0.01:
                                    dpi_w = base["width"] / w_inch
                                    dpi_h = base["height"] / h_inch
                                    dpi_val = round((dpi_w + dpi_h) / 2)
                                    if 10 <= dpi_val <= 2400:
                                        dpi_str = str(int(dpi_val))
                                    else:
                                        dpi_str = str(int(dpi_val)) + "?"
                        except:
                            pass

                        if dpi_str == "N/A":
                            # Fallback (unverändert)
                            for info in page.get_image_info():
                                if info.get('xref') == xref:
                                    bbox = info.get('bbox', (0, 0, 0, 0))
                                    w_inch = (bbox[2] - bbox[0]) / 72.0
                                    h_inch = (bbox[3] - bbox[1]) / 72.0
                                    if w_inch > 0.01 and h_inch > 0.01:
                                        dpi_val = round(((base["width"] / w_inch) + (base["height"] / h_inch)) / 2)
                                        if 10 <= dpi_val <= 2400:
                                            dpi_str = str(int(dpi_val))
                                    break

                        # Speichern
                        cursor.execute("""
                            INSERT OR IGNORE INTO images 
                            (img_hash, width, height, filter, bpc, colorspace, subsampling, object_type, has_alpha) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            h, base["width"], base["height"], base.get("ext", "Unknown").upper(),
                            dynamic_bbp, cspace_text, subsampling, "Image", has_alpha
                        ))

                        cursor.execute("""
                            INSERT INTO occurrences (doc_id, page_id, img_hash, xref, size_kb, dpi) 
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (
                            doc_id, page_id, h, xref, len(base["image"]) / 1024, dpi_str
                        ))

                    if progress_callback:
                        progress_callback(int(((page_num + 1) / total_pages) * 100))

                # WICHTIG: Dokument schließen VOR Commit
                doc.close()
                conn.commit()

            return doc_id

        except Exception as e:
            print(f"Database error during scan of {path}: {e}")
            doc.close()
            return -1

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