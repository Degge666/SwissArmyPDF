#core/database.py

class PDFProjectDB:
    def __init__(self, db_path="project_data.spdf"):
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.create_schema()

    def create_schema(self):
        cursor = self.conn.cursor()
        cursor.executescript('''
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT, path TEXT, size_bytes INTEGER, imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS pages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_id INTEGER, page_num INTEGER, content_size_kb REAL,
                FOREIGN KEY(doc_id) REFERENCES documents(id)
            );
            CREATE TABLE IF NOT EXISTS images (
                img_hash TEXT PRIMARY KEY, width INTEGER, height INTEGER,
                bpc INTEGER, colorspace TEXT, filter TEXT
            );
            CREATE TABLE IF NOT EXISTS occurrences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doc_id INTEGER, page_id INTEGER, img_hash TEXT,
                xref INTEGER, size_kb REAL, transparent INTEGER,
                FOREIGN KEY(page_id) REFERENCES pages(id),
                FOREIGN KEY(img_hash) REFERENCES images(img_hash)
            );
        ''')
        self.conn.commit()

    def add_document(self, name, path, size):
        c = self.conn.cursor()
        c.execute("INSERT INTO documents (name, path, size_bytes) VALUES (?, ?, ?)", (name, path, size))
        self.conn.commit()
        return c.lastrowid

    def add_page(self, doc_id, num, size):
        c = self.conn.cursor()
        c.execute("INSERT INTO pages (doc_id, page_num, content_size_kb) VALUES (?, ?, ?)", (doc_id, num, size))
        self.conn.commit()
        return c.lastrowid

    def add_occurrence(self, doc_id, page_id, img_data):
        c = self.conn.cursor()
        c.execute("INSERT OR IGNORE INTO images VALUES (?, ?, ?, ?, ?, ?)",
                  (img_data['hash'], img_data['width'], img_data['height'],
                   img_data['bpc'], img_data['colorspace'], img_data['filter']))
        c.execute("INSERT INTO occurrences (doc_id, page_id, img_hash, xref, size_kb, transparent) VALUES (?, ?, ?, ?, ?, ?)",
                  (doc_id, page_id, img_data['hash'], img_data['xref'], img_data['size_kb'], img_data['transparent']))
        self.conn.commit()