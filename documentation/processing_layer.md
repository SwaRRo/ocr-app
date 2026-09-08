# Processing Layer
---
This layer is purely for processing the *file* and rescaling the given file to 300 DPI for proper OCR processing.

For processing, we need to convert whatever format of image to a specific 'format type' that can be processed further and given to next layer (OCR).

1. Converting 'raw_file' to a single specific format() : #goes into numpy array
2. Rescaling the image to 300 DPI. # opencv
3. Fixing the layout from tilt, skew and others. #opencv

From here on out, we parse the numpy array to the next layer (OCR_layer)
