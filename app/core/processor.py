# app/core/processor.py
import os
import cv2
import numpy as np
from PIL import Image, ImageOps
from pdf2image import convert_from_path

def pil_to_opencv(pil_image) -> np.ndarray:
    """
    Converts a PIL image into an OpenCV BGR NumPy array safely.
    Forces RGB mode first to prevent crashes on binary or grayscale scans.
    """
    if pil_image.mode != "RGB":
        pil_image = pil_image.convert("RGB")
        
    array = np.array(pil_image)
    bgr_array = cv2.cvtColor(array, cv2.COLOR_RGB2BGR)
    return bgr_array

def scale_image_dpi(image_matrix: np.ndarray, current_dpi: int, target_dpi: int = 300) -> np.ndarray:
    """
    Resizes an OpenCV BGR matrix to match the target DPI using bicubic interpolation.
    Only upscales if the current DPI is lower than the target DPI.
    """
    if current_dpi >= target_dpi:
        return image_matrix
    
    scale_factor = target_dpi / current_dpi
    new_width = int(image_matrix.shape[1] * scale_factor)
    new_height = int(image_matrix.shape[0] * scale_factor)
    
    scaled_matrix = cv2.resize(image_matrix, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
    return scaled_matrix

def preprocess_file(file_path: str, target_dpi: int = 300) -> list:
    """
    Loads any PDF or Image, applies EXIF rotation tags, and scales it to 300 DPI [1.1.2, 2].
    (All manual rotation, binarization, and dual-stream complexity are removed).
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The input file path does not exist: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()
    bgr_matrices = []

    # --- INGESTION STAGE ---
    if ext == ".pdf":
        pil_pages = convert_from_path(file_path, dpi=target_dpi)
        for page in pil_pages:
            opencv_page = pil_to_opencv(page)
            bgr_matrices.append(opencv_page)
            
    elif ext in [".jpg", ".jpeg", ".png", ".tiff", ".bmp", ".webp"]:
        img = Image.open(file_path)
        img = ImageOps.exif_transpose(img)
        
        # Safely extract DPI, default to 72 if missing
        dpi_info = img.info.get('dpi', (72, 72))
        if isinstance(dpi_info, (tuple, list)) and len(dpi_info) > 0:
            current_dpi = dpi_info[0]
        elif isinstance(dpi_info, (int, float)):
            current_dpi = dpi_info
        else:
            current_dpi = 72
        
        opencv_img = pil_to_opencv(img)
        scaled_img = scale_image_dpi(opencv_img, current_dpi, target_dpi)
        bgr_matrices.append(scaled_img)
        
    else:
        raise ValueError(f"Unsupported file format: {ext}")

    # --- ENHANCEMENT STAGE ---
    final_processed_pages = []
    for page_matrix in bgr_matrices:
        final_processed_pages.append(page_matrix)

    return final_processed_pages

def save_processed_pages(pages: list, original_filename: str, output_directory: str = "data/output"):
    """
    Saves a list of OpenCV matrices as physical PNG files to disk 
    so you can inspect them visually on your computer.
    """
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    base_name = os.path.splitext(os.path.basename(original_filename))[0]
    for index, page_matrix in enumerate(pages):
        output_path = os.path.join(output_directory, f"{base_name}_page_{index + 1}.png")
        cv2.imwrite(output_path, page_matrix)
        print(f"   [debug] Saved processed output to: {output_path}")
