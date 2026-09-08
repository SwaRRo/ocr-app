# app/main.py
import os
import io
from pypdf import PdfReader, PdfWriter
from core.processor import preprocess_file
from core.ocr_engine import easyocr_to_pdf_bytes, extract_text_from_matrix

def select_file(files_list: list) -> str:
    if len(files_list) == 1:
        selected = files_list[0]
        print(f"[+] Only one file found: '{selected}'. Proceeding automatically.")
        return selected

    print("\n==============================")
    print("    Select a File to Process  ")
    print("==============================")
    for index, filename in enumerate(files_list):
        print(f" [{index + 1}] {filename}")
        
    choice = input(f"\nSelect a file number (1-{len(files_list)}) [Default is 1]: ").strip()
    
    try:
        choice_idx = int(choice) - 1
        if 0 <= choice_idx < len(files_list):
            selected = files_list[choice_idx]
            print(f"   -> Selected: {selected}")
            return selected
    except ValueError:
        pass
        
    print(f"   -> Invalid or empty selection. Defaulting to first file: '{files_list[0]}'")
    return files_list[0]

def render_confidence_bar(confidence: float, bar_length: int = 15) -> str:
    filled_blocks = int(round(bar_length * (confidence / 100.0)))
    empty_blocks = bar_length - filled_blocks
    bar = "█" * filled_blocks + "░" * empty_blocks
    return f"[{bar}] {confidence:.1f}%"

if __name__ == "__main__":
    data_dir = "data"
    output_dir = os.path.join(data_dir, "output")
    supported_extensions = [".pdf", ".jpg", ".jpeg", ".png", ".tiff", ".bmp", ".webp"]

    print("==========================================")
    print("        Document OCR Selector Tool        ")
    print("==========================================")
    
    if not os.path.exists(data_dir):
        print(f"[-] Error: The directory '{data_dir}' does not exist.")
    else:
        try:
            all_files = os.listdir(data_dir)
        except Exception as e:
            print(f"[-] Error reading directory: {e}")
            all_files = []

        files_to_process = []
        for filename in all_files:
            file_path = os.path.join(data_dir, filename)
            if os.path.isdir(file_path):
                continue
            ext = os.path.splitext(filename)[1].lower()
            if ext in supported_extensions:
                files_to_process.append(filename)

        if not files_to_process:
            print(f"[-] No supported files found in '{data_dir}' directory.")
        else:
            selected_filename = select_file(files_to_process)
            file_path = os.path.join(data_dir, selected_filename)
            base_name = os.path.splitext(selected_filename)[0]
            
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            ocr_lang = "eng+mar"
            
            print(f"\n[+] Ingesting: {file_path}")
            try:
                # 1. Preprocess (Returns standard yesterday BGR page matrices)
                processed_pages = preprocess_file(file_path)
                print(f"    -> Rendered {len(processed_pages)} page(s) at 300 DPI.")
                
                # Create the PDF writer to consolidate our final pages
                pdf_writer = PdfWriter()
                
                # 2. Process each page sequentially
                for index, page_matrix in enumerate(processed_pages):
                    print(f"\n    -> Running EasyOCR on Page {index + 1}/{len(processed_pages)} [Model: {ocr_lang}]...")
                    
                    # A. Run EasyOCR to get text, confidence, and coordinates
                    raw_text, confidence, ocr_results = extract_text_from_matrix(page_matrix, lang=ocr_lang)
                    
                    # Render the confidence progress bar
                    conf_bar = render_confidence_bar(confidence)
                    
                    print(f"\n--- EXTRACTED RAW TEXT (PAGE {index + 1}) ---")
                    print(f"OCR Confidence Accuracy: {conf_bar}")
                    print("-------------------------------------------")
                    print(raw_text)
                    print("-------------------------------------------\n")
                    
                    # B. Generate the searchable PDF bytes using EasyOCR results and ReportLab
                    page_pdf_bytes = easyocr_to_pdf_bytes(page_matrix, ocr_results, target_dpi=300)
                    
                    # C. Load the page bytes into pypdf
                    reader = PdfReader(io.BytesIO(page_pdf_bytes))
                    page = reader.pages[0]
                    
                    # D. Add the page directly to our output PDF
                    pdf_writer.add_page(page)
                
                # 3. Save the final multi-page Searchable PDF to disk
                pdf_output_path = os.path.join(output_dir, f"{base_name}_searchable.pdf")
                with open(pdf_output_path, "wb") as f:
                    pdf_writer.write(f)
                    
                print(f"    [Success] Saved Searchable Sandwich PDF to: {pdf_output_path}")
                print("==========================================")
                
            except Exception as e:
                print(f"[-] Failed to process '{selected_filename}': {e}")
