# Ausblick auf die Struktur der core/sabotage.py
class PDFTask:
    """Basisklasse für eine einzelne Manipulation"""
    def execute(self, doc):
        raise NotImplementedError

class PurgeTask(PDFTask):
    def execute(self, doc):
        # Logik für garbage=4
        return doc

class PDFPipeline:
    """Verwaltet die Abfolge der Schritte"""
    def __init__(self, input_path):
        self.doc = fitz.open(input_path)
        self.tasks = []

    def add_task(self, task):
        self.tasks.append(task)

    def run(self, output_path):
        for task in self.tasks:
            self.doc = task.execute(self.doc)
        self.doc.save(output_path, ...)