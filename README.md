# Multilingual OCR Document Engine

A GPU-accelerated, deep-learning OCR pipeline for processing complex legal documents, ancient scriptures (like Dasbodh), and standard PDFs. It features automatic EXIF alignment, 300 DPI upscaling, and native double-layer Searchable PDF generation.

## Features
* **Zero-Trust Architecture:** Runs rootless and processes data entirely in volatile memory (`/tmp`), leaving no traces on the host.
* **Dual-Engine:** Uses **EasyOCR (PyTorch)** for high-accuracy Devanagari/Marathi extraction, and **Tesseract** for searchable PDF formatting.

## How to Run the Public Container

You do not need to download the source code. You can run the pre-built, fully self-contained application using Podman or Docker.

### 1. Create a `compose.yaml` file:
```yaml
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

2. Start the Server:
code Bash

podman-compose up -d

Visit http://localhost:8501 in your browser to access the drag-and-drop web UI.
code Code

---

### Step 3: Push Your Code to GitHub (Private Repo)

1. Go to [GitHub.com](https://github.com) and log in.
2. Click the **`+`** icon in the top right and select **New repository**.
3. Name it `ocr-app`.
4. Select **Private** (This keeps your blueprints hidden).
5. Click **Create repository**. Don't close this page yet.

Now, open your Fedora terminal inside your `WORK/OCR` folder and run these commands one by one to pack and upload your code:

```bash
# 1. Initialize the directory as a Git repository
git init

# 2. Add all your files (the .gitignore will protect your private data folders)
git add .

# 3. Save a snapshot of your code
git commit -m "Initial MVP: Dual-Engine OCR with Flask UI"

# 4. Rename the default branch to 'main'
git branch -M main

# 5. Link it to your GitHub repo (Replace <YOUR-USERNAME> with your actual GitHub username)
git remote add origin https://github.com/<YOUR-USERNAME>/ocr-app.git

# 6. Push the code to GitHub!
git push -u origin main

(It will ask for your GitHub username and the same Personal Access Token you used earlier).
