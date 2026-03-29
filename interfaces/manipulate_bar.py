#!/usr/bin/env python3
"""
Mini-GUI für Ghostscript-Komprimierung (standalone zum Testen)
"""

import sys
import subprocess
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFileDialog, QTextEdit, QMessageBox
)
from PyQt6.QtCore import Qt


class MiniGSWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SwissArmyPDF – Ghostscript Test GUI")
        self.resize(600, 400)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # DPI + Quality
        param_layout = QHBoxLayout()
        param_layout.addWidget(QLabel("DPI:"))
        self.dpi_field = QLineEdit("150")
        self.dpi_field.setFixedWidth(80)
        param_layout.addWidget(self.dpi_field)

        param_layout.addWidget(QLabel("Qualität:"))
        self.quality_field = QLineEdit("80")
        self.quality_field.setFixedWidth(80)
        param_layout.addWidget(self.quality_field)
        param_layout.addStretch()

        layout.addLayout(param_layout)

        # Datei-Auswahl
        file_layout = QHBoxLayout()
        self.input_label = QLabel("Keine PDF ausgewählt")
        file_layout.addWidget(self.input_label)

        btn_select = QPushButton("PDF auswählen")
        btn_select.clicked.connect(self.select_input_pdf)
        file_layout.addWidget(btn_select)

        layout.addLayout(file_layout)

        # Run-Button
        self.btn_run = QPushButton("Compress with Ghostscript")
        self.btn_run.clicked.connect(self.run_compress)
        self.btn_run.setEnabled(False)
        layout.addWidget(self.btn_run)

        # Output-Status
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        layout.addWidget(self.status_text)

        self.input_pdf = None

    def select_input_pdf(self):
        file, _ = QFileDialog.getOpenFileName(self, "PDF auswählen", "", "PDF (*.pdf)")
        if file:
            self.input_pdf = file
            self.input_label.setText(Path(file).name)
            self.btn_run.setEnabled(True)
            self.status_text.append(f"[INFO] Ausgewählt: {file}")

    def run_compress(self):
        if not self.input_pdf:
            QMessageBox.warning(self, "Fehler", "Keine PDF ausgewählt")
            return

        try:
            dpi = int(self.dpi_field.text())
            quality = int(self.quality_field.text())
            if not (50 <= dpi <= 600 and 30 <= quality <= 100):
                raise ValueError("DPI: 50–600, Quality: 30–100")
        except ValueError as e:
            QMessageBox.warning(self, "Ungültige Werte", str(e))
            return

        input_path = Path(self.input_pdf)
        suggested = str(input_path.with_stem(input_path.stem + f"_gs_{dpi}dpi_q{quality}"))

        out_path, _ = QFileDialog.getSaveFileName(
            self, "Output speichern", suggested, "PDF (*.pdf)"
        )
        if not out_path:
            return

        gs_cmd = [
            "gs",
            "-sDEVICE=pdfwrite",
            "-dCompatibilityLevel=1.4",
            "-dPDFSETTINGS=/ebook",
            "-dDownsampleColorImages=true",
            "-dColorImageResolution=" + str(dpi),
            "-dGrayImageResolution=" + str(dpi),
            "-dMonoImageResolution=" + str(dpi),
            "-dColorImageDownsampleType=1",
            "-dJPEGQ=" + str(quality),
            "-dCompressPages=true",
            "-dCompressFonts=true",
            "-dEmbedAllFonts=true",
            "-dSubsetFonts=true",
            "-dNOPAUSE", "-dQUIET", "-dBATCH",
            "-sOutputFile=" + out_path,
            str(input_path)
        ]

        self.status_text.append(f"[GS] Starte: {' '.join(gs_cmd)}")
        self.status_text.append("")

        try:
            subprocess.run(gs_cmd, check=True)
            self.status_text.append("[SUCCESS] Ghostscript abgeschlossen")
            new_size = Path(out_path).stat().st_size / 1024
            self.status_text.append(f"→ Ausgabe: {out_path}")
            self.status_text.append(f"→ Neue Größe: {new_size:.1f} KB")
        except subprocess.CalledProcessError as e:
            self.status_text.append("[ERROR] Ghostscript fehlgeschlagen:")
            self.status_text.append(str(e))

        self.status_text.append("")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MiniGSWindow()
    window.show()
    sys.exit(app.exec())