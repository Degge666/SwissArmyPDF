# gs_presets.txt – Ghostscript-Presets für SwissArmyPDF
# Format: Typ: Parameter-String (ein Parameter pro Zeile)

Typ 1 (Aggressiv):
-dDownsampleColorImages=true
-dColorImageResolution=72
-dGrayImageResolution=72
-dMonoImageResolution=72
-dColorImageDownsampleType=1
-dJPEGQ=60
-dCompressPages=true
-dNOPAUSE
-dBATCH

Typ 2 (Ausgewogen):
-dDownsampleColorImages=true
-dColorImageResolution=150
-dGrayImageResolution=150
-dMonoImageResolution=150
-dColorImageDownsampleType=1
-dJPEGQ=80
-dCompressPages=true
-dNOPAUSE
-dBATCH

Typ 3 (Hochqualitativ):
-dDownsampleColorImages=true
-dColorImageResolution=300
-dGrayImageResolution=300
-dMonoImageResolution=300
-dColorImageDownsampleType=1
-dJPEGQ=92
-dCompressPages=true
-dNOPAUSE
-dBATCH

selfdefined:
-dDownsampleColorImages=true
-dColorImageResolution={dpi}
-dGrayImageResolution={dpi}
-dMonoImageResolution={dpi}
-dColorImageDownsampleType=1
-dJPEGQ={quality}
-dCompressPages=true
-dNOPAUSE
-dBATCH