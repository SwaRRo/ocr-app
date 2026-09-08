# Mail Logic
Upload: Accept a scanned PDF or images of pages.

Process: Run the pre-processing, layout analysis, and OCR steps.

Rearrange: Let the user interact with the list of pages (e.g., changing page 3 to page 2, deleting blank pages, or adding a missing scan).

Finalize: Merge the rearranged pages, compress the final document, package it (as a PDF or a ZIP of extracted text/images), and provide a download link.

---

# Directory tree

OCR/
│
├── app/
│   ├── __init__.py
│   ├── main.py            # The main Streamlit UI and user interaction logic
│   ├── core/
│   │   ├── preprocessor.py # Image scaling, DPI adjustments, OpenCV thresholding
│   │   ├── ocr_engine.py   # Tesseract/EasyOCR integration and text extraction
│   │   └── pdf_handler.py  # Page merging, sorting, and final PDF compression
│   └── utils.py           # General helpers (zipping files, handling temp directories)
│
├── config/                # App settings, default DPIs, allowed file types
├── requirements.txt       # Python dependencies list
└── data/                  # Local folder for temporary uploads and processed files
