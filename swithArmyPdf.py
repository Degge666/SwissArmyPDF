toolNameame = "SWISS ARMY PDF TOOLKIT"
sAPDFVString = "0.21 ⍺"
import fitz
import os
import subprocess
import sys
from utility import analyze_compression
from show_data_table import print_metadata_table, print_recon_master_table

def print_banner():
    print(f"\n--- ({toolNameame}) ({sAPDFVString}) ---")

def show_toolkit_intel():
    """Versions of installed libraries and tools of interest."""
    print(f"\n{'=' * 17} VERSION TABLE {'=' * 17}")

    # 1. PyMuPDF Info
    v_fitz = fitz.version[0] if hasattr(fitz, "version") else "Unknown"
    print(f"[+] PyMuPDF (fitz):       v{v_fitz}")

    # 2. Python Info
    v_python = sys.version.split()[0]
    print(f"[+] Python Core:          v{v_python}")

    # 3. OS Info
    import platform
    print(f"[+] Operating System:     {platform.system()} ({platform.release()})")

    # 4. Ghostscript Check (Externes Tool)
    try:
        # Versucht 'gs -v' oder 'gswin64c -v' aufzurufen
        gs_cmd = "gswin64c" if os.name == "nt" else "gs"
        gs_version = subprocess.check_output([gs_cmd, "--version"], stderr=subprocess.STDOUT).decode().strip()
        print(f"[+] Ghostscript:          v{gs_version}")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(f"[!] Ghostscript:          NOT FOUND (Heavy Strike will fail!)")

    print(f"{'=' * 49}")
    input("\nPress Enter to return to the command menu...")

def get_save_path(original_path, suffix):
    base, ext = os.path.splitext(original_path)
    suggested = f"{base}_{suffix}{ext}"
    print(f"\nTo save as: {suggested}")
    user_input = input("Press ENTER or give different File Name/Path: ").strip()

    if not user_input:
        return suggested

    # Pfad-Logic (File Namen or full path)
    if os.sep in user_input or "/" in user_input:
        return user_input.replace("'", "").replace('"', "").strip()
    else:
        directory = os.path.dirname(original_path)
        if not user_input.endswith(ext): user_input += ext
        return os.path.join(directory, user_input)

def print_target_report(filepath):
    """Zeigt nach einer Operation sofort die neuen Fakten an."""
    if not os.path.exists(filepath):
        return

    size_mb = os.path.getsize(filepath) / (1024 * 1024)
    print(f"\n{'=' * 60}")
    print(f"NEW TARGET ACQUIRED: {os.path.basename(filepath)}")
    print(f"TOTAL SIZE: {size_mb:.2f} MB")
    print(f"{'=' * 60}")
    scout_pdf(filepath)

def change_target(prompt="\nEnter path to PDF (or drag & drop): "):
    """Zentrale Funktion zum Wechseln der Zieldatei mit Validierung."""
    new_path = input(prompt).strip()
    # Bereinigung von Drag & Drop Artefakten
    new_path = new_path.replace("'", "").replace('"', "").strip()

    if not new_path:
        return None

    if os.path.exists(new_path):
        return new_path
    else:
        print(f"[!] Error: Path '{new_path}' does not exist.")
        return None

def export_pages_as_jpg(filepath):
    """Konvertiert jede Seite des PDFs in eine separate JPG-Datei."""
    print(f"\n[+] Starting Page-to-JPG Mission: {os.path.basename(filepath)}")

    try:
        # DPI Abfrage für die Qualität
        dpi_input = input("Target Resolution (DPI) [Standard 150]: ").strip()
        dpi = int(dpi_input) if dpi_input else 150
        zoom = dpi / 72  # 72 ist der Standard-PDF-Punktwert
        matrix = fitz.Matrix(zoom, zoom)

        doc = fitz.open(filepath)
        base_name = os.path.splitext(os.path.basename(filepath))[0]
        output_dir = os.path.join(os.path.dirname(filepath), f"pages_{base_name}")

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        print(f"[*] Exporting {len(doc)} pages to {output_dir}...")

        for i in range(len(doc)):
            page = doc[i]
            # Die Seite mit der Matrix (DPI) rendern
            pix = page.get_pixmap(matrix=matrix, colorspace=fitz.csRGB)

            img_filename = f"page_{i + 1}.jpg"
            full_path = os.path.join(output_dir, img_filename)

            # Speichern (Qualität 90% ist ein guter Kompromiss)
            pix.save(full_path, "jpg")
            if (i + 1) % 5 == 0:  # Kleines Fortschritts-Update alle 5 Seiten
                print(f"    [+] {i + 1} pages processed...")

        doc.close()
        print(f"\n[*] MISSION ACCOMPLISHED: All pages stored as JPG.")
        print(f"[*] Location: {output_dir}")

    except Exception as e:
        print(f"[!] Export Error: {e}")


def export_pages_precision(filepath):
    """Konvertiert PDF-Seiten mit intelligenten Pixel-Vorgaben in JPG."""
    print(f"\n[+] Intelligent Precision Export: {os.path.basename(filepath)}")

    try:
        # Abfragen der Parameter
        print("\nEnter dimensions. Leave one empty for proportional scaling.")
        print("Prefix with '<=' for 'Fit-In' logic (e.g., w = <=2480).")

        in_w = input("Target Width (w): ").strip().lower()
        in_h = input("Target Height (h): ").strip().lower()

        # Logik-Flags
        fit_in = False
        if in_w.startswith("<=") or in_h.startswith("<="):
            fit_in = True
            in_w = in_w.replace("<=", "")
            in_h = in_h.replace("<=", "")

        # Konvertierung zu Integer (wenn vorhanden)
        target_w = int(in_w) if in_w else None
        target_h = int(in_h) if in_h else None

        doc = fitz.open(filepath)
        base_name = os.path.splitext(os.path.basename(filepath))[0]
        output_dir = os.path.join(os.path.dirname(filepath), f"pages_export_{base_name}")
        if not os.path.exists(output_dir): os.makedirs(output_dir)

        for i in range(len(doc)):
            page = doc[i]
            pdf_w = page.rect.width
            pdf_h = page.rect.height
            aspect = pdf_w / pdf_h

            final_w, final_h = 0, 0

            # --- FALLUNTERSCHEIDUNG ---

            # FALL: Fit-In Logik (w <= und h <=)
            if fit_in and target_w and target_h:
                # Berechne Skalierung für beide Achsen und nimm die kleinere
                scale = min(target_w / pdf_w, target_h / pdf_h)
                final_w = int(pdf_w * scale)
                final_h = int(pdf_h * scale)

            # FALL: Beide Maße exakt vorgegeben (Stretch/Squash)
            elif target_w and target_h:
                final_w = target_w
                final_h = target_h

            # FALL: Nur Breite vorgegeben
            elif target_w:
                final_w = target_w
                final_h = int(target_w / aspect)

            # FALL: Nur Höhe vorgegeben
            elif target_h:
                final_h = target_h
                final_w = int(target_h * aspect)

            else:
                print("[!] Error: No valid dimensions provided.")
                return

            # Matrix berechnen und Bild erzeugen
            zoom_x = final_w / pdf_w
            zoom_y = final_h / pdf_h
            mat = fitz.Matrix(zoom_x, zoom_y)

            pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
            img_filename = f"page_{i + 1}_{final_w}x{final_h}.jpg"
            pix.save(os.path.join(output_dir, img_filename), "jpg")

            if (i + 1) % 5 == 0 or i == 0:
                print(f"    [+] Page {i + 1} forged to {final_w}x{final_h} px")

        doc.close()
        print(f"\n[*] MISSION ACCOMPLISHED: Files stored in {output_dir}")

    except Exception as e:
        print(f"[!] Precision Export Error: {e}")

def scout_pdf(filepath):
    """Schnelle Übersicht: Was liegt auf welcher Seite?"""
    print(f"\n[+] Scout Mission: {filepath}")
    try:
        doc = fitz.open(filepath)
        scout_results = []

        for i in range(len(doc)):
            page = doc[i]
            
            # 1. Seitengröße messen
            temp_doc = fitz.open()
            temp_doc.insert_pdf(doc, from_page=i, to_page=i)
            p_size = len(temp_doc.convert_to_pdf()) / 1024
            temp_doc.close()

            # 2. Nur Bild-Typen sammeln (ohne DPI-Berechnung)
            page_imgs = page.get_images()
            formats = []
            for img in page_imgs:
                # img[8] enthält oft das Format (z.B. 'jpg', 'png')
                fmt = img[8].upper()
                if fmt not in formats:
                    formats.append(fmt)

            scout_results.append({
                "page": i + 1,
                "size": p_size,
                "img_count": len(page_imgs),
                "formats": formats
            })

        from show_data_table import print_scout_table
        print_scout_table(scout_results)
        doc.close()
        input("\nPress Enter to return to the command menu...")
    except Exception as e:
        print(f"[!] Scout Error: {e}")

def sabotage_patch(filepath):
    """
    Sucht gezielt nach Bildern, die über einem User-Limit liegen,
    und rechnet nur diese auf das Limit herunter.
    """
    print(f"\n[!] Smart Sabotage Mission: {filepath}")

    try:
        limit_input = input("Maximal erlaubte DPI (z.B. 150): ").strip()
        max_dpi = int(limit_input) if limit_input else 150

        doc = fitz.open(filepath)
        found_monsters = 0

        for page_index in range(len(doc)):
            page = doc[page_index]
            page_w_inch = page.rect.width / 72
            img_list = page.get_images()

            for img in img_list:
                xref = img[0]
                base_img = doc.extract_image(xref)

                if base_img:
                    # Aktuelle DPI berechnen
                    current_dpi = int(base_img["width"] / page_w_inch) if page_w_inch > 0 else 0

                    if current_dpi > max_dpi:
                        found_monsters += 1
                        print(
                            f"    [*] Page {page_index + 1}: Image (xref {xref}) has {current_dpi} DPI. Sabotaging to {max_dpi}...")

                        # Bild skalieren
                        pix = fitz.Pixmap(doc, xref)

                        # Skalierungsfaktor berechnen (z.B. 150 / 300 = 0.5)
                        zoom = max_dpi / current_dpi
                        mat = fitz.Matrix(zoom, zoom)

                        # Neue Pixmap mit reduzierter Größe erstellen
                        new_pix = fitz.Pixmap(pix.colorspace, pix.width, pix.height, pix.alpha)
                        # Wir nutzen eine temporäre Pixmap zum Skalieren
                        scaled_pix = fitz.Pixmap(pix, pix.width, pix.height, None)  # Platzhalter

                        # Einfachere Methode: Bild neu einsetzen mit transformierter Matrix
                        # Wir ersetzen das Bild am selben XREF
                        doc.replace_image(xref, pixmap=pix)  # Platzhalter für die Logik
                        # Da replace_image die Pixmap direkt nimmt, skalieren wir hier:
                        if pix.width > base_img["width"] * zoom:
                            # Wir erstellen ein skaliertes Sample
                            sample_pix = fitz.Pixmap(pix)
                            sample_pix.shrink(int(1 / zoom) if zoom < 1 else 1)
                            doc.replace_image(xref, pixmap=sample_pix)

                        pix = None
                        sample_pix = None

        if found_monsters > 0:
            base, ext = os.path.splitext(filepath)
            out_path = f"{base}_smart_sabotaged{ext}"
            doc.save(out_path, garbage=4, deflate=True)

            old_size = os.path.getsize(filepath) / 1024
            new_size = os.path.getsize(out_path) / 1024
            print(f"\n[*] Mission Accomplished: {found_monsters} Images sabotaged.")
            print(f"[*] Damage Report: {old_size:.2f} KB -> {new_size:.2f} KB")
            print(f"[*] Result saved as: {os.path.basename(out_path)}")
        else:
            print("[*] Intelligence Report: No images found above DPI limit. No action taken.")

        doc.close()
    except Exception as e:
        print(f"[!] Sabotage Error: {e}")


def sabotage_patch_Mini(filepath):
    """Gezielte Sabotage: Bilder über Limit werden physisch durch kleinere ersetzt."""
    print(f"\n[!] Smart Sabotage Mission: {filepath}")

    try:
        limit_input = input("Maximal erlaubte DPI (Standard 150): ").strip()
        max_dpi = int(limit_input) if limit_input else 150

        doc = fitz.open(filepath)
        found_monsters = 0

        for page in doc:
            page_w_inch = page.rect.width / 72
            # Wir holen uns die Bild-Informationen inklusive der Position (rect)
            # 'item' enthält: [xref, smask, width, height, bpc, colorspace, ...]
            img_info = page.get_image_info(hashes=False)

            for img in img_info:
                xref = img["xref"]
                bbox = img["bbox"]  # Die Position auf der Seite

                # DPI Check
                current_dpi = int(img["width"] / page_w_inch) if page_w_inch > 0 else 0

                if current_dpi > max_dpi:
                    found_monsters += 1
                    print(f"    [*] Page {page.number + 1}: Sabotaging {current_dpi} DPI image...")

                    # 1. Bild als Pixmap extrahieren
                    pix = fitz.Pixmap(doc, xref)

                    # 2. Skalierungsfaktor berechnen
                    zoom = max_dpi / current_dpi

                    # 3. Neue, kleinere Pixmap erstellen
                    # Wir nutzen ein neues Dokument als temporären Speicher, um saubere Streams zu erzeugen
                    img_data = pix.tobytes("jpeg")  # JPEG ist am kompatibelsten

                    # 4. Altes Bild auf der Seite "übermalen" oder entfernen
                    # Da wir das Objekt nicht einfach löschen können ohne das Layout zu zerstören,
                    # legen wir das neue Bild einfach mit Priorität darüber.
                    page.insert_image(bbox, stream=img_data)

                    pix = None

        if found_monsters > 0:
            base, ext = os.path.splitext(filepath)
            out_path = f"{base}_sabotaged{ext}"

            # WICHTIG: 'incremental=False' erzwingen durch Speichern in neue Datei
            doc.save(out_path, garbage=4, deflate=True, clean=True)

            if os.path.exists(out_path):
                old_size = os.path.getsize(filepath) / 1024
                new_size = os.path.getsize(out_path) / 1024
                print(f"\n[*] Mission Accomplished: {found_monsters} Images handled.")
                print(f"[*] Damage Report: {old_size:.2f} KB -> {new_size:.2f} KB")
                print(f"[*] File saved at: {out_path}")
            else:
                print("[!] Error: File could not be written to disk.")
        else:
            print("[*] Intelligence Report: No images found above DPI limit.")

        doc.close()
    except Exception as e:
        print(f"[!] Sabotage Error: {e}")

def heavy_strike_gs(filepath):
    """Radikale Kompression via Ghostscript - Optimiert für GS 10.x."""
    import os, subprocess
    print(f"\n[!] Heavy Strike Mission (Ghostscript): {os.path.basename(filepath)}")

    try:
        # 1. Inputs mit Defaults
        limit_input = input("Target DPI [Standard 150]: ").strip()
        target_dpi = limit_input if limit_input else "150"

        q_input = input("Quality 1...100% [Standard 90]: ").strip()
        quality_val = int(q_input) if q_input else 90

        # Berechnung des QFactors (GS intern)
        q_factor = (100 - quality_val) / 100

        # 2. Zielpfad über deine Helper-Funktion
        out_path = get_save_path(filepath, "gs_compressed")

        # 3. Das finale, getestete Kommando
        # 3. Das stabilste Kommando ohne bevormundende Profile
        cmd = [
            "gs",
            "-sDEVICE=pdfwrite",
            "-dCompatibilityLevel=1.4",
            "-dNOPAUSE", "-dQUIET", "-dBATCH",
            f"-sOutputFile={out_path}",
            # Erzwinge Neuberechnung aller Bilder
            "-dColorImageFilter=/DCTEncode",
            "-dGrayImageFilter=/DCTEncode",
            f"-dColorImageResolution={target_dpi}",
            f"-dGrayImageResolution={target_dpi}",
            "-dAutoFilterColorImages=false",
            "-dAutoFilterGrayImages=false",
            "-dDownsampleColorImages=true",
            "-dDownsampleGrayImages=true",
            # Die Qualitätsparameter direkt übergeben
            "-c",
            f"<< /ColorImageDict << /JPEGQ {quality_val} /QFactor {q_factor} >> /GrayImageDict << /JPEGQ {quality_val} /QFactor {q_factor} >> >> setdistillerparams",
            "-f", filepath
        ]

        # Strike ausführen
        result = subprocess.run(cmd, capture_output=True, text=True)

        # 4. Erfolgskontrolle
        if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
            old_size = os.path.getsize(filepath)
            new_size = os.path.getsize(out_path)
            # Ersparnis berechnen
            savings = (1 - (new_size / old_size)) * 100
            print(f"\n[*] MISSION ACCOMPLISHED")
            print(f"[*] Saved to: {os.path.basename(out_path)}")
            print(f"[*] Damage Report: {old_size / 1024:.1f} KB -> {new_size / 1024:.1f} KB (-{savings:.1f}%)")
            return out_path
        else:
            print(f"\n[!] MISSION FAILED: Ghostscript output missing.")
            if result.stderr:
                print(f"[!] System Message: {result.stderr}")
            return None

    except Exception as e:
        print(f"\n[!] MISSION FAILED: Heavy Strike Error.")
        print(f"[!] Details: {e}")
        return None

def deep_recon(filepath):
    """
    Führt eine tiefen-forensische Analyse des PDFs durch.
    """
    print(f"\n[+] Deep Forensic Recon: {filepath}")

    # 1. WICHTIG: Liste AUSSERHALB des try initialisieren
    recon_results = []

    try:
        doc = fitz.open(filepath)

        for i in range(len(doc)):
            page = doc[i]

            # Seitengröße messen (∑SIZE Wert)
            temp_doc = fitz.open()
            temp_doc.insert_pdf(doc, from_page=i, to_page=i)
            p_size = len(temp_doc.convert_to_pdf()) / 1024
            temp_doc.close()

            page_w_inch = page.rect.width / 72
            page_imgs = page.get_images()
            img_details = []

            for img in page_imgs:
                xref = img[0]
                base_img = doc.extract_image(xref)

                if base_img:
                    # Aufruf der Funktion aus utility.py
                    q_val = analyze_compression(base_img["image"], base_img["width"], base_img["height"],
                                                base_img["ext"].upper())

                    # Farbenraum-Sonde
                    cs_name = base_img.get("colorspace", "Unknown")
                    if cs_name == "Unknown" or not cs_name or isinstance(cs_name, int):
                        try:
                            pix = fitz.Pixmap(doc, xref)
                            cs_name = pix.colorspace.name if pix.colorspace else "n/a"
                            pix = None
                        except:
                            cs_name = "n/a"

                    dpi_est = int(base_img["width"] / page_w_inch) if page_w_inch > 0 else 0

                    img_details.append({
                        "size_kb": len(base_img["image"]) / 1024,
                        "w": base_img["width"],
                        "h": base_img["height"],
                        "cs": cs_name,
                        "q_val": q_val,
                        "dpi": dpi_est,
                        "ext": base_img["ext"].upper()
                    })

            recon_results.append({
                "page": i + 1,
                "size": p_size,
                "img_count": len(page_imgs),
                "images": img_details
            })

        doc.close()

        # 2. Die Tabelle nur drucken, wenn Daten da sind
        if recon_results:
            print_recon_master_table(recon_results)
        else:
            print("[!] Mission failure: No data collected.")


    except Exception as e:
        # Jetzt wird 'e' ausgegeben, was uns den echten Grund verrät
        print(f"[!] Recon Error: {e}")

    input("\nPress Enter to return to the command menu...")

def split_scroll(filepath):
    """Splitting PDF"""
    print(f"\n[+] Splitting Scroll: {filepath}")
    try:
        doc = fitz.open(filepath)
        base_name = os.path.splitext(os.path.basename(filepath))[0]
        output_dir = os.path.join(os.path.dirname(filepath), f"split_{base_name}")

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        for i in range(len(doc)):
            new_doc = fitz.open()
            new_doc.insert_pdf(doc, from_page=i, to_page=i)
            new_doc.save(os.path.join(output_dir, f"page_{i + 1}.pdf"))
            new_doc.close()

        doc.close()
        print(f"[*] Victory! Pages scattered into: {output_dir}")
    except Exception as e:
        print(f"[!] Split Error: {e}")

def merge_scrolls():
    """Merge Pages to PDF."""
    print("\n[+] Preparation for Forge: Merging multiple scrolls.")
    target_name = input("Enter name for the new forged scroll (e.g. combined.pdf): ").strip()
    if not target_name.endswith(".pdf"): target_name += ".pdf"

    print("Enter paths to scrolls (one per line, empty line to start forging):")
    scrolls = []
    while True:
        path = input("> ").strip().replace("'", "").replace('"', "")
        if not path: break
        if os.path.exists(path):
            scrolls.append(path)
        else:
            print(f"[!] Scroll not found: {path}")

    if len(scrolls) < 2:
        print("[!] Not enough scrolls to merge. The forge remains cold.")
        return

    try:
        new_doc = fitz.open()
        for path in scrolls:
            with fitz.open(path) as src:
                new_doc.insert_pdf(src)

        new_doc.save(target_name)
        new_doc.close()
        print(f"[*] Forge successful: {target_name} created.")
        return target_name
    except Exception as e:
        print(f"[!] Forge Error: {e}")

def technical_intel(filepath):
    """Scannt das PDF nach technischen Feinheiten, Müll und aktiven Inhalten."""
    print(f"\n[+] Technical Intel Mission: {filepath}")
    try:
        doc = fitz.open(filepath)
        
        # 1. PDF Version direkt aus der Datei lesen (Bulletproof)
        pdf_ver = "Unknown"
        with open(filepath, "rb") as f:
            header = f.read(8).decode('utf-8', errors='ignore')
            if header.startswith("%PDF-"):
                pdf_ver = header[5:8]

        # 2. Check für JavaScript / Scripte (Katalog-Scan)
        has_js = "No"
        try:
            # Wir prüfen den Katalog-String direkt auf JS-Marker
            cat_str = str(doc.pdf_catalog())
            if "/JS" in cat_str or "/JavaScript" in cat_str:
                has_js = "YES (Active Content!)"
        except:
            pass
        
        # 3. Garbage Scan (Simuliere eine Bereinigung im RAM)
        original_size = os.path.getsize(filepath)
        try:
            # garbage=3 ist sicher und entfernt ungenutzte Objekte
            clean_buffer = doc.tobytes(garbage=3, deflate=True)
            savings = (original_size - len(clean_buffer)) / 1024
        except:
            savings = 0.0
        
        # 4. Intel-Daten zusammenstellen
        intel_data = {
            "PDF Version": pdf_ver,
            "Object Count": doc.xref_length(),
            "Interactive Forms": "YES" if doc.is_form_pdf else "No",
            "JavaScript": has_js,
            "Layers (OCGs)": "YES" if doc.get_ocgs() else "No",
            "Cleanable Waste": f"{max(0, savings):.2f} KB",
            "Encryption": "Encrypted" if doc.is_encrypted else "None",
            "Rights (Permissions)": "Full" if doc.permissions == -1 else "Restricted"
        }
        
        from show_data_table import print_metadata_table
        print_metadata_table(intel_data)
        
        if savings > 100:
            print(f"[*] Intelligence Note: Waste detected! Option 5 or a re-save could trim {savings:.2f} KB.")
            
        doc.close()
    except Exception as e:
        print(f"[!] Intel Error: {e}")

def purge_waste(filepath):
    print(f"\n[+] Purge Mission: Cleaning {os.path.basename(filepath)}...")

    # Zielpfad abfragen
    out_path = get_save_path(filepath, "purged")

    try:
        doc = fitz.open(filepath)
        doc.save(out_path, garbage=4, deflate=True, clean=True)
        doc.close()

        if os.path.exists(out_path):
            print(f"[*] Success: File secured at {out_path}")
            return out_path
        else:
            raise FileNotFoundError("File was not created.")

    except Exception as e:
        print(f"\n[!] MISSION FAILED: Could not create purged file.")
        print(f"[!] Error Details: {e}")
        return None

def extract_loot(filepath):
    """Extrahiert alle eingebetteten Bilder aus dem PDF in einen Loot-Ordner."""
    print(f"\n[+] Starting Loot Mission: Extracting images from {filepath}...")
    try:
        doc = fitz.open(filepath)
        base_name = os.path.splitext(os.path.basename(filepath))[0]
        loot_dir = os.path.join(os.path.dirname(filepath), f"loot_{base_name}")

        if not os.path.exists(loot_dir):
            os.makedirs(loot_dir)

        img_count = 0
        for i in range(len(doc)):
            img_list = doc.get_page_images(i)
            for img_index, img in enumerate(img_list):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]

                img_filename = f"pg{i + 1}_img{img_index + 1}.{image_ext}"
                with open(os.path.join(loot_dir, img_filename), "wb") as f:
                    f.write(image_bytes)
                img_count += 1

        print(f"[*] Mission Accomplished: {img_count} items looted!")
        print(f"[*] Storage Location: {loot_dir}")
        doc.close()
    except Exception as e:
        print(f"[!] Loot Error: {e}")

def check_gs_presence():
    """Prüft im Hintergrund, ob Ghostscript verfügbar ist."""
    gs_cmd = "gswin64c" if os.name == "nt" else "gs"
    try:
        subprocess.check_output([gs_cmd, "--version"], stderr=subprocess.STDOUT)
        return True
    except:
        return False

def main():
    print_banner()
    # Initial path-check
    if not check_gs_presence():
        print("[!] Warning: Ghostscript not detected. 'Heavy Strike' will be unavailable.")

    if len(sys.argv) > 1:
        current_path = sys.argv[1].replace("'", "").replace('"', "")
    else:
        current_path = ""
        while not os.path.exists(current_path):
            current_path = change_target("Enter path to the first scroll: ")
            if not current_path:
                print("[!] A valid scroll is required to enter the vault.")
                current_path = "" # Loop fortsetzen
    while True:
        # Falls der Pfad zwischendurch ungültig wurde
        if not os.path.exists(current_path):
            print(f"[!] Target lost: {current_path}")
            current_path = change_target("Enter path to a new valid scroll: ")
            if not current_path: continue

        print(f"\n{'=' * 20} CURRENT TARGET: {os.path.basename(current_path)} {'=' * 20}")
        print("\n--- Command Menu ------ Analyze PDF ---:")
        print("a) Page Sizes (simple)        b) Advanced Page Info      c) PDF Intel (Tech-Check)")
        print("--- Manipulate PDF to Reduce Size ---:")
        #print("1) Heavy Strike (GS)          2) Purge/Clean             22) Smart Sabotage (DPI)")
        print("1) Heavy Strike (GS)          2) Purge/Clean")
        print("--- Manipulate PDF MISC ---:")
        print("10) Split PDF                 11) Merge PDF              12) Loot (Extract Imgs)")
        print("13) Pages to JPG (DPI)        14) Pages to JPG (Fixed Res)") # <-- NEU
        print("--- Control ---:")
        print("n) Select PDF (Change)        i) Version table           q) Quit")

        choice = input("\nAction: ").lower()
        new_file = None

        # --- Logic Routing ---
        if choice == 'a': scout_pdf(current_path)
        elif choice == 'b': deep_recon(current_path)
        elif choice == 'c': technical_intel(current_path)
        elif choice == '1': new_file = heavy_strike_gs(current_path)
        elif choice == '2': new_file = purge_waste(current_path)
        #elif choice == '22': sabotage_patch_Mini(current_path)
        elif choice == '10': split_scroll(current_path)
        elif choice == '11': new_file = merge_scrolls() # result = merge_scrolls()
        elif choice == '12': extract_loot(current_path)
        elif choice == '13': export_pages_as_jpg(current_path)
        elif choice == '14': export_pages_precision(current_path)
        elif choice == 'n':
            result = change_target("Enter path to new scroll: ")
            if result:
                current_path = result
        elif choice == 'i': show_toolkit_intel()
        elif choice == 'q':
            print("Exiting the vault. Fare thee well!")
            break

        # Falls eine neue Datei erzeugt wurde, fragen wir, ob wir das Ziel wechseln wollen
        if new_file and os.path.exists(new_file):
            print_target_report(new_file)
            switch = input(f"Switch focus to new file? (y/n): ").lower()
            if switch == 'y':
                current_path = new_file

if __name__ == "__main__":
    main()