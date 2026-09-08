# OCR Layer
---

This layer converts the provided numpy array to OCR.

Uses : tesseract & EasyOCR library

Note: There are not major things happening here. To increase accuracy of OCR check one of the two things:
1. The library used in this layer
2. Improving pre-processing layers output accuracy

The output from here will be parsed as pdf(which has to be sandwiched with OCR text underneath the image) to the container rootless user folder output_dir = "/home/appuser/ocr_output".
While, there is still no accuracy or confidence report it has to be integrated either, after processing layer or at OCR layer.

