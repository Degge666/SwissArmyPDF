# img_processor.py
from PIL import Image

def analyze_transparency(image_path):
    """
    Check if an image has a 'ghostly veil' (alpha channel).
    Returns a dictionary for easy GUI/Terminal processing.
    """
    try:
        with Image.open(image_path) as img:
            has_alpha = img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info)
            return {
                "status": "success",
                "has_transparency": has_alpha,
                "mode": img.mode,
                "path": image_path
            }
    except Exception as e:
        return {"status": "error", "message": str(e)}
