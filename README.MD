# SwissArmyPDF (sAPDF) Toolkit - v0.3.0 ⍺ -Baseline 🇨🇭📄

A precision forensic toolchain for PDF reconnaissance, asset looting, and surgical optimization. Built for security researchers and digital forensics who need deep insights into PDF structures via a database-driven interface.

## 🛡️ Tactical Intelligence (System Info)
Developed and tested under:
* **OS:** macOS (Darwin) / Linux / Windows
* **Python:** v3.14+
* **Core Engine:** PyMuPDF (fitz) v1.27+
* **Storage:** SQLite3 (Persistent Forensic Database)
* **GUI:** PyQt6

## ⚔️ Tactical Modules & V2 Features

### 🔍 Forensic Recon (New in V2)
* **Persistent Archive:** Every scanned PDF is stored in a local SQLite database (`project_data.spdf`).
* **Deep Asset Inspection:** High-detail tables showing:
    * **XREF & Hashes:** Unique identification of embedded objects.
    * **DPI & Resolution:** Real-time calculation of effective image resolution.
    * **Color Intelligence:** Colorspace decoding (RGB, CMYK, Grayscale) and Chroma Subsampling detection.
* **Smart Filtering:** Live-Search for XREFs/Hashes and numerical sorting for sizes and page numbers.

### 💰 Looting & Extraction
* **Hierarchical vs. Flat View:** Switch between "Page-grouped" view and a global "Flat list" of all assets.
* **Targeted Selection:** Use the "Hide Unchecked" feature to focus on specific forensic findings.
* **Alpha Detection:** Identify transparency/alpha channels before conversion to prevent data loss.

### ⚡ Manipulation & Infrastructure
* **Modular Design:** Clean separation between `core` (Engine) and `interfaces` (GUI).
* **Cross-Platform Setup:** Automatic dependency check and environment launch via `setup.sh`.

## 🚀 Deployment

1. **Clone the Vault:**
   ```bash
   git clone [https://github.com/Degge666/SwissArmyPDF.git](https://github.com/Degge666/SwissArmyPDF.git)
   cd SwissArmyPDF
   
2. **Equip & Launch:**
The included setup.sh handles virtual environments and dependencies automatically:
   ```bash
   chmod +x setup.sh
   ./setup.sh

## ⚖️ License & Disclaimer
This tool is provided under the MIT License. Use it wisely. The authors are not responsible for any data loss or corrupted scrolls resulting from the use of this software.

___
Status: V0.3.0 ⍺ -Baseline (Refactored) - The forge is active.

# 🗺️ Roadmap & Current Missions
[ ] Surgical Export: Implementation of a dedicated export engine to dump selected loot into structured directories with metadata manifests (JSON).

[ ] JPEG Header Parsing: Deep-dive into SOF markers for exact Chroma Subsampling values.

[ ] PDF Patching: Re-injecting optimized assets back into the original PDF structure.