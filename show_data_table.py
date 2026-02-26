# Datei: /Users/degge/MyProjects/swithArmyPdf/show_data_table.py

def print_scout_table(scout_data):
    """Kompakte Übersicht für Option 1: Scout."""
    print("\n" + "╔" + "═"*55 + "╗")
    print(f"║ {'PG':<3} ║ {'SIZE (KB)':<12} ║ {'IMGS':<4} ║ {'FORMATS':<25} ║")
    print("╟" + "─"*5 + "╫" + "─"*14 + "╫" + "─"*6 + "╫" + "─"*27 + "╢")
    
    for row in scout_data:
        # Formate kompakt als String sammeln, z.B. "JPEG, PNG"
        fmt_str = ", ".join(row['formats']) if row['formats'] else "-"
        print(f"║ {row['page']:<3} ║ {row['size']:>12.2f} ║ {row['img_count']:<4} ║ {fmt_str:<25} ║")
    
    print("╚" + "═"*55 + "╝")

def print_metadata_table(metadata):
    print("\n" + "╔" + "═"*73 + "╗")
    print(f"║ {'METADATA KEY':<20} ║ {'VALUE':<48} ║")
    print("╟" + "─"*22 + "╫" + "─"*50 + "╢")
    for key, value in metadata.items():
        val = str(value) if value else "n/a"
        display_val = val[:45] + "..." if len(val) > 48 else val
        print(f"║ {key:<20} ║ {display_val:<48} ║")
    print("╚" + "═"*73 + "╝")

# Datei: /Users/degge/MyProjects/swithArmyPdf/show_data_table.py

# Datei: /Users/degge/MyProjects/swithArmyPdf/show_data_table.py

def print_recon_master_table(recon_data): # Hier heißt es 'recon_data'
    """Präzise kalibrierte Tabelle für Page-Stats, Bilder, DPI und Typ."""
    header =  "║ PG  ║ ∑SIZE (KB) ║ SIZE (KB) ║ IMG ║ PIXELS (px)   ║  Q[%;bpp]  ║ DPI   ║ TYPE   ║ COLORSPACE                          ║"
    sep_mid = "╟─────╫────────────╫───────────╫─────╫───────────────╫────────────╫───────╫────────╫─────────────────────────────────────╢"

    print("\n" + "╔" + "═" * (len(header) - 2) + "╗")
    print(header)
    print(sep_mid)

    grand_total_size = 0

    for res in recon_data:
        pg = res["page"]
        total_size = res["size"]
        img_count = res["img_count"]
        images = res["images"]

        grand_total_size += total_size

        if not images:
            # Fall: Seite ohne Bilder (nur Text/Vektoren)
            row = f"║ {pg:<3} ║ {total_size:>10.2f} ║ {'-':>9} ║ 0   ║ {'-':<13} ║ {'-':<10} ║ {'-':<5} ║ {'-':<6} ║ {'No Images':<35} ║"
            print(row)
            continue

        for i, img in enumerate(images):
            # Logik für die Gruppierung: PG und ∑SIZE nur in der ersten Zeile der Seite
            pg_str = str(pg) if i == 0 else ""
            total_size_str = f"{total_size:>10.2f}" if i == 0 else " " * 10
            img_count_str = str(img_count) if i == 0 else ""

            # Pixel-String (Breite x Höhe)
            res_str = f"{img['w']}x{img['h']}"

            # Formatierte Zeile
            row = (
                f"║ {pg_str:<3} ║ {total_size_str} ║ {img['size_kb']:>9.2f} ║ {img_count_str:<3} ║ "
                f"{res_str:<13} ║ {img['q_val']:<10} ║ {img['dpi']:<5} ║ {img['ext']:<6} ║ {img['cs']:<35} ║"
            )
            print(row)

    # Abschluss der Tabelle
    print("╚" + "═" * (len(header) - 2) + "╝")
    print(f" ∑ = {grand_total_size / 1024:.2f} MB\n")
    
def print_page_size_table(page_data):
    print("\n" + "╔" + "═"*32 + "╗")
    print(f"║ {'PAGE':<8} ║ {'SIZE (KB)':<18} ║")
    print("╟" + "─"*10 + "╫" + "─"*20 + "╢")
    for page_num, size in page_data:
        print(f"║ {page_num:<8} ║ {size:>18.2f} ║")
    print("╚" + "═"*32 + "╝")

def print_image_report_table(image_data):
    print("\n" + "╔" + "═"*75 + "╗")
    print(f"║ {'PAGE':<6} ║ {'WIDTH (px)':<12} ║ {'HEIGHT (px)':<12} ║ {'COLORSPACE':<35} ║")
    print("╟" + "─"*8 + "╫" + "─"*14 + "╫" + "─"*14 + "╫" + "─"*37 + "╢")
    for img in image_data:
        print(f"║ {img['page']:<6} ║ {img['width']:<12} ║ {img['height']:<12} ║ {img['colorspace']:<35} ║")
    print("╚" + "═"*75 + "╝")

def print_font_table(font_data):
    print("\n" + "╔" + "═"*75 + "╗")
    print(f"║ {'PAGE':<6} ║ {'FONT NAME':<35} ║ {'TYPE':<12} ║ {'EMBEDDED':<10} ║")
    print("╟" + "─"*8 + "╫" + "─"*37 + "╫" + "─"*14 + "╫" + "─"*12 + "╢")
    for f in font_data:
        print(f"║ {f['page']:<6} ║ {f['name']:<35} ║ {f['type']:<12} ║ {f['emb']:<10} ║")
    print("╚" + "═"*75 + "╝")

# Datei: /Users/degge/MyProjects/swithArmyPdf/show_data_table.py

