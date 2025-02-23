import cv2
import numpy as np
import pytesseract

def extractFromImage(image_path, output_text_path=None):
    # load image
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"could not load image: {image_path}")
    
    # to hsv
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # define range
    lower_green = np.array([35, 80, 80])
    upper_green = np.array([85, 255, 255])
    
    # create mask
    mask = cv2.inRange(hsv, lower_green, upper_green)
    
    # morph cleanup
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    
    # mask image
    highlighted = 255 * np.ones_like(img)
    highlighted[mask != 0] = img[mask != 0]
    
    # to grayscale
    gray = cv2.cvtColor(highlighted, cv2.COLOR_BGR2GRAY)
    
    # perform ocr
    ocr_result = pytesseract.image_to_string(gray)
    
    # split lines
    text_lines = ocr_result.splitlines()
    
    # optional save
    if output_text_path:
        with open(output_text_path, 'w', encoding='utf-8') as f:
            f.write(ocr_result)
    
    # show windows
    cv2.imshow("mask", mask)
    cv2.imshow("highlight", highlighted)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    
    return text_lines