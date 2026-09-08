# app/core/pdf_handler.py
import os
import subprocess

def compress_pdf(input_path: str, output_path: str, quality: str = "ebook") -> str:
    """
    Compresses a PDF file using Ghostscript to keep file sizes under 20MB.
    Preserves the invisible searchable text layer while optimizing the background images.
    
    Quality options:
    - /screen : Lowest resolution, smallest size (72 dpi)
    - /ebook  : Medium resolution, great for reading (150 dpi) - Recommended
    - /printer: High resolution, larger size (300 dpi)
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input PDF not found: {input_path}")

    # Ghostscript command line arguments
    gs_command = [
        "gs",
        "-sDEVICE=pdfwrite",
        "-dCompatibilityLevel=1.4",
        f"-dPDFSETTINGS=/{quality}",
        "-dNOPAUSE",
        "-dQUIET",
        "-dBATCH",
        f"-sOutputFile={output_path}",
        input_path
    ]

    try:
        print(f"   [debug] Compressing PDF using Ghostscript (Quality: {quality})...")
        subprocess.run(gs_command, check=True)
        
        # Check if the output was successfully created
        if os.path.exists(output_path):
            # Calculate file sizes for logging
            original_size = os.path.getsize(input_path) / (1024 * 1024)
            new_size = os.path.getsize(output_path) / (1024 * 1024)
            print(f"   [debug] Compression successful: {original_size:.2f}MB -> {new_size:.2f}MB")
            
            # Delete the heavy original file to save storage space
            os.remove(input_path)
            
            return output_path
        else:
            return input_path
            
    except subprocess.CalledProcessError as e:
        print(f"   [warning] Ghostscript compression failed: {e}. Returning uncompressed PDF.")
        return input_path
