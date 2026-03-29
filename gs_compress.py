#!/usr/bin/env python3
"""
SwissArmyPDF - Ghostscript Komprimierungs-Test (standalone)
"""

import argparse
import subprocess
from pathlib import Path
import sys


def run_gs_compress(self):
    if not self.engine.current_pdf:
        self.status_bar.showMessage("Kein Dokument ausgewählt")
        return

    try:
        dpi = int(self.gs_dpi_field.text())
        quality = int(self.gs_quality_field.text())
        if not (30 <= quality <= 100 and 50 <= dpi <= 600):
            raise ValueError("DPI 50–600, Quality 30–100")
    except ValueError as e:
        self.status_bar.showMessage(f"Ungültige Werte: {e}")
        return

    input_path = Path(self.engine.current_pdf)
    suggested = str(input_path.with_stem(input_path.stem + f"_gs_{dpi}dpi_q{quality}"))

    out_path, _ = QFileDialog.getSaveFileName(self, "GS Output", suggested, "PDF (*.pdf)")
    if not out_path:
        return

    # Template füllen
    gs_params = GS_TEMPLATE.format(dpi=dpi, quality=quality)

    gs_cmd = ["gs"] + gs_params.split() + ["-sOutputFile=" + out_path, str(input_path)]

    print(f"[GS] Ausführung: {' '.join(gs_cmd)}")

    try:
        subprocess.run(gs_cmd, check=True)
        self.status_bar.showMessage(f"GS fertig → {Path(out_path).name}")

        # Optional: Re-Scan
        new_id = self.engine.run_full_scan(out_path, parent_doc_id=self.current_doc_id)
        if new_id != -1:
            self.refresh_archive_list()
            self.status_bar.showMessage(f"Re-Scan OK – neues Derived (ID {new_id})")

    except Exception as e:
        print(f"[GS] Fehler: {e}")
        self.status_bar.showMessage("Ghostscript Fehler – siehe Konsole")


def main():
    parser = argparse.ArgumentParser(description="Ghostscript Komprimierungs-Test")
    parser.add_argument("input", type=str, help="Input PDF")
    parser.add_argument("output", type=str, nargs="?", default="output.pdf", help="Output PDF")
    parser.add_argument("--dpi", type=int, default=150, help="Ziel-DPI für Bilder")
    parser.add_argument("--settings", type=str, default="/ebook",
                        choices=["/screen", "/ebook", "/printer", "/prepress", "/default"],
                        help="PDFSETTINGS: /screen (aggressiv), /ebook (ausgewogen), /prepress (hoch)")

    args = parser.parse_args()

    run_ghostscript(args.input, args.output, args.dpi, args.settings)


if __name__ == "__main__":
    main()