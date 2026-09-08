# app/ui.py
import os
import io
import tempfile
from flask import Flask, request, render_template_string, send_file
from pypdf import PdfReader, PdfWriter
from core.processor import preprocess_file
from core.ocr_engine import extract_text_from_matrix, ocr_matrix_to_pdf_bytes, flush_ocr_memory

app = Flask(__name__)

# A clean, lightweight, raw CSS/HTML template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Lightweight Document OCR</title>
    <style>
        body { font-family: sans-serif; max-width: 800px; margin: 40px auto; padding: 0 20px; line-height: 1.6; background-color: #f9f9f9; color: #333; }
        h1 { color: #111; border-bottom: 2px solid #ddd; padding-bottom: 10px; }
        .card { background: white; padding: 25px; border-radius: 6px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }
        input[type="file"] { display: block; margin-bottom: 15px; }
        button { background: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; font-size: 16px; }
        button:hover { background: #0056b3; }
        textarea { width: 100%; height: 250px; font-family: monospace; padding: 10px; border-radius: 4px; border: 1px solid #ccc; box-sizing: border-box; }
        .progress-container { margin: 15px 0; background: #eee; border-radius: 4px; height: 20px; overflow: hidden; }
        .progress-bar { background: #28a745; height: 100%; color: white; text-align: center; font-size: 14px; line-height: 20px; font-weight: bold; }
        .success { color: #28a745; font-weight: bold; margin-bottom: 15px; }
        .spinner { border: 4px solid #f3f3f3; border-top: 4px solid #007bff; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 20px auto; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <h1>📄 Lightweight Document OCR</h1>
    
    <div class="card" id="upload-card">
        <form action="/process" method="post" enctype="multipart/form-data">
            <label style="font-weight: bold; display: block; margin-bottom: 10px;">Upload scanned image or PDF:</label>
            <input type="file" name="file" required>
            <button type="submit" id="submit-btn">Process Document</button>
        </form>
    </div>

    <div class="card" id="loading-card" style="display: none; text-align: center;">
        <div class="spinner"></div>
        <p style="font-weight: bold; color: #007bff; margin-bottom: 5px;">Loading AI & Processing Document...</p>
        <p style="font-size: 14px; color: #666; margin-top: 0;">Please do not refresh or close this page.</p>
    </div>

    {% if processed %}
    <div class="card" id="results-card">
        <div class="success">🎉 Processing complete! RAM has been freed.</div>
        
        <p><strong>OCR Confidence Accuracy:</strong></p>
        <div class="progress-container">
            <div class="progress-bar" style="width: {{ confidence }}%;">{{ "%.1f"|format(confidence) }}%</div>
        </div>

        <p><strong>Extracted Marathi/English Text:</strong></p>
        <textarea readonly>{{ text }}</textarea>

        <div style="margin-top: 20px;">
            <a href="/download/{{ output_filename }}" style="display: inline-block; background: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; font-size: 16px; font-weight: bold;">⬇️ Download Searchable PDF</a>
        </div>
    </div>
    {% endif %}

    <script>
        document.querySelector('form').addEventListener('submit', function() {
            document.getElementById('upload-card').style.display = 'none';
            var resultsCard = document.getElementById('results-card');
            if (resultsCard) resultsCard.style.display = 'none';
            document.getElementById('loading-card').style.display = 'block';
        });
    </script>
</body>
</html>
"""

@app.route("/", methods=["GET"])
def home():
    return render_template_string(HTML_TEMPLATE, processed=False)

@app.route("/process", methods=["POST"])
def process():
    if "file" not in request.files:
        return "No file uploaded", 400
        
    uploaded_file = request.files["file"]
    if uploaded_file.filename == "":
        return "No file selected", 400

    file_extension = os.path.splitext(uploaded_file.filename)[1].lower()
    base_name = os.path.splitext(uploaded_file.filename)[0]

    with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
        uploaded_file.save(temp_file.name)
        temp_file_path = temp_file.name

    try:
        processed_pages = preprocess_file(temp_file_path, target_dpi=300)
        pdf_writer = PdfWriter()
        ocr_lang = "eng+mar"
        
        full_text_list = []
        accumulated_confidence = []
        
        for index, page_matrix in enumerate(processed_pages):
            raw_text, confidence = extract_text_from_matrix(page_matrix, lang=ocr_lang)
            full_text_list.append(raw_text)
            accumulated_confidence.append(confidence)
            
            page_pdf_bytes = ocr_matrix_to_pdf_bytes(page_matrix, lang=ocr_lang)
            reader = PdfReader(io.BytesIO(page_pdf_bytes))
            page = reader.pages[0]
            pdf_writer.add_page(page)
        
        output_dir = "/home/appuser/ocr_output"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, mode=0o700, exist_ok=True)
            
        output_filename = f"{base_name}_searchable.pdf"
        pdf_output_path = os.path.join(output_dir, output_filename)
        
        with open(pdf_output_path, "wb") as f:
            pdf_writer.write(f)
            
        combined_text = "\n\n--- PAGE BREAK ---\n\n".join(full_text_list)
        average_confidence = sum(accumulated_confidence) / len(accumulated_confidence) if accumulated_confidence else 0.0
        
        return render_template_string(
            HTML_TEMPLATE,
            processed=True,
            text=combined_text,
            confidence=average_confidence,
            output_filename=output_filename
        )
        
    except Exception as e:
        return f"Error during processing: {e}", 500
        
    finally:
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
            
        # VERY IMPORTANT: Flush the AI from RAM/VRAM the exact second processing finishes!
        flush_ocr_memory()

@app.route("/download/<filename>", methods=["GET"])
def download(filename):
    pdf_path = os.path.join("/home/appuser/ocr_output", filename)
    if os.path.exists(pdf_path):
        return send_file(pdf_path, as_attachment=True)
    return "File not found", 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8501)
