# SwissArmyPDF (sAPDF) Toolkit – v0.3.1 ⍺

A precision forensic and manipulation toolchain for PDFs.

## 🛡️ System Info
* **Version**  **0.3.1 ⍺** – stable two-tree baseline

Developed and tested under:
* **OS:** macOS (Darwin)
* **Python:** v3.14
* **Core Engine:** PyMuPDF (fitz) v1.23
* **Storage:** SQLite3 (Persistent Forensic Database)
* **GUI:** PyQt6
* **Current Branch** `feature/refactoring-baseline`

## ⚔️ Current Capabilities (v0.3.1 ⍺)

### 🔍 Forensic Recon & Archive
- Persistent document archive in SQLite (`project_data.spdf`)
- Full PDF scan: pages, images, XREFs, MD5 hashes, DPI (V2.0 mean-value), colorspace, bbp (bytes per pixel), subsampling
- Two-tree GUI structure:
  - **Original Documents** (top) – imported via drag & drop
  - **Derived Documents** (bottom) – created via Purge Waste or other manipulations
- Correct parent-child registration (`parent_doc_id`) for derived files

### 🛠️ Manipulation Layer
- **Purge Waste**: Removes garbage objects (garbage=4 + deflate + clean) via modular pipeline
- **Pipeline architecture** in `core/manipulate.py` – easy to extend with new tasks
- Save dialog for output file with automatic `_purged` suffix suggestion

### 📊 Analysis Interface
- Hierarchical / Flat view toggle
- Live filter (XREF, hash, format)
- Sortable columns (size, XREF, DPI, bbp, …)
- Checkboxes + "Hide Unchecked" to focus on relevant findings
- Inspector windows for page/image preview

## 🏁 Usability & Stability
- Drag & Drop import always creates **original** entries
- Purge Waste always creates **derived** entries (linked via `parent_doc_id`)
- Robust handling of SQLite `NULL` vs empty string quirks in Qt
- Progress bar during long scans
- Status bar feedback

## 🚀 Quick Start

    ```bash
    # 1. Clone the repository
    git clone https://github.com/Degge666/SwissArmyPDF.git
    cd SwissArmyPDF

    # 2. Launch (creates venv + installs deps if needed)
    chmod +x setup.sh
    ./setup.sh

## ⚖️ License & Disclaimer
MIT License – use at your own risk.
The authors are not responsible for data loss, corrupted files, forensic traceability issues or any legal consequences resulting from the use of this tool.
Handle with care.

## 🗺️ Roadmap (short-term priorities)

 [ ] Hierarchical tree view (nested derived documents under parents)
 [ ] Tooltip & status bar enhancements
 [ ] Surgical export of selected images/assets with metadata
 [ ] JPEG SOF marker parsing for exact subsampling
 [ ] PDF patching / re-injection of optimized assets
___
Status: V0.3.0 ⍺ -Baseline (Refactored) - The forge is active.