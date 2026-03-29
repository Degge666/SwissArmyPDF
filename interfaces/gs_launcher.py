#!/usr/bin/env python3
"""
SwissArmyPDF – Ghostscript Mini-GUI (Launcher + Einstellungen)
"""

import sys
import subprocess
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFileDialog, QTextEdit, QMessageBox
)
from PyQt6.QtCore import Qt


class GSLauncherWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SwissArmyPDF – GS Launcher")
        self.resize(700, 180)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Input-Pfad
        h = QHBoxLayout()
        h.addWidget(QLabel("Quell-PDF:"))
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Pfad zur input.pdf")
        h.addWidget(self.input_field)

        btn_select = QPushButton("Auswählen")
        btn_select.clicked.connect(self.select_input_pdf)
        h.addWidget(btn_select)

        layout.addLayout(h)

        # Run-Button
        self.btn_run = QPushButton("Compress with Ghostscript")
        self.btn_run.clicked.connect(self.open_settings_gui)
        self.btn_run.setEnabled(False)
        layout.addWidget(self.btn_run)

        layout.addStretch()

        self.input_pdf = None

    def select_input_pdf(self):
        file, _ = QFileDialog.getOpenFileName(self, "PDF auswählen", "", "PDF (*.pdf)")
        if file:
            self.input_pdf = file
            self.input_field.setText(file)
            self.btn_run.setEnabled(True)
            self.statusBar().showMessage(f"Ausgewählt: {Path(file).name}")

    def open_settings_gui(self):
        if not self.input_pdf:
            QMessageBox.warning(self, "Fehler", "Bitte zuerst eine PDF auswählen")
            return
        self.settings_window = GSSettingsWindow(self.input_pdf)
        self.settings_window.show()


class GSSettingsWindow(QMainWindow):
    def __init__(self, input_pdf: str):
        super().__init__()
        self.setWindowTitle("SwissArmyPDF - Use Ghostscript")
        self.resize(750, 550)
        self.input_pdf = input_pdf

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Pfad anzeigen
        layout.addWidget(QLabel("Quell-PDF:"))
        self.input_label = QLabel(Path(input_pdf).name)
        self.input_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.input_label)

        # DPI
        h = QHBoxLayout()
        h.addWidget(QLabel("DPI:"))
        self.dpi_field = QLineEdit("150")
        self.dpi_field.setFixedWidth(80)
        h.addWidget(self.dpi_field)
        layout.addLayout(h)

        # Quality
        h = QHBoxLayout()
        h.addWidget(QLabel("Qualität:"))
        self.quality_field = QLineEdit("80")
        self.quality_field.setFixedWidth(80)
        h.addWidget(self.quality_field)
        layout.addLayout(h)

        # Output-Vorschlag
        h = QHBoxLayout()
        h.addWidget(QLabel("Output-Datei:"))
        self.output_field = QLineEdit()
        self.update_output_suggestion()
        self.dpi_field.textChanged.connect(self.update_output_suggestion)
        self.quality_field.textChanged.connect(self.update_output_suggestion)
        h.addWidget(self.output_field)
        layout.addLayout(h)

        # Parameter-Textfeld (mit Platzhaltern – bleibt unverändert)
        layout.addWidget(QLabel("Ghostscript Parameter (ein Parameter pro Zeile – Platzhalter {dpi} und {quality}):"))
        self.param_text = QTextEdit()
        self.param_text.setPlainText(self.build_gs_params_template())
        layout.addWidget(self.param_text)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("OK – Compress")
        btn_ok.clicked.connect(self.run_compress)
        btn_layout.addWidget(btn_ok)

        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.close)
        btn_layout.addWidget(btn_cancel)

        layout.addLayout(btn_layout)

    def build_gs_params_template(self):
        """Template mit Platzhaltern – bleibt so im Textfeld sichtbar"""
        return """-dDownsampleColorImages=true
-dColorImageResolution={dpi}
-dGrayImageResolution={dpi}
-dMonoImageResolution={dpi}
-dColorImageDownsampleType=1
-dJPEGQ={quality}
-dCompressPages=true
-dNOPAUSE
-dBATCH"""

    def update_output_suggestion(self):
        try:
            dpi = self.dpi_field.text() or "150"
            q = self.quality_field.text() or "80"
            input_path = Path(self.input_pdf)
            suggested = str(input_path.with_stem(f"{input_path.stem}_gs_{dpi}dpi_q{q}"))
            self.output_field.setText(suggested)
        except:
            self.output_field.setText("Fehler bei Vorschlag")

    def run_compress(self):
        try:
            dpi = int(self.dpi_field.text())
            quality = int(self.quality_field.text())
            if not (50 <= dpi <= 600 and 30 <= quality <= 100):
                raise ValueError("DPI: 50–600, Quality: 30–100")
        except ValueError as e:
            QMessageBox.warning(self, "Fehler", str(e))
            return

        out_path = self.output_field.text().strip()
        if not out_path:
            QMessageBox.warning(self, "Fehler", "Kein Output-Pfad")
            return

        # Template holen
        template = self.build_gs_params_template()

        # Platzhalter ersetzen (erst jetzt!)
        params_str = template.format(dpi=dpi, quality=quality)
        params = params_str.splitlines()

        gs_cmd = ["gs", "-sDEVICE=pdfwrite", "-dCompatibilityLevel=1.4"]
        for p in params:
            p = p.strip()
            if p and not p.startswith('#'):
                gs_cmd.extend(p.split())
        gs_cmd.extend(["-sOutputFile=" + out_path, self.input_pdf])

        self.statusBar().showMessage("Ghostscript wird gestartet...")

        try:
            # Für Debug: QUIET und BATCH entfernt – echte Ausgabe sichtbar
            result = subprocess.run(gs_cmd, check=True, capture_output=True, text=True)
            self.statusBar().showMessage("Ghostscript abgeschlossen")
            QMessageBox.information(self, "Erfolg", f"Komprimierung fertig!\n{out_path}\n\nAusgabe:\n{result.stdout}")
            self.close()
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr or "Kein Fehlertext (Exit 255)"
            QMessageBox.critical(self, "Fehler", f"Ghostscript fehlgeschlagen (Exit {e.returncode}):\n{error_msg}")
            self.statusBar().showMessage("Fehler – siehe Dialog")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = GSLauncherWindow()
    window.show()
    sys.exit(app.exec())