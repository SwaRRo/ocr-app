# app/core/ocr_engine.py
import io
import cv2
import numpy as np
import pytesseract
from PIL import Image

# Global cache so multi-page documents process fast
_easyocr_readers = {}

def get_easyocr_reader(lang_codes: list):
    """
    Initializes and caches the EasyOCR Reader for the requested languages.
    """
    lang_key = tuple(sorted(lang_codes))
    if lang_key not in _easyocr_readers:
        import easyocr
        print(f"   [debug] Initializing EasyOCR Reader into RAM for languages: {lang_codes}...")
        _easyocr_readers[lang_key] = easyocr.Reader(lang_codes, gpu=True)
    return _easyocr_readers[lang_key]

def flush_ocr_memory():
    """
    Aggressively nukes the AI models from system RAM and GPU VRAM to keep the server lightweight when idle.
    """
    global _easyocr_readers
    _easyocr_readers.clear()  # Delete references to the loaded models
    
    import gc
    gc.collect()  # Force Python to return the freed RAM to the Linux OS
    
    try:
        import torch
        if torch.cuda.is_available():
            torch.cuda.empty_cache()  # Force PyTorch to return VRAM to the NVIDIA GPU
    except Exception:
        pass
        
    try:
        import ctypes
        libc = ctypes.CDLL("libc.so.6")
        libc.malloc_trim(0)
    except Exception as e:
        print (f" [warning] Could not run malloc_trim: {e}")
    print("   [debug] AI models flushed. RAM and VRAM successfully reclaimed.")

def extract_text_from_matrix(image_matrix: np.ndarray, lang: str = "eng") -> tuple:
    easyocr_langs = []
    if "mar" in lang:
        easyocr_langs.append("mr")
    if "eng" in lang or "en" in lang:
        easyocr_langs.append("en")
        
    if not easyocr_langs:
        easyocr_langs = ["en"]

    try:
        reader = get_easyocr_reader(easyocr_langs)
        results = reader.readtext(image_matrix)
        
        text_lines = [item[1] for item in results]
        scores = [item[2] for item in results]
        avg_confidence = (sum(scores) / len(scores)) * 100.0 if scores else 0.0
        
        return "\n".join(text_lines), avg_confidence
        
    except Exception as e:
        print(f"   [warning] EasyOCR extraction failed, falling back to Tesseract: {e}")
        gray = cv2.cvtColor(image_matrix, cv2.COLOR_BGR2GRAY)
        data = pytesseract.image_to_data(gray, lang=lang, output_type=pytesseract.Output.DICT)
        conf_list = [int(c) for c in data['conf'] if int(c) != -1]
        avg_confidence = sum(conf_list) / len(conf_list) if conf_list else 0.0
        
        custom_config = "--psm 3 -c load_system_dawg=1"
        text = pytesseract.image_to_string(gray, lang=lang, config=custom_config)
        return text, avg_confidence

def ocr_matrix_to_pdf_bytes(image_matrix: np.ndarray, lang: str = "eng") -> bytes:
    rgb = cv2.cvtColor(image_matrix, cv2.COLOR_BGR2RGB)
    custom_config = "--psm 3 -c load_system_dawg=1"
    pdf_bytes = pytesseract.image_to_pdf_or_hocr(rgb, lang=lang, config=custom_config, extension="pdf")
    return pdf_bytes
