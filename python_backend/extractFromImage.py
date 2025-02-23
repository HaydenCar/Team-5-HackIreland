import cv2
import numpy as np
import pytesseract
import base64
import io

def extractFromImage(image_base64, output_text_path=None):

    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


    # Decode base64 to image bytes
    image_bytes = base64.b64decode(image_base64)
    image_stream = io.BytesIO(image_bytes)
    img = cv2.imdecode(np.frombuffer(image_stream.read(), np.uint8), cv2.IMREAD_COLOR)
    
    if img is None:
        raise ValueError("Could not decode image from base64 string.")
    
    # Convert to HSV color space
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # Define the HSV range for green highlight
    lower_green = np.array([35, 80, 80])
    upper_green = np.array([85, 255, 255])
    
    # Create a mask for the green highlight
    mask = cv2.inRange(hsv, lower_green, upper_green)
    
    # Optional morphological operations to clean up noise
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    
    # Create a masked image where only the green highlight remains
    highlighted = 255 * np.ones_like(img)
    highlighted[mask != 0] = img[mask != 0]
    
    # Convert to grayscale for OCR
    gray = cv2.cvtColor(highlighted, cv2.COLOR_BGR2GRAY)
    
    # Perform OCR
    ocr_result = pytesseract.image_to_string(gray)
    
    # Split lines
    text_lines = ocr_result.splitlines()
    
    # Optionally save the recognized text to a file
    if output_text_path:
        with open(output_text_path, 'w', encoding='utf-8') as f:
            f.write(ocr_result)
    
    # Show the masked image for debugging (optional)

    cv2.destroyAllWindows()
    
    return text_lines
