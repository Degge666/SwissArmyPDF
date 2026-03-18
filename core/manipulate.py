# core/manipulate.py
import fitz
from pathlib import Path
from typing import List, Callable, Optional

class ManipulateTask:
    def __init__(self, name: str, action_func: Callable):
        self.name = name
        self.action_func = action_func

class Pipeline:
    def __init__(self):
        self.tasks: List[ManipulateTask] = []
        # self.intermediate_steps = False
        # self.steps_dir = None

    def add_task(self, task: ManipulateTask):
        self.tasks.append(task)

    def run(self, input_path: str, output_path: Optional[str] = None) -> str:
        doc = fitz.open(input_path)
        for task in self.tasks:
            doc = task.action_func(doc)

        if output_path is None:
            base = Path(input_path)
            output_path = str(base.with_stem(base.stem + "_purged"))

        doc.save(output_path, garbage=4, clean=True, deflate=True)
        doc.close()
        return output_path

    def enable_intermediate_steps(self, steps_dir: str):
        self.intermediate_steps = True
        self.steps_dir = Path(steps_dir)
        self.steps_dir.mkdir(parents=True, exist_ok=True)

# === PURGE WASTE TASK (exakt deine alte Logik) ===
def purge_waste_action(doc: fitz.Document) -> fitz.Document:
    """PurgeWaste – garbage=4 + clean + deflate"""
    temp_path = Path("temp_purge_buffer.pdf")
    doc.save(str(temp_path), garbage=4, clean=True, deflate=True)
    new_doc = fitz.open(str(temp_path))
    temp_path.unlink(missing_ok=True)
    return new_doc