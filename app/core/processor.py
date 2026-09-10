# app/core/processor.py
import os
import cv2
import numpy as np
from PIL import Image, ImageOps
from pdf2image import convert_from_path

def pil_to_opencv(pil_image) -> np.ndarray:
    if pil_image.mode != "RGB":
        pil_image = pil_image.convert("RGB")
    array = np.array(pil_image)
    return cv2.cvtColor(array, cv2.COLOR_RGB2BGR)

def scale_image_dpi(image_matrix: np.ndarray, current_dpi: int, target_dpi: int = 200) -> np.ndarray:
    MAX_WIDTH = 3000  # Safety ceiling to prevent VRAM overflow
    
    scale_factor = target_dpi / current_dpi
    new_width = int(image_matrix.shape[1] * scale_factor)
    new_height = int(image_matrix.shape[0] * scale_factor)
    
    if new_width > MAX_WIDTH:
        ratio = MAX_WIDTH / new_width
        new_width = MAX_WIDTH
        new_height = int(new_height * ratio)
    
    return cv2.resize(image_matrix, (new_width, new_height), interpolation=cv2.INTER_CUBIC)

def preprocess_file(file_path: str, target_dpi: int = 200) -> list:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The input file path does not exist: {file_path}")

    ext = os.path.splitext(file_path)[1].lower()
    bgr_matrices = []

    if ext == ".pdf":
        pil_pages = convert_from_path(file_path, dpi=target_dpi)
        for page in pil_pages:
            bgr_matrices.append(pil_to_opencv(page))
            
    elif ext in [".jpg", ".jpeg", ".png", ".tiff", ".bmp", ".webp"]:
        img = Image.open(file_path)
        img = ImageOps.exif_transpose(img)
        
        dpi_info = img.info.get('dpi', (72, 72))
        current_dpi = dpi_info[0] if isinstance(dpi_info, (tuple, list)) else 72
        
        opencv_img = pil_to_opencv(img)
        scaled_img = scale_image_dpi(opencv_img, current_dpi, target_dpi)
        bgr_matrices.append(scaled_img)
    else:
        raise ValueError(f"Unsupported file format: {ext}")

    return bgr_matrices

def save_processed_pages(pages: list, original_filename: str, output_directory: str = "data/output"):
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    base_name = os.path.splitext(os.path.basename(original_filename))[0]
    for index, page_matrix in enumerate(pages):
        output_path = os.path.join(output_directory, f"{base_name}_page_{index + 1}.png")
        cv2.imwrite(output_path, page_matrix)
        print(f"   [debug] Saved processed output to: {output_path}")
