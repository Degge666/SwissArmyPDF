#!/usr/bin/env python3
from dataclasses import dataclass
from pathlib import Path

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QFileDialog, QTextEdit, QMessageBox
)
from PyQt6.QtCore import Qt


@dataclass
class GhostscriptConfig:
    source_pdf: str
    dpi: int = 300
    quality: int = 85
    method_name: str = "CompressGS"
    # Hier können später weitere Parameter (z. B. custom_command, device, etc.) hin


class MiniGSWindow(QDialog):
    def __init__(self, config: GhostscriptConfig):
        super().__init__()
        self.setWindowTitle("Ghostscript Komprimierung")
        self.resize(800, 500)
        self.result_path: str | None = None

        self.config = config
        self.current_command = 'gs -dNOPAUSE -dBATCH -dSAFER -sDEVICE=pdfwrite ...'  # später erweiterbar

        layout = QVBoxLayout(self)

        # Source (nur Anzeige)
        layout.addWidget(QLabel(f"Source: {Path(config.source_pdf).name}"))

        # Target
        self.target_field = QLineEdit()
        self.target_field.setText(self._generate_target_name())
        layout.addWidget(QLabel("Target PDF:"))
        layout.addWidget(self.target_field)

        # DPI + Quality
        h = QHBoxLayout()
        h.addWidget(QLabel("DPI:"))
        self.dpi_field = QLineEdit(str(config.dpi))
        h.addWidget(self.dpi_field)
        h.addWidget(QLabel("Qualität:"))
        self.quality_field = QLineEdit(str(config.quality))
        h.addWidget(self.quality_field)
        layout.addLayout(h)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(QPushButton("Ghostscript-Befehl bearbeiten", clicked=self.edit_command))
        btn_layout.addWidget(QPushButton("▶️ AUSFÜHREN", clicked=self.run_ghostscript))
        layout.addLayout(btn_layout)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        layout.addWidget(self.log)

    def _generate_target_name(self):
        p = Path(self.config.source_pdf)
        return str(p.with_name(f"{p.stem}_{self.config.method_name}.pdf"))

    def edit_command(self):
        # Platzhalter für später
        QMessageBox.information(self, "Edit", "Befehl bearbeiten kommt in nächstem Schritt.")

    def run_ghostscript(self):
        # Hier später der echte Aufruf
        self.log.append("Simulierter Aufruf mit übergebenen Parametern...")
        self.result_path = self.target_field.text()
        self.accept()   # Dialog schließen mit Erfolg


# Für direkten Test
if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys
    app = QApplication(sys.argv)
    cfg = GhostscriptConfig(source_pdf="/Users/degge/Desktop/TEST/xxxXUnkomprimiert_DE_purged_purged.pdf")
    dlg = MiniGSWindow(cfg)
    dlg.exec()