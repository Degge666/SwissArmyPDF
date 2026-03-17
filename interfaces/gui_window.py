import os
import json
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QProgressBar, QApplication, QLineEdit,
                             QTreeWidget, QTreeWidgetItem, QMenu, QHeaderView, QFrame)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt
from PyQt6.QtSql import QSqlDatabase, QSqlQuery
import fitz
from core.pdf_engine import SwissArmyPDFEngine


# --- DIESE KLASSE MUSS HIER OBEN STEHEN ---
class SortableTreeWidgetItem(QTreeWidgetItem):
    def __lt__(self, other):
        column = self.treeWidget().sortColumn()
        text1 = self.text(column)
        text2 = other.text(column)  # Fix: 'other' fehlte in deiner Version

        # Versuche numerisch zu sortieren (XREF, Size, Page)
        try:
            return float(text1) < float(text2)
        except ValueError:
            # Fallback auf String-Sortierung (Format, Hash, etc.)
            return text1.lower() < text2.lower()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.engine = SwissArmyPDFEngine()
        self.inspectors = []
        self.current_doc_id = None
        self.settings_file = "ui_settings.json"

        self.COLUMN_MAP = {
            "page": "Page",
            "xref": "XREF",
            "size": "Size [KB]",
            "pixels": "Pixel",
            "bbp": "bbp",
            "dpi": "DPI",
            "colorspace": "Colorspace",
            "subsampling": "Chroma Sub.",
            "format": "Format",
            "hash": "Content Hash",
            "transparency": "Transparency"
        }
        self.col_ids = list(self.COLUMN_MAP.keys())

        self.setWindowTitle("SwissArmyPDF Forensic Tool - Baseline")
        self.resize(1550, 900)

        # Main Layout
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.layout = QVBoxLayout(self.main_widget)

        # --- UI Komponenten Setup ---
        # 1. Zuerst den Content (Tree) erstellen
        self.setup_content_area()
        self.setup_top_bar()

        # --- Initialisierung ---
        self.init_db_connection()
        self.refresh_archive_list()
        self.load_ui_settings()
        # Stellt Sichtbarkeit/Breite wieder her
        self.setAcceptDrops(True)

    def setup_top_bar(self):
        self.top_bar = QHBoxLayout()
        self.layout.insertLayout(0, self.top_bar)

        # 1. Live-Suche (Filter)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Live-Filter (XREF, Hash)...")
        self.search_input.setFixedWidth(180)
        self.search_input.textChanged.connect(lambda: self.refresh_tree_view())

        # 2. Sortier-Kommando (Enter)
        self.sort_input = QLineEdit()
        self.sort_input.setPlaceholderText("Sortier-Cmd (z.B. size desc)...")
        self.sort_input.setFixedWidth(180)
        self.sort_input.returnPressed.connect(self.refresh_tree_view)

        self.btn_flat_view = QPushButton("Flat View: OFF")
        self.btn_flat_view.setCheckable(True)
        self.btn_flat_view.setStyleSheet("background-color: #333;")
        self.btn_flat_view.toggled.connect(self.toggle_flat_view)

        self.btn_hide_unchecked = QPushButton("Hide Unchecked")
        self.btn_hide_unchecked.setCheckable(True)
        self.btn_hide_unchecked.toggled.connect(self.apply_visibility_filter)

        self.btn_activate_inspector = QPushButton("Activate Inspector")
        self.btn_activate_inspector.clicked.connect(self.open_new_inspector)

        self.btn_columns = QPushButton("Columns ▼")
        self.btn_columns.setMenu(self.create_column_menu())

        self.expand_btn = QPushButton("Expand All")
        self.expand_btn.clicked.connect(lambda: self.main_tree.expandAll())

        self.collapse_btn = QPushButton("Collapse All")
        self.collapse_btn.clicked.connect(lambda: self.main_tree.collapseAll())

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setFixedWidth(120)

        # Hinzufügen zum Layout
        self.top_bar.addWidget(QLabel("Filter:"))
        self.top_bar.addWidget(self.search_input)
        self.top_bar.addWidget(QLabel("Sort:"))
        self.top_bar.addWidget(self.sort_input)
        self.top_bar.addWidget(self.btn_flat_view)
        self.top_bar.addWidget(self.btn_activate_inspector)
        self.top_bar.addWidget(self.btn_columns)
        self.top_bar.addWidget(self.expand_btn)
        self.top_bar.addWidget(self.collapse_btn)
        self.top_bar.addWidget(self.progress_bar)
        self.top_bar.addStretch()
        self.top_bar.addWidget(self.btn_hide_unchecked)

    def setup_content_area(self):
        self.content_area = QHBoxLayout()

        # Archive Tree (Links)
        self.archive_tree = QTreeWidget()
        self.archive_tree.setHeaderLabel("Dokumenten Archiv")
        self.archive_tree.setFixedWidth(200)
        self.archive_tree.itemClicked.connect(self.on_doc_selected)

        # Main Finder Tree (Mitte)
        self.main_tree = QTreeWidget()
        self.main_tree.setColumnCount(len(self.col_ids))
        self.main_tree.setHeaderLabels(list(self.COLUMN_MAP.values()))
        # Einfache Header-Sortierung
        self.main_tree.setSortingEnabled(True)

        # Header Features (Verschiebbar & Context Menu)
        header = self.main_tree.header()
        header.setSectionsMovable(True)
        header.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        header.customContextMenuRequested.connect(self.on_header_context_menu)

        # Persistenz-Trigger (Wiederhergestellt)
        header.sectionMoved.connect(self.save_ui_settings)
        header.sectionResized.connect(self.save_ui_settings)

        self.main_tree.itemSelectionChanged.connect(self.on_selection_changed)
        self.main_tree.itemChanged.connect(self.handle_item_changed)

        self.content_area.addWidget(self.archive_tree)
        self.content_area.addWidget(self.main_tree)
        self.layout.addLayout(self.content_area)

    def toggle_flat_view(self, checked):
        if checked:
            self.btn_flat_view.setText("Flat View: ON")
            self.btn_flat_view.setStyleSheet("background-color: #005500;")
            self.expand_btn.setEnabled(False)
            self.collapse_btn.setEnabled(False)
        else:
            self.btn_flat_view.setText("Flat View: OFF")
            self.btn_flat_view.setStyleSheet("background-color: #333;")
            self.expand_btn.setEnabled(True)
            self.collapse_btn.setEnabled(True)

        self.refresh_tree_view()

    def apply_visibility_filter(self):
        # Falls der Button noch nicht existiert oder nicht gecheckt ist,
        # machen wir nichts oder zeigen alles an.
        hide = getattr(self, 'btn_hide_unchecked', None)
        if hide is None:
            return

        hide_active = hide.isChecked()
        root = self.main_tree.invisibleRootItem()

        for i in range(root.childCount()):
            parent = root.child(i)
            data = parent.data(0, Qt.ItemDataRole.UserRole)

            if data and data.get("type") == "page":
                # Hierarchische Ansicht
                any_child_visible = False
                for j in range(parent.childCount()):
                    child = parent.child(j)
                    is_checked = child.checkState(0) == Qt.CheckState.Checked
                    # Verstecken wenn Filter aktiv UND nicht angehakt
                    child.setHidden(hide_active and not is_checked)
                    if not child.isHidden():
                        any_child_visible = True
                # Seite nur zeigen, wenn mindestens ein Bild darin sichtbar ist
                parent.setHidden(hide_active and not any_child_visible)
            else:
                # Flat View
                is_checked = parent.checkState(0) == Qt.CheckState.Checked
                parent.setHidden(hide_active and not is_checked)

    def refresh_tree_view(self):
        if self.current_doc_id is None: return
        self.main_tree.blockSignals(True)
        self.main_tree.clear()

        search = self.search_input.text().strip().lower()
        sort_cmd = self.sort_input.text().strip().lower()
        is_flat = self.btn_flat_view.isChecked()

        # 1. Sortier-Logik vorbereiten
        sort_mapping = {"size": "o.size_kb", "xref": "o.xref", "page": "p.page_num", "bbp": "i.bpc"}
        order_by = "p.page_num ASC, o.xref ASC"  # Default
        if sort_cmd:
            parts = sort_cmd.split()
            if parts[0] in sort_mapping:
                direction = "DESC" if "desc" in parts else "ASC"
                order_by = f"{sort_mapping[parts[0]]} {direction}"

        def get_col(cid):
            return self.col_ids.index(cid)

        # 2. Daten abrufen
        if is_flat:
            # FLAT VIEW: Alle Bilder direkt unter den Root
            q = QSqlQuery()
            q.prepare(f"""
                SELECT o.xref, o.size_kb, i.width, i.height, i.filter, i.bpc, 
                       i.colorspace, i.subsampling, i.img_hash, i.has_alpha, p.page_num, o.dpi
                FROM occurrences o 
                LEFT JOIN images i ON o.img_hash = i.img_hash 
                LEFT JOIN pages p ON o.page_id = p.id
                WHERE o.doc_id = ?
                ORDER BY {order_by}
            """)
            q.addBindValue(self.current_doc_id)
            q.exec()
            while q.next():
                # Hier geben wir self.main_tree als Parent mit
                self._add_image_item(q, self.main_tree, get_col, search, is_flat=True)
        else:
            # HIERARCHISCH: Erst Seiten, dann Bilder
            p_query = QSqlQuery()
            p_query.prepare("SELECT id, page_num FROM pages WHERE doc_id = ? ORDER BY page_num ASC")
            p_query.addBindValue(self.current_doc_id)
            p_query.exec()
            while p_query.next():
                pid, pnum = p_query.value(0), p_query.value(1)

                img_q = QSqlQuery()
                img_q.prepare(f"""
                    SELECT o.xref, o.size_kb, i.width, i.height, i.filter, i.bpc, 
                           i.colorspace, i.subsampling, i.img_hash, i.has_alpha, p.page_num, o.dpi
                    FROM occurrences o 
                    LEFT JOIN images i ON o.img_hash = i.img_hash 
                    LEFT JOIN pages p ON o.page_id = p.id
                    WHERE o.page_id = ? AND o.doc_id = ?
                    ORDER BY {order_by}
                """)
                img_q.addBindValue(pid)
                img_q.addBindValue(self.current_doc_id)
                img_q.exec()

                temp_items_data = []
                total_page_size = 0

                # Wir sammeln erst, um zu sehen, ob die Seite überhaupt Bilder hat (wichtig für Filter)
                while img_q.next():
                    temp_items_data.append([img_q.value(i) for i in range(12)])

                # Nur wenn Bilder da sind (unter Berücksichtigung des Filters)
                page_item = None
                for data in temp_items_data:
                    # Mock-Query Objekt für _add_image_item bauen oder Methode anpassen
                    item = self._add_image_item_from_list(data, None, get_col, search, is_flat=False)
                    if item:
                        if not page_item:
                            page_item = SortableTreeWidgetItem(self.main_tree)
                            page_item.setText(get_col("page"), f"Page {pnum}")
                            page_item.setData(0, Qt.ItemDataRole.UserRole, {"type": "page", "num": pnum})

                        page_item.addChild(item)
                        total_page_size += data[1]  # size_kb

                if page_item:
                    page_item.setText(get_col("size"), f"{total_page_size:.2f}")
                    page_item.setExpanded(True)

        self.apply_visibility_filter()
        self.main_tree.blockSignals(False)

    def _add_image_item(self, q, parent, get_col, search, is_flat):
        # Hilfsmethode, um q (QSqlQuery) in Liste zu wandeln
        data = [q.value(i) for i in range(12)]
        return self._add_image_item_from_list(data, parent, get_col, search, is_flat)

    def _add_image_item_from_list(self, data, parent, get_col, search, is_flat):
        xr, sz, w, h, flt, bpc, cs, sub, hsh, alpha, pnum, dpi = data

        # Format Mapping
        fmt_map = {"DCTDecode": "JPG", "FlateDecode": "PNG/ZLIB", "JPXDecode": "JP2000", "JBIG2Decode": "JBIG2"}
        display_fmt = fmt_map.get(flt, flt.split("/")[-1] if flt and "/" in flt else (flt if flt else "RAW"))

        # Filter
        if search:
            if not any(search in str(v).lower() for v in [xr, hsh, display_fmt]):
                return None

        # Item erstellen
        item = SortableTreeWidgetItem(parent)

        # In der flachen Ansicht schreiben wir die Seitenzahl direkt ins erste Feld
        if is_flat:
            item.setText(get_col("page"), f"P. {pnum}")

        item.setText(get_col("xref"), str(xr))
        item.setText(get_col("size"), f"{sz:.2f}")
        item.setText(get_col("pixels"), f"{w}x{h}")

        # bbp Berechnung
        try:
            comp = 3 if "RGB" in str(cs) else (4 if "CMYK" in str(cs) else 1)
            item.setText(get_col("bbp"), str(int(bpc) * comp))
        except:
            item.setText(get_col("bbp"), str(bpc))

        item.setText(get_col("dpi"), str(dpi))
        item.setText(get_col("colorspace"), str(cs))
        item.setText(get_col("subsampling"), str(sub))
        item.setText(get_col("format"), display_fmt)
        item.setText(get_col("hash"), (hsh[:12] + "...") if hsh else "N/A")
        item.setText(get_col("transparency"), "Yes" if alpha else "No")

        item.setCheckState(0, Qt.CheckState.Unchecked)
        item.setData(0, Qt.ItemDataRole.UserRole, {"type": "image", "xref": xr})
        return item

    # --- Die restlichen Methoden (create_column_menu, save_ui_settings, etc.) bleiben wie in deiner Basis ---
    def create_column_menu(self):
        menu = QMenu(self)
        if not hasattr(self, 'main_tree'): return menu
        for i, col_name in enumerate(self.COLUMN_MAP.values()):
            action = QAction(col_name, menu, checkable=True)
            action.setChecked(not self.main_tree.isColumnHidden(i))
            action.triggered.connect(lambda checked, idx=i: self.toggle_column(idx, checked))
            menu.addAction(action)
        return menu

    def toggle_column(self, idx, visible):
        self.main_tree.setColumnHidden(idx, not visible)
        self.save_ui_settings()

    def on_header_context_menu(self, pos):
        logical_idx = self.main_tree.header().logicalIndexAt(pos)
        if logical_idx < 0: return
        col_name = list(self.COLUMN_MAP.values())[logical_idx]
        menu = QMenu()
        hide_action = menu.addAction(f"Spalte '{col_name}' ausblenden")
        hide_action.triggered.connect(lambda: self.toggle_column(logical_idx, False))
        menu.exec(self.main_tree.header().mapToGlobal(pos))

    def save_ui_settings(self):
        header = self.main_tree.header()
        settings = {
            "column_states": [not self.main_tree.isColumnHidden(i) for i in range(header.count())],
            "column_widths": [self.main_tree.columnWidth(i) for i in range(header.count())],
            "column_order": [header.visualIndex(i) for i in range(header.count())]
        }
        with open(self.settings_file, "w") as f:
            json.dump(settings, f)

    def load_ui_settings(self):
        if not os.path.exists(self.settings_file): return
        try:
            with open(self.settings_file, "r") as f:
                s = json.load(f)
                header = self.main_tree.header()
                for i, visible in enumerate(s.get("column_states", [])):
                    if i < header.count(): self.main_tree.setColumnHidden(i, not visible)
                for i, width in enumerate(s.get("column_widths", [])):
                    if i < header.count(): self.main_tree.setColumnWidth(i, width)
        except Exception as e:
            print(f"UI Settings load error: {e}")

    def handle_item_changed(self, item, column):
        if column != 0: return
        self.main_tree.blockSignals(True)
        state = item.checkState(0)
        data = item.data(0, Qt.ItemDataRole.UserRole)

        if data["type"] == "page":
            for i in range(item.childCount()): item.child(i).setCheckState(0, state)
        else:
            p = item.parent()
            if p:
                checked = sum(1 for i in range(p.childCount()) if p.child(i).checkState(0) == Qt.CheckState.Checked)
                p.setCheckState(0, Qt.CheckState.Checked if checked == p.childCount() else (
                    Qt.CheckState.Unchecked if checked == 0 else Qt.CheckState.PartiallyChecked))
        self.main_tree.blockSignals(False)

    def on_selection_changed(self):
        items = self.main_tree.selectedItems()
        if not items or not self.inspectors: return
        data = items[0].data(0, Qt.ItemDataRole.UserRole)
        for insp in self.inspectors:
            if data["type"] == "image":
                insp.update_content(xref=data["xref"])
            elif data["type"] == "page":
                insp.update_content(page_num=data["num"])

    def open_new_inspector(self):
        from interfaces.inspector_window import InspectorWindow
        new_id = len(self.inspectors) + 1
        insp = InspectorWindow(self.engine, new_id)
        insp.show()
        self.inspectors.append(insp)
        insp.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        insp.destroyed.connect(lambda: self.inspectors.remove(insp))

    def on_doc_selected(self, item):
        self.current_doc_id = item.data(0, Qt.ItemDataRole.UserRole)
        query = QSqlQuery()
        query.prepare("SELECT path FROM documents WHERE id = ?")
        query.addBindValue(self.current_doc_id)
        query.exec()
        if query.next(): self.engine.current_pdf = query.value(0)
        self.refresh_tree_view()

    def init_db_connection(self):
        if not QSqlDatabase.contains("qt_sql_default_connection"):
            db = QSqlDatabase.addDatabase("QSQLITE")
            db.setDatabaseName("project_data.spdf")
            db.open()

    def refresh_archive_list(self):
        self.archive_tree.clear()
        query = QSqlQuery("SELECT id, name FROM documents ORDER BY id DESC")
        while query.next():
            item = QTreeWidgetItem([query.value(1)])
            item.setData(0, Qt.ItemDataRole.UserRole, query.value(0))
            self.archive_tree.addTopLevelItem(item)

    def update_progress(self, val):
        self.progress_bar.setValue(val)
        QApplication.processEvents()

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls(): e.accept()

    def dropEvent(self, e):
        path = e.mimeData().urls()[0].toLocalFile()
        if path.lower().endswith(".pdf"):
            self.progress_bar.setVisible(True)
            self.progress_bar.setValue(0)
            new_id = self.engine.run_full_scan(path, progress_callback=self.update_progress)
            self.progress_bar.setVisible(False)
            self.refresh_archive_list()
            self.current_doc_id = new_id
            self.refresh_tree_view()