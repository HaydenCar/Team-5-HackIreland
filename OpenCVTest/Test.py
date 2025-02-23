import cv2
import numpy as np
import pytesseract

def extract_green_highlighted_text(image_path, output_text_path=None):
    """
    Loads an image, isolates green-highlighted areas, performs OCR on them,
    and returns the recognized text. Optionally saves the text to a file.
    """

    # 1. Load the image
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError(f"Could not load image: {image_path}")

    # 2. Convert to HSV color space
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # 3. Define the HSV range for green highlight (adjust as needed)
    lower_green = np.array([35, 80, 80])
    upper_green = np.array([85, 255, 255])

    # 4. Create a mask for the green highlight
    mask = cv2.inRange(hsv, lower_green, upper_green)

    # 5. (Optional) Morphological operations to clean up noise
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

    # 6. Create a masked image where only the green highlight remains (others white)
    highlighted = 255 * np.ones_like(img)  # white background
    highlighted[mask != 0] = img[mask != 0]

    # 7. Convert to grayscale for Tesseract
    gray = cv2.cvtColor(highlighted, cv2.COLOR_BGR2GRAY)

    # 8. OCR the resulting image
    ocr_result = pytesseract.image_to_string(gray)

    # 9. Print the recognized text (same as before)
    print("Recognized Text:\n", ocr_result)

    # 10. Optionally save the recognized text to a file
    if output_text_path:
        with open(output_text_path, 'w', encoding='utf-8') as f:
            f.write(ocr_result)
        print(f"\nText also saved to: {output_text_path}")

    # Show the masked image for debugging (optional)
    cv2.imshow("Green Highlight Mask", mask)
    cv2.imshow("Green Highlighted Areas", highlighted)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def main():
    # Replace these with your own file paths
    image_path = "image.png"
    output_text_file = "output.txt"

    extract_green_highlighted_text(image_path, output_text_file)

if __name__ == "__main__":
    main()
