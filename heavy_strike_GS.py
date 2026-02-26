import os
import subprocess

def heavy_strike_gs(filepath):
    """Isolierter Test für Ghostscript 10.06 Kompression."""
    print(f"\n[!] HEAVY STRIKE TEST RUN: {os.path.basename(filepath)}")

    if not os.path.exists(filepath):
        print(f"[!] ERROR: File not found: {filepath}")
        return None

    try:
        # 1. Parameter (DPI und Quality)
        target_dpi = input("Target DPI [Standard 150]: ").strip() or "150"
        quality_val = input("Quality 1...100 [Standard 90]: ").strip() or "90"

        # Zielpfad im gleichen Ordner wie das Original
        base, ext = os.path.splitext(filepath)
        out_path = f"{base}_test_result{ext}"

        # 2. Das Kommando - Umgestellt auf GS 10.06 Stabilität
        cmd = [
            "gs", 
            "-sDEVICE=pdfwrite",
            "-dCompatibilityLevel=1.4",
            "-dPDFSETTINGS=/ebook",
            "-dNOPAUSE", "-dQUIET", "-dBATCH",
            f"-sOutputFile={out_path}",
            f"-dColorImageResolution={target_dpi}",
            f"-dGrayImageResolution={target_dpi}",
            f"-dMonoImageResolution={target_dpi}",
            "-dDownsampleColorImages=true",
            "-dDownsampleGrayImages=true",
            "-dDownsampleMonoImages=true",
            # NEU: Direktere Qualitätssteuerung für GS 10.x
            f"-c", f".setpdfwrite << /ColorImageDict << /JPEGQ {quality_val} /QFactor { (100-int(quality_val))/100 } >> >> setdistillerparams",
            "-f", filepath
        ]

        print(f"[*] Command: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
            print(f"\n[*] SUCCESS!")
            print(f"[*] New File: {out_path}")
            print(f"[*] Size: {os.path.getsize(out_path)/1024:.2f} KB")
            return out_path
        else:
            print(f"\n[!] FAILED")
            print(f"STDOUT: {result.stdout}")
            print(f"STDERR: {result.stderr}")
            return None

    except Exception as e:
        print(f"\n[!] ERROR: {e}")
        return None

# --- DER TEST-AUFRUF ---
if __name__ == "__main__":
    # Pfad zu deiner Dropbox-Datei hier einfügen
    test_file = "/Users/degge/Library/CloudStorage/Dropbox/Bewerbung_Target/Anlagen/Scans/Unkomprimiert_Komplett 2.pdf"
    heavy_strike_gs(test_file)