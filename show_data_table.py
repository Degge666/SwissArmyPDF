# Datei: /Users/degge/MyProjects/swithArmyPdf/show_data_table.py

def print_scout_table(scout_data):
    """Kompakte Übersicht für Option 1: Scout."""
    print("\n" + "╔" + "═"*58 + "╗")
    print(f"║ {'PG':<3} ║ {'SIZE (KB)':<12} ║ {'IMGS':<4} ║ {'FORMATS':<25} ║")
    print("╟" + "─"*5 + "╫" + "─"*14 + "╫" + "─"*6 + "╫" + "─"*27 + "╢")
    
    for row in scout_data:
        # Formate kompakt als String sammeln, z.B. "JPEG, PNG"
        fmt_str = ", ".join(row['formats']) if row['formats'] else "-"
        print(f"║ {row['page']:<3} ║ {row['size']:>12.2f} ║ {row['img_count']:<4} ║ {fmt_str:<25} ║")
    
    print("╚" + "═"*58 + "╝")

def print_metadata_table(metadata):
    print("\n" + "═"*75)
    print(f"║ {'METADATA KEY':<20} ║ {'VALUE':<48} ║")
    print("╟" + "─"*22 + "╫" + "─"*50 + "╢")
    for key, value in metadata.items():
        val = str(value) if value else "n/a"
        display_val = val[:45] + "..." if len(val) > 48 else val
        print(f"║ {key:<20} ║ {display_val:<48} ║")
    print("╚" + "═"*73 + "╝")

# Datei: /Users/degge/MyProjects/swithArmyPdf/show_data_table.py

# Datei: /Users/degge/MyProjects/swithArmyPdf/show_data_table.py

def print_recon_master_table(recon_data):
    """Präzise kalibrierte Tabelle für Page-Stats, Bilder, DPI und Typ."""
    # Gesamtlänge: 110 Zeichen
    header = f"║ {'PG':<3} ║ {'SIZE (KB)':<10} ║ {'IMG':<3} ║ {'PIXELS (px)':<16} ║ {'DPI':<5} ║ {'TYPE':<6} ║ {'COLORSPACE':<35} ║"
    sep_main = "╟" + "─"*5 + "╫" + "─"*12 + "╫" + "─"*5 + "╫" + "─"*18 + "╫" + "─"*7 + "╫" + "─"*8 + "╫" + "─"*37 + "╢"
    
    print("\n╔" + "═"*108 + "╗")
    print(header)
    print(sep_main)
    
    for row in recon_data:
        imgs = row['images']
        pg_num = str(row['page'])
        pg_size = f"{row['size']:>10.2f}"
        img_count = str(row['img_count'])
        
        if not imgs:
            # Zeile für Seiten ohne Bilder
            print(f"║ {pg_num:<3} ║ {pg_size:<10} ║ {img_count:<3} ║ {'no images':<16} ║ {'-':<5} ║ {'-':<6} ║ {'-':<35} ║")
        else:
            for i, img in enumerate(imgs):
                # Nur in der ersten Zeile eines Seiten-Blocks die Seitendaten zeigen
                curr_pg = pg_num if i == 0 else ""
                curr_sz = pg_size if i == 0 else ""
                curr_cnt = img_count if i == 0 else ""
                
                dims = f"{img['w']}x{img['h']}"
                dpi = str(img['dpi'])
                ext = img['ext']
                cs = img['cs'][:33] # Kürzen falls zu lang
                
                print(f"║ {curr_pg:<3} ║ {curr_sz:<10} ║ {curr_cnt:<3} ║ {dims:<16} ║ {dpi:<5} ║ {ext:<6} ║ {cs:<35} ║")
    
    print("╚" + "═"*108 + "╝")
    
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

