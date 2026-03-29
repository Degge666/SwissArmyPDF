#!/usr/bin/env python3
"""
SwissView - Unified Viewer (Page + XREF in same viewport)
"""

import sys
from pathlib import Path

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QToolBar,
    QStatusBar, QFileDialog, QScrollArea,
    QDockWidget, QTreeWidget, QTreeWidgetItem
)
from PyQt6.QtGui import QPixmap, QAction, QKeySequence
from PyQt6.QtCore import Qt

from PIL import Image, ImageDraw, ImageFont, ImageQt
import pypdfium2 as pdfium
import fitz  # PyMuPDF


class SwissView(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("SwissView - PDF Viewer")
        self.resize(1280, 860)

        # --- Core state ---
        self.current_doc = None
        self.current_pdf_path = None
        self.current_page = 0

        # Viewer mode
        self.MODE_PAGE = "page"
        self.MODE_XREF = "xref"
        self.current_mode = self.MODE_PAGE
        self.current_xref = None  # (type, id)

        # Zoom
        self.current_zoom = 1.0
        self.saved_zooms = {}
        self.base_dpi = 144

        self.init_ui()

    # ---------------- UI ---------------- #

    def init_ui(self):
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)

        open_action = QAction("Open PDF...", self)
        open_action.triggered.connect(self.open_pdf_dialog)
        toolbar.addAction(open_action)

        toolbar.addSeparator()

        prev_action = QAction("◀ Previous", self)
        prev_action.setShortcut(QKeySequence("Left"))
        prev_action.triggered.connect(self.prev_page)
        toolbar.addAction(prev_action)

        self.page_label = QLabel("Page 0 / 0")
        toolbar.addWidget(self.page_label)

        next_action = QAction("Next ▶", self)
        next_action.setShortcut(QKeySequence("Right"))
        next_action.triggered.connect(self.next_page)
        toolbar.addAction(next_action)

        toolbar.addSeparator()

        # Back to page button
        self.back_action = QAction("Back to Page", self)
        self.back_action.triggered.connect(self.back_to_page)
        self.back_action.setEnabled(False)
        toolbar.addAction(self.back_action)

        toolbar.addSeparator()

        fit_w = QAction("Fit Width", self)
        fit_w.triggered.connect(self.fit_to_width)
        toolbar.addAction(fit_w)

        fit_h = QAction("Fit Height", self)
        fit_h.triggered.connect(self.fit_to_height)
        toolbar.addAction(fit_h)

        fit_f = QAction("Fit Frame", self)
        fit_f.triggered.connect(self.fit_to_frame)
        toolbar.addAction(fit_f)

        toolbar.addSeparator()

        zoom_out = QAction("- Zoom", self)
        zoom_out.setShortcut(QKeySequence("Ctrl+-"))
        zoom_out.triggered.connect(self.zoom_out)
        toolbar.addAction(zoom_out)

        self.zoom_label = QLabel("Zoom: 1.0x")
        toolbar.addWidget(self.zoom_label)

        zoom_in = QAction("+ Zoom", self)
        zoom_in.setShortcut(QKeySequence("Ctrl++"))
        zoom_in.triggered.connect(self.zoom_in)
        toolbar.addAction(zoom_in)

        # --- Central viewer ---
        self.scroll_area = QScrollArea()
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll_area.setWidget(self.image_label)
        self.scroll_area.setWidgetResizable(True)
        self.setCentralWidget(self.scroll_area)

        # --- XREF tree ---
        self.xref_dock = QDockWidget("XREF Inspector", self)
        self.xref_tree = QTreeWidget()
        self.xref_tree.setHeaderLabel("XREF Objects")
        self.xref_tree.itemClicked.connect(self.on_xref_clicked)
        self.xref_dock.setWidget(self.xref_tree)

        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.xref_dock)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

    # ---------------- PDF ---------------- #

    def open_pdf_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open PDF", "", "PDF Files (*.pdf)")
        if file_path:
            self.open_pdf(file_path)

    def open_pdf(self, file_path: str):
        try:
            self.current_pdf_path = file_path
            self.current_doc = pdfium.PdfDocument(file_path)

            self.current_page = 0
            self.current_mode = self.MODE_PAGE
            self.saved_zooms.clear()

            self.extract_xrefs()
            self.render_page()

            self.status_bar.showMessage(f"Loaded: {Path(file_path).name}")

        except Exception as e:
            self.status_bar.showMessage(f"Error: {e}")

    # ---------------- Rendering ---------------- #

    def render_page(self):
        """Render PDF page."""
        if not self.current_doc:
            return

        self.current_mode = self.MODE_PAGE
        self.current_xref = None
        self.back_action.setEnabled(False)

        if self.current_page in self.saved_zooms:
            self.current_zoom = self.saved_zooms[self.current_page]

        try:
            page = self.current_doc[self.current_page]
            scale = self.current_zoom * (self.base_dpi / 72.0)

            pil_image = page.render(scale=scale).to_pil()
            qimage = ImageQt.ImageQt(pil_image)

            self.image_label.setPixmap(QPixmap.fromImage(qimage))

            self.page_label.setText(f"Page {self.current_page + 1} / {len(self.current_doc)}")
            self.zoom_label.setText(f"Zoom: {self.current_zoom:.2f}x")

        except Exception as e:
            self.status_bar.showMessage(f"Render error: {e}")

    def render_xref(self):
        """Render selected XREF in same viewer."""
        if not self.current_xref or not self.current_pdf_path:
            return

        self.current_mode = self.MODE_XREF
        self.back_action.setEnabled(True)

        obj_type, obj_id = self.current_xref

        try:
            doc = fitz.open(self.current_pdf_path)
            page = doc[self.current_page]

            if obj_type == "image":
                for img in page.get_images(full=True):
                    if str(img[0]) == obj_id:
                        pix = fitz.Pixmap(doc, img[0])

                        # scale XREF with same zoom
                        img_data = pix.tobytes("png")
                        qpixmap = QPixmap()
                        qpixmap.loadFromData(img_data, "PNG")

                        scaled = qpixmap.scaled(
                            qpixmap.size() * self.current_zoom,
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation
                        )

                        self.image_label.setPixmap(scaled)
                        self.page_label.setText(f"XREF Image {obj_id}")
                        break

            doc.close()

        except Exception as e:
            self.status_bar.showMessage(f"XREF error: {e}")

    # ---------------- Navigation ---------------- #

    def next_page(self):
        if self.current_doc and self.current_page < len(self.current_doc) - 1:
            self.saved_zooms[self.current_page] = self.current_zoom
            self.current_page += 1

            # auto return to page mode
            self.current_mode = self.MODE_PAGE

            self.extract_xrefs()
            self.render_page()

    def prev_page(self):
        if self.current_page > 0:
            self.saved_zooms[self.current_page] = self.current_zoom
            self.current_page -= 1

            self.current_mode = self.MODE_PAGE

            self.extract_xrefs()
            self.render_page()

    def back_to_page(self):
        self.render_page()

    # ---------------- Zoom ---------------- #

    def zoom_in(self):
        self.current_zoom = min(5.0, self.current_zoom + 0.25)
        self.refresh_view()

    def zoom_out(self):
        self.current_zoom = max(0.1, self.current_zoom - 0.25)
        self.refresh_view()

    def refresh_view(self):
        if self.current_mode == self.MODE_PAGE:
            self.render_page()
        else:
            self.render_xref()

    def fit_to_width(self):
        if self.current_mode != self.MODE_PAGE:
            return

        page = self.current_doc[self.current_page]
        page_width = page.get_size()[0]
        viewport_width = self.scroll_area.viewport().width()

        self.current_zoom = (viewport_width / page_width) * (72.0 / self.base_dpi)
        self.refresh_view()

    def fit_to_height(self):
        if self.current_mode != self.MODE_PAGE:
            return

        page = self.current_doc[self.current_page]
        page_height = page.get_size()[1]
        viewport_height = self.scroll_area.viewport().height()

        self.current_zoom = (viewport_height / page_height) * (72.0 / self.base_dpi)
        self.refresh_view()

    def fit_to_frame(self):
        if self.current_mode != self.MODE_PAGE:
            return

        page = self.current_doc[self.current_page]
        w, h = page.get_size()

        vw = self.scroll_area.viewport().width()
        vh = self.scroll_area.viewport().height()

        zoom_w = (vw / w) * (72.0 / self.base_dpi)
        zoom_h = (vh / h) * (72.0 / self.base_dpi)

        self.current_zoom = min(zoom_w, zoom_h)
        self.refresh_view()

    # ---------------- XREF ---------------- #

    def extract_xrefs(self):
        self.xref_tree.clear()

        root = QTreeWidgetItem([f"Page {self.current_page + 1}"])
        root.setData(0, Qt.ItemDataRole.UserRole, ("page", None))
        self.xref_tree.addTopLevelItem(root)

        try:
            doc = fitz.open(self.current_pdf_path)
            page = doc[self.current_page]

            for img in page.get_images(full=True):
                xref = img[0]
                item = QTreeWidgetItem(root)
                item.setText(0, f"[IMAGE] XREF {xref}")
                item.setData(0, Qt.ItemDataRole.UserRole, ("image", str(xref)))

            doc.close()

        except Exception as e:
            item = QTreeWidgetItem(root)
            item.setText(0, f"Error: {e}")

        self.xref_tree.expandAll()

    def on_xref_clicked(self, item):
        data = item.data(0, Qt.ItemDataRole.UserRole)
        if not data:
            return

        obj_type, obj_id = data

        if obj_type == "page":
            self.render_page()
        else:
            self.current_xref = (obj_type, obj_id)
            self.render_xref()


# ---------------- MAIN ---------------- #

if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = SwissView()
    viewer.show()
    sys.exit(app.exec())
