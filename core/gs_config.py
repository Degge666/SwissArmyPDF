# gs_config.py oder direkt in gui_window.py
GS_TEMPLATE = """
-sDEVICE=pdfwrite
-dCompatibilityLevel=1.4
-dPDFSETTINGS=/ebook
-dDownsampleColorImages=true
-dColorImageDownsampleType=1
-dGrayImageDownsampleType=1
-dMonoImageDownsampleType=1
-dCompressPages=true
-dCompressFonts=true
-dEmbedAllFonts=true
-dSubsetFonts=true
-dNOPAUSE -dQUIET -dBATCH
-dColorImageResolution={dpi}
-dJPEGQ={quality}
"""