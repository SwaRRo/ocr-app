# app/ui.py
import os
import io
import uuid
import tempfile
import threading
import queue
from flask import Flask, request, jsonify, render_template_string, send_file
from pypdf import PdfReader, PdfWriter
from core.processor import preprocess_file
from core.ocr_engine import extract_text_from_matrix, ocr_matrix_to_pdf_bytes, flush_ocr_memory
from core.pdf_handler import compress_pdf

app = Flask(__name__)

# Task queue and tracking dictionary
task_queue = queue.Queue()
TASKS = {}

def background_worker():
    while True:
        task = task_queue.get()
        if task is None:
            break
            
        task_id = task['task_id']
        temp_file_path = task['temp_file_path']
        base_name = task['base_name']

        try:
            TASKS[task_id]['status'] = "Preprocessing document (Scaling to 250 DPI)..."
            TASKS[task_id]['progress'] = 5
            processed_pages = preprocess_file(temp_file_path, target_dpi=250)
            
            pdf_writer = PdfWriter()
            ocr_lang = "eng+mar"
            full_text_list = []
            accumulated_confidence = []
            total_pages = len(processed_pages)
            
            for index, page_matrix in enumerate(processed_pages):
                TASKS[task_id]['status'] = f"Running AI OCR on Page {index + 1} of {total_pages}..."
                TASKS[task_id]['progress'] = int(5 + ((index / total_pages) * 80))
                
                raw_text, confidence = extract_text_from_matrix(page_matrix, lang=ocr_lang)
                full_text_list.append(raw_text)
                accumulated_confidence.append(confidence)
                
                page_pdf_bytes = ocr_matrix_to_pdf_bytes(page_matrix, lang=ocr_lang)
                reader = PdfReader(io.BytesIO(page_pdf_bytes))
                pdf_writer.add_page(reader.pages[0])
            
                flush_ocr_memory()
                
            TASKS[task_id]['status'] = "Merging PDF layers..."
            TASKS[task_id]['progress'] = 85
            
            output_dir = "/home/appuser/ocr_output"
            os.makedirs(output_dir, mode=0o700, exist_ok=True)
                
            heavy_filename = f"{base_name}_heavy.pdf"
            heavy_pdf_path = os.path.join(output_dir, heavy_filename)
            
            with open(heavy_pdf_path, "wb") as f:
                pdf_writer.write(f)
                
            TASKS[task_id]['status'] = "Compressing PDF with Ghostscript..."
            TASKS[task_id]['progress'] = 90
            
            compressed_filename = f"{base_name}_searchable.pdf"
            compressed_pdf_path = os.path.join(output_dir, compressed_filename)
            
            compress_pdf(input_path=heavy_pdf_path, output_path=compressed_pdf_path, quality="ebook")
                
            combined_text = "\n\n--- PAGE BREAK ---\n\n".join(full_text_list)
            average_confidence = sum(accumulated_confidence) / len(accumulated_confidence) if accumulated_confidence else 0.0
            
            TASKS[task_id]['status'] = 'Complete'
            TASKS[task_id]['progress'] = 100
            TASKS[task_id]['result_text'] = combined_text
            TASKS[task_id]['confidence'] = average_confidence
            TASKS[task_id]['output_filename'] = compressed_filename
            
        except Exception as e:
            TASKS[task_id]['status'] = f"Error: {str(e)}"
            TASKS[task_id]['progress'] = 0
        finally:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
            flush_ocr_memory()
            task_queue.task_done()

# Start background worker thread
threading.Thread(target=background_worker, daemon=True).start()

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Enterprise Document OCR</title>
    <style>
        body { font-family: sans-serif; max-width: 800px; margin: 40px auto; padding: 0 20px; background-color: #f9f9f9; color: #333; }
        .card { background: white; padding: 25px; border-radius: 6px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px; }
        button, .btn { background: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; font-size: 16px; text-decoration: none; display: inline-block; }
        button:hover, .btn:hover { background: #0056b3; }
        .btn-secondary { background: #6c757d; }
        .btn-secondary:hover { background: #5a6268; }
        .btn-success { background: #28a745; }
        .btn-success:hover { background: #218838; }
        textarea { width: 100%; height: 250px; font-family: monospace; padding: 10px; border-radius: 4px; border: 1px solid #ccc; box-sizing: border-box; }
        .progress-container { margin: 15px 0; background: #eee; border-radius: 4px; height: 20px; overflow: hidden; }
        .progress-bar { background: #28a745; height: 100%; width: 0%; color: white; text-align: center; font-size: 14px; line-height: 20px; font-weight: bold; transition: width 0.3s ease; }
        .spinner { border: 4px solid #f3f3f3; border-top: 4px solid #007bff; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin: 20px auto; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body>
    <h1>Document OCR Pipeline</h1>
    
    <div class="card" id="upload-card">
        <form id="upload-form">
            <label style="font-weight: bold; display: block; margin-bottom: 10px;">Upload scanned image or PDF:</label>
            <input type="file" id="file-input" required style="margin-bottom: 15px; display: block;">
            <button type="submit" id="submit-btn">Process Document</button>
        </form>
    </div>

    <div class="card" id="loading-card" style="display: none; text-align: center;">
        <div class="spinner"></div>
        <p id="status-text" style="font-weight: bold; color: #007bff;">Uploading...</p>
        <div class="progress-container">
            <div id="progress-bar" class="progress-bar">0%</div>
        </div>
    </div>

    <div class="card" id="results-card" style="display: none;">
        <h3 style="color: #28a745;">Processing Complete!</h3>
        <p><strong>OCR Confidence:</strong> <span id="conf-text"></span></p>
        <textarea id="result-text" readonly></textarea>
        <div style="margin-top: 20px;">
            <a id="download-link" href="#" class="btn btn-success">Download Searchable PDF</a>
            <button type="button" class="btn btn-secondary" onclick="resetUI()">Process Another Document</button>
        </div>
    </div>

    <script>
        document.getElementById('upload-form').onsubmit = async function(e) {
            e.preventDefault();
            let fileInput = document.getElementById('file-input');
            if (fileInput.files.length === 0) return;

            let formData = new FormData();
            formData.append('file', fileInput.files[0]);

            document.getElementById('upload-card').style.display = 'none';
            document.getElementById('loading-card').style.display = 'block';

            let response = await fetch('/process', {method: 'POST', body: formData});
            let data = await response.json();
            
            if(data.task_id) {
                pollStatus(data.task_id);
            } else {
                alert("Upload failed.");
                resetUI();
            }
        };

        function pollStatus(taskId) {
            let interval = setInterval(async () => {
                let res = await fetch('/status/' + taskId);
                let task = await res.json();
                
                document.getElementById('status-text').innerText = task.status;
                document.getElementById('progress-bar').style.width = task.progress + '%';
                document.getElementById('progress-bar').innerText = task.progress + '%';

                if (task.status === 'Complete') {
                    clearInterval(interval);
                    document.getElementById('loading-card').style.display = 'none';
                    document.getElementById('results-card').style.display = 'block';
                    document.getElementById('result-text').value = task.result_text;
                    document.getElementById('conf-text').innerText = task.confidence.toFixed(1) + '%';
                    document.getElementById('download-link').href = '/download/' + task.output_filename;
                } else if (task.status.startsWith('Error')) {
                    clearInterval(interval);
                    document.getElementById('loading-card').style.display = 'none';
                    document.getElementById('upload-card').style.display = 'block';
                    alert(task.status);
                }
            }, 1500);
        }

        function resetUI() {
            document.getElementById('results-card').style.display = 'none';
            document.getElementById('file-input').value = '';
            document.getElementById('result-text').value = '';
            document.getElementById('progress-bar').style.width = '0%';
            document.getElementById('progress-bar').innerText = '0%';
            document.getElementById('status-text').innerText = 'Uploading...';
            document.getElementById('upload-card').style.display = 'block';
        }
    </script>
</body>
</html>
"""

@app.route("/", methods=["GET"])
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route("/process", methods=["POST"])
def process():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
        
    uploaded_file = request.files["file"]
    if uploaded_file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    file_extension = os.path.splitext(uploaded_file.filename)[1].lower()
    base_name = os.path.splitext(uploaded_file.filename)[0]

    with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
        uploaded_file.save(temp_file.name)
        temp_file_path = temp_file.name

    task_id = uuid.uuid4().hex
    TASKS[task_id] = {
        "status": "Queued...",
        "progress": 0
    }
    
    task_queue.put({
        "task_id": task_id,
        "temp_file_path": temp_file_path,
        "base_name": base_name
    })

    return jsonify({"task_id": task_id})

@app.route("/status/<task_id>", methods=["GET"])
def status(task_id):
    task = TASKS.get(task_id, {"status": "Not found", "progress": 0})
    return jsonify(task)

@app.route("/download/<filename>", methods=["GET"])
def download(filename):
    pdf_path = os.path.join("/home/appuser/ocr_output", filename)
    if os.path.exists(pdf_path):
        return send_file(pdf_path, as_attachment=True)
    return "File not found", 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8501)
