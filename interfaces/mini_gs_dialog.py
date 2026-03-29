#!/usr/bin/env python3
"""
SwissArmyPDF – Sehr minimale Ghostscript GUI
"""

import sys
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QFileDialog, QTextEdit, QMessageBox
)
from PyQt6.QtCore import Qt


class MiniMainGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SwissArmyPDF – Mini Ghostscript")
        self.resize(780, 520)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(12)

        # === Source PDF Pfad (mit deinem Default) ===
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("Source PDF:"))

        self.path_field = QLineEdit()
        self.path_field.setText("/Users/degge/Desktop/TEST/xxxXUnkomprimiert_DE_purged_purged.pdf")
        self.path_field.setMinimumWidth(500)
        path_layout.addWidget(self.path_field)

        btn_select = QPushButton("Auswählen...")
        btn_select.clicked.connect(self.select_pdf)
        path_layout.addWidget(btn_select)

        layout.addLayout(path_layout)

        # === Auflösung + Qualität ===
        param_layout = QHBoxLayout()
        param_layout.addWidget(QLabel("Auflösung (dpi):"))
        self.dpi_field = QLineEdit("300")
        self.dpi_field.setFixedWidth(100)
        param_layout.addWidget(self.dpi_field)

        param_layout.addWidget(QLabel("Qualität (1-100):"))
        self.quality_field = QLineEdit("85")
        self.quality_field.setFixedWidth(100)
        param_layout.addWidget(self.quality_field)
        param_layout.addStretch()
        layout.addLayout(param_layout)

        # === Buttons ===
        btn_layout = QHBoxLayout()

        self.btn_edit = QPushButton("✏️ Ghostscript-Befehl bearbeiten")
        self.btn_edit.clicked.connect(self.edit_command)
        btn_layout.addWidget(self.btn_edit)

        self.btn_run = QPushButton("▶️ Ghostscript AUSFÜHREN")
        self.btn_run.clicked.connect(self.run_ghostscript)
        self.btn_run.setStyleSheet("font-weight: bold; padding: 8px;")
        btn_layout.addWidget(self.btn_run)

        layout.addLayout(btn_layout)

        # === Log Fenster ===
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        layout.addWidget(self.log)

        # Default Ghostscript Command
        self.current_command = (
            'gs -dNOPAUSE -dBATCH -dSAFER -sDEVICE=png16m '
            '-r{resolution} -dJPEGQ={quality} '
            '-dTextAlphaBits=4 -dGraphicsAlphaBits=4 '
            '-sOutputFile="output_%03d.png" "{input_file}"'
        )

        self.log.append("Mini GUI gestartet. Default-Pfad ist vorausgefüllt.")

    def select_pdf(self):
        file, _ = QFileDialog.getOpenFileName(self, "Source PDF auswählen", "", "PDF (*.pdf)")
        if file:
            self.path_field.setText(file)
            self.log.append(f"[INFO] Neuer Pfad ausgewählt: {file}")

    def edit_command(self):
        # Einfaches Edit-Fenster (kann später noch schöner gemacht werden)
        dialog = QMainWindow(self)
        dialog.setWindowTitle("Ghostscript-Befehl bearbeiten")
        dialog.resize(950, 550)

        widget = QWidget()
        lay = QVBoxLayout(widget)
        lay.addWidget(QLabel("Bearbeite den vollständigen Befehl.\n"
                             "Platzhalter: {resolution}, {quality}, {input_file}"))

        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(self.current_command)
        lay.addWidget(self.text_edit)

        btn_lay = QHBoxLayout()
        btn_lay.addWidget(QPushButton("Speichern", clicked=lambda: self.save_command(dialog)))
        btn_lay.addWidget(QPushButton("Abbrechen", clicked=dialog.close))
        lay.addLayout(btn_lay)

        dialog.setCentralWidget(widget)
        dialog.show()

    def save_command(self, dialog):
        self.current_command = self.text_edit.toPlainText().strip()
        dialog.close()
        self.log.append("[INFO] Befehl wurde gespeichert.")

    def run_ghostscript(self):
        input_file = self.path_field.text().strip()

        if not input_file or not Path(input_file).exists():
            QMessageBox.warning(self, "Fehler", "Die angegebene PDF-Datei existiert nicht!")
            return

        try:
            resolution = self.dpi_field.text().strip()
            quality = self.quality_field.text().strip()

            cmd = self.current_command.format(
                resolution=resolution,
                quality=quality,
                input_file=input_file
            )

            self.log.append(f"\n[START] DPI: {resolution} | Qualität: {quality}")
            self.log.append(f"[CMD]  {cmd}")
            self.log.append("-" * 90)

            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=120)

            if result.returncode == 0:
                self.log.append("✅ Ghostscript erfolgreich abgeschlossen!")
            else:
                self.log.append("❌ Fehler bei der Ausführung:")
                self.log.append(result.stderr)
        except Exception as e:
            QMessageBox.critical(self, "Fehler", str(e))
            self.log.append(f"[EXCEPTION] {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MiniMainGUI()
    window.show()
    sys.exit(app.exec())