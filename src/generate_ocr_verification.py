import cv2
import os
import time
from datetime import datetime
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
VEHICLE_DIR = os.path.join(BASE_DIR, "data", "vehicles")
PLATE_DIR = os.path.join(BASE_DIR, "data", "plates")
CSV_PATH = os.path.join(BASE_DIR, "data", "plates.csv")
OUTPUT_PATH = os.path.join(BASE_DIR, "screenshots", "ocr_verification.png")


def create_verification_screenshot():
    vehicle_files = sorted([f for f in os.listdir(VEHICLE_DIR) if f.endswith(('.jpg', '.png'))])
    plate_files = sorted([f for f in os.listdir(PLATE_DIR) if f.endswith('.png')])
    
    if not vehicle_files or not plate_files:
        print("No captured images found. Please capture at least one vehicle first.")
        return
    
    latest_vehicle = os.path.join(VEHICLE_DIR, vehicle_files[-1])
    latest_plate = os.path.join(PLATE_DIR, plate_files[-1])
    
    vehicle_img = cv2.imread(latest_vehicle)
    plate_img = cv2.imread(latest_plate)
    
    plate_gray = cv2.cvtColor(plate_img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(plate_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    ocr_text = pytesseract.image_to_string(thresh, config='--psm 7 --oem 3').strip()
    
    canvas_width = 1400
    canvas_height = 900
    canvas = np.zeros((canvas_height, canvas_width, 3), dtype=np.uint8)
    canvas[:] = (40, 40, 40)
    
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cv2.putText(canvas, "ANPR OCR VERIFICATION SCREENSHOT", (50, 50), 
                cv2.FONT_HERSHEY_BOLD, 1.2, (0, 255, 255), 3)
    cv2.putText(canvas, f"Date/Time: {current_time}", (50, 90), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    y_offset = 140
    cv2.putText(canvas, "FILE PATHS:", (50, y_offset), 
                cv2.FONT_HERSHEY_BOLD, 0.8, (0, 255, 0), 2)
    y_offset += 35
    cv2.putText(canvas, f"Vehicle: {latest_vehicle}", (70, y_offset), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
    y_offset += 30
    cv2.putText(canvas, f"Plate: {latest_plate}", (70, y_offset), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
    y_offset += 30
    cv2.putText(canvas, f"CSV Log: {CSV_PATH}", (70, y_offset), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
    
    y_offset += 50
    cv2.putText(canvas, "OCR RESULT:", (50, y_offset), 
                cv2.FONT_HERSHEY_BOLD, 0.8, (0, 255, 0), 2)
    y_offset += 35
    cv2.putText(canvas, f"Extracted Text: {ocr_text if ocr_text else 'NO TEXT DETECTED'}", (70, y_offset), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
    
    vehicle_small = cv2.resize(vehicle_img, (400, 300))
    canvas[350:650, 50:450] = vehicle_small
    cv2.putText(canvas, "1. Original Vehicle Image", (50, 340), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
    
    plate_height = 150
    plate_width = int(plate_img.shape[1] * (plate_height / plate_img.shape[0]))
    plate_resized = cv2.resize(plate_img, (plate_width, plate_height))
    canvas[350:500, 500:500+plate_width] = plate_resized
    cv2.putText(canvas, "2. Extracted Plate (Color)", (500, 340), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
    
    thresh_bgr = cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)
    thresh_resized = cv2.resize(thresh_bgr, (plate_width, plate_height))
    canvas[520:670, 500:500+plate_width] = thresh_resized
    cv2.putText(canvas, "3. OCR Threshold (Binary)", (500, 510), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
    
    cv2.putText(canvas, "Tesseract OCR Engine: v5.x", (500, 700), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)
    cv2.putText(canvas, "Config: --psm 7 --oem 3", (500, 730), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)
    
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        last_entries = lines[-5:] if len(lines) > 5 else lines[1:]
    
    y_offset = 700
    cv2.putText(canvas, "RECENT CSV LOGS:", (50, y_offset), 
                cv2.FONT_HERSHEY_BOLD, 0.7, (0, 255, 0), 2)
    y_offset += 30
    for entry in last_entries:
        cv2.putText(canvas, entry.strip(), (70, y_offset), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (200, 200, 200), 1)
        y_offset += 25
    
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    cv2.imwrite(OUTPUT_PATH, canvas)
    
    print(f"\n{'='*60}")
    print("OCR VERIFICATION SCREENSHOT GENERATED")
    print(f"{'='*60}")
    print(f"Output: {OUTPUT_PATH}")
    print(f"Timestamp: {current_time}")
    print(f"OCR Result: {ocr_text if ocr_text else 'NO TEXT DETECTED'}")
    print(f"{'='*60}\n")
    
    cv2.imshow("OCR Verification Screenshot", canvas)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == "__main__":
    import numpy as np
    create_verification_screenshot()
