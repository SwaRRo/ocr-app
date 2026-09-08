# Multilingual OCR Document Engine

A GPU-accelerated, deep-learning OCR pipeline for processing legal court documents, ancient scriptures, and standard PDFs. It features automatic EXIF alignment, 300 DPI upscaling, and native double-layer Searchable PDF generation.

## Features
* **Zero-Trust Architecture:** Runs rootless and processes data entirely in volatile memory (`/tmp`), leaving no traces on the host.
* **Dual-Engine:** Uses **EasyOCR (PyTorch)** for high-accuracy Devanagari/Marathi/Hindi/English extraction, and **Tesseract** for searchable PDF formatting.

---

## How to Run the Container

You do not need to download the source code. You can run the pre-built, fully self-contained application using Podman or Docker.
In just 2 steps:

### 1. Create a `compose.yaml` file:
```
services:
  ocr:
    image: ghcr.io/swarro/ocr-app:latest
    ports:
      - "8501:8501"
    volumes:
      - ocr_cache:/home/appuser/.EasyOCR:z     
    devices:
      - nvidia.com/gpu=all
    security_opt:
      - label=disable
    stdin_open: true
    tty: true

volumes:
  ocr_cache:
```


### 2. Start the Server:
```
podman-compose up -d
```
Visit http://localhost:8501 in your browser to access the drag-and-drop web UI.

---

## Nerd Stuff:

The complete app works on 3 layers:
1. Pre-processing Layer
2. OCR and Sandwich pdf creation layer
3. Compression layer

### 1. Preprocessing Layer
The core file preprocessing pipeline operates in three main stages:

1. Format Handling & Parsing: Supports multi-page PDFs alongside standard image formats (.jpg, .jpeg, .png, .tiff, .bmp, .webp).
2. Standardization & Orientation: Fixes camera/scanner orientation tags and scales images to a uniform resolution.
3. OpenCV Conversion: Outputs all processed pages as standardized BGR NumPy arrays.

### 2. OCR & .pdf creation
The module supports a dual-engine hybrid approach:
1. Primary Engine (EasyOCR): Used for deep-learning-based, high-accuracy text extractions.
2. Fallback Engine (Tesseract): Used as a secondary text extractor if EasyOCR encounters an error, as well as the generator for output searchable PDFs.

### 3. Compression Layer
This layer takes the pdf and uses `ghost script` library to compress the pdf to less than 20mb pdf.

### Integration layer (main.py)
Overview & WorkflowFile Scanning & User Selection:
1. Scans the target directory, presents matching document files, and prompts the user to select one.
2. Page Ingestion: Uses preprocess_file to standardize pages into 300 DPI BGR OpenCV matrices.
3. OCR & Text Extraction: Runs EasyOCR (with Marathi + English language models) across each page to output raw text, confidence scores, and bounding box positions.
4. Searchable PDF Assembly: Generates searchable PDF bytes for each page via easyocr_to_pdf_bytes and merges them into a multi-page PDF output using pypdf.PdfWriter.
