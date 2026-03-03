import fitz
import os


def interactive_image_replacer(main_pdf_path, replacement_path=None, output_path=None):
    """Ersetzt ein Bild in einem PDF durch ein anderes PDF oder Bild.
    Löscht das alte Asset physisch, um die Dateigröße zu minimieren."""
    print(f"\n--- 🛠️ Forge: Surgical Asset Replacement ---")

    # 1. Pfade säubern
    main_pdf_path = main_pdf_path.strip("'").strip('"')

    if not os.path.exists(main_pdf_path):
        print(f"❌ Error: Source PDF not found at {main_pdf_path}")
        return None

    if not replacement_path:
        replacement_path = input("Enter Path to Replacement File (PDF/Image): ").strip().strip("'").strip('"')

    if not os.path.exists(replacement_path):
        print(f"❌ Error: Replacement file not found at {replacement_path}")
        return None

    if not output_path:
        default_output = main_pdf_path.replace(".pdf", "_replaced.pdf")
        output_path = input(f"Enter Output Path [Enter for {default_output}]: ").strip().strip("'").strip('"')
        output_path = output_path if output_path else default_output

    try:
        # Docs öffnen
        doc = fitz.open(main_pdf_path)
        replacement_doc = fitz.open(replacement_path)

        # 2. Recon: Bilder im Dokument finden
        found_images = []
        for p_no in range(len(doc)):
            page = doc[p_no]
            for img in page.get_images(full=True):
                xref = img[0]
                rects = page.get_image_rects(xref)
                if rects:
                    # Wir speichern alle Meta-Daten für die Auswahl
                    found_images.append({
                        "page": p_no,
                        "xref": xref,
                        "rect": rects[0],
                        "dim": f"{img[2]}x{img[3]}",
                        "type": img[8]  # z.B. DCTDecode (JPG) oder FlateDecode (PNG)
                    })

        if not found_images:
            print("❌ No target images found in source PDF.")
            doc.close()
            replacement_doc.close()
            return None

        # 3. Auswahl durch den Nutzer
        print("\nTarget Assets Found (Recon Results):")
        print(f"{'IDX':<4} | {'PG':<3} | {'XREF':<6} | {'DIMENSION':<12} | {'RECTANGLE'}")
        print("-" * 65)
        for i, img in enumerate(found_images):
            print(f"[{i:1}] | {img['page'] + 1:<3} | {img['xref']:<6} | {img['dim']:<12} | {img['rect']}")

        choice_input = input(f"\nSelect Index to replace (0-{len(found_images) - 1}): ").strip()
        if not choice_input.isdigit():
            print("❌ Invalid input. Mission aborted.")
            return None

        selected = found_images[int(choice_input)]

        # 4. Der chirurgische Eingriff
        target_page = doc[selected['page']]
        target_rect = selected['rect']
        target_xref = selected['xref']

        # Schritt A: Altes Bild-Objekt von der Seite lösen
        target_page.delete_image(target_xref)

        # Schritt B: Content-Stream säubern (entfernt Reste im Code)
        target_page.clean_contents()

        # Schritt C: Neues Element an exakt dieselbe Stelle setzen
        # Das replacement_doc wird automatisch in das target_rect skaliert
        target_page.show_pdf_page(target_rect, replacement_doc, 0)

        # 5. Finale Versiegelung & Müllabfuhr
        # garbage=4 ist kritisch, um das alte XREF-Objekt physisch zu löschen!
        doc.save(
            output_path,
            garbage=4,
            deflate=True,
            clean=True
        )

        doc.close()
        replacement_doc.close()

        print(f"\n✅ Success! Old asset removed and replaced.")
        print(f"🚀 New file saved: {output_path}")
        return output_path

    except Exception as e:
        print(f"❌ Mission failed: {e}")
        return None