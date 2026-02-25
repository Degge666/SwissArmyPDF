# SwissArmyPDF (sAPDF) - v0.1 ⍺ 🇨🇭📄

A precision forensic toolchain for PDF reconnaissance, asset looting, and surgical optimization. Developed for security researchers and power users who need deep insights into PDF structures.

## 🛡️ System Intelligence
Developed and tested under the following conditions:
* **OS:** Darwin 25.3.0 (macOS)
* **Python:** v3.14.0
* **Core:** PyMuPDF (fitz) v1.27.1
* **External Support:** Ghostscript v10.06.0

## ⚔️ Tactical Modules

### 🔍 Recon & Analysis
* **Scout & Deep Recon:** Tables for page sizes, embedded images, DPI estimations, and colorspace analysis.
* **Technical Intel:** Scans for active content (JavaScript), encryption, and cleanable data waste.

### 💰 Looting & Extraction
* **Loot Mission:** Automated extraction of all embedded images.
* **Intelligent JPG Export:** High-precision page-to-image conversion with proportional scaling or "Fit-In" logic (e.g., `<=` width/height constraints).

### ⚡ Manipulation & Sabotage
* **Heavy Strike:** Radical file size reduction via Ghostscript while preserving text layers.
* **Smart Sabotage:** Targeted DPI reduction for oversized images only.
* **Purge:** Deep cleaning of PDF objects to remove hidden overhead.

## 🚀 Installation

1. **Clone the Vault:**
   ```bash
   git clone https://github.com/Degge666/SwissArmyPDF.git
   cd SwissArmyPDF
   
2. **Equip Dependencies:**
   ```bash
   pip install -r requirements.txt
   
* Note: Ensure Ghostscript is installed on your system for "Heavy Strike" operations.

3. **Enter the Vault:
   ```bash
   python swithArmyPdf.py
   
## ⚖️ License & Disclaimer
This tool is provided under the MIT License. Use it wisely. The authors are not responsible for any data loss or corrupted scrolls resulting from the use of this software.

Status: Alpha v0.1 - The forge is still hot.