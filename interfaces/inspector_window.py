# inspector_window.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QComboBox, QCheckBox, QPushButton)
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt


class InspectorWindow(QWidget):
    def __init__(self, engine, window_id):
        super().__init__()
        self.engine = engine
        self.window_id = window_id
        self.current_xref = None
        self.current_page = None

        self.setWindowTitle(f"Inspector #{self.window_id}")
        self.resize(400, 500)

        layout = QVBoxLayout(self)

        # --- Settings Area ---
        settings_layout = QHBoxLayout()
        self.auto_update = QCheckBox("Auto-Update")
        self.auto_update.setChecked(True)

        self.quality_mode = QComboBox()
        self.quality_mode.addItems(["Thumbnail", "Original Qualität"])

        settings_layout.addWidget(self.auto_update)
        settings_layout.addWidget(self.quality_mode)
        layout.addLayout(settings_layout)

        # --- Display Area ---
        self.info_label = QLabel("Keine Auswahl")
        self.info_label.setStyleSheet("font-weight: bold; color: #00ff00;")
        layout.addWidget(self.info_label)

        self.img_display = QLabel("Vorschau")
        self.img_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img_display.setStyleSheet("border: 1px solid #444; background: #000;")
        layout.addWidget(self.img_display, 1)  # Streckt sich

        self.manual_update_btn = QPushButton("Manuelles Update")
        self.manual_update_btn.clicked.connect(self.force_update)
        layout.addWidget(self.manual_update_btn)

    def update_content(self, xref=None, page_num=None, force=False):
        """Wird vom MainWindow aufgerufen, wenn sich die Auswahl ändert."""
        if not force and not self.auto_update.isChecked():
            return

        self.current_xref = xref
        self.current_page = page_num
        self.force_update()

    def force_update(self):
        if self.current_xref:
            self.display_image(self.current_xref)
        elif self.current_page:
            self.display_page(self.current_page)

    def display_page(self, page_num):
        self.info_label.setText(f"Inhalt: Seite {page_num}")

        # Qualitäts-Einstellung prüfen
        zoom_factor = 2.0 if self.quality_mode.currentText() == "Original Qualität" else 1.0

        data = self.engine.get_page_preview(page_num, zoom=zoom_factor)
        if data:
            pix = QPixmap()
            pix.loadFromData(data)
            self.img_display.setPixmap(pix.scaled(
                self.img_display.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            ))
        else:
            self.img_display.setText("Fehler beim Rendern der Seite")

    def display_image(self, xref):
        self.info_label.setText(f"Inhalt: XREF {xref}")
        data = self.engine.get_pixmap(xref)

        if data:
            pix = QPixmap()
            pix.loadFromData(data)

            # Bei Bildern bedeutet "Original Qualität", dass wir nicht auf die
            # Label-Größe skalieren, sondern das Fenster scrollbar machen (optional)
            # Hier skalieren wir für die Vorschau erstmal weiterhin sauber:
            self.img_display.setPixmap(pix.scaled(
                self.img_display.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            ))