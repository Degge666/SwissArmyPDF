def technical_intel(filepath):
    print(f"\n[+] Technical Intel Mission: {filepath}")
    try:
        doc = fitz.open(filepath)
        
        # 1. Check für interaktive Elemente
        has_js = "YES (Warning)" if doc.get_sigflags() > 0 or b"/JS" in doc.read_contents() else "None"
        has_forms = "YES" if doc.is_form_pdf else "No"
        
        # 2. Garbage Scan (Simuliere eine Bereinigung)
        original_size = os.path.getsize(filepath)
        # Wir speichern es im Speicher (BytesIO) mit Garbage Collection Level 4
        buffer = doc.tobytes(garbage=4, deflate=True)
        potential_saving = (original_size - len(buffer)) / 1024
        
        # 3. Struktur-Details
        intel_data = {
            "PDF Version": doc.pdf_major_version + (doc.pdf_minor_version / 10),
            "Total Objects": doc.xref_length(),
            "Interactive Forms": has_forms,
            "JavaScript/Scripts": has_js,
            "Layers (OCGs)": "YES" if doc.get_ocgs() else "No",
            "Potential Cleaning Gain": f"{potential_saving:.2f} KB",
            "Encryption": "Encrypted (Locked)" if doc.is_encrypted else "None (Open)"
        }
        
        # Wir nutzen die print_metadata_table aus deinem Toolkit für die Anzeige
        from show_data_table import print_metadata_table
        print_metadata_table(intel_data)
        
        doc.close()
    except Exception as e:
        print(f"[!] Intel Error: {e}")
