import csv
import os
import re
import time

import cv2
import numpy as np
import pytesseract

# Windows only — update path if your install location differs
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

MIN_AREA = 600
AR_MIN, AR_MAX = 2.0, 8.0
W_OUT, H_OUT = 450, 140
DEFAULT_PLATE_REGEX = r"[A-Z]{3}[0-9]{3}[A-Z]"
PLATE_RE = re.compile(os.getenv("ANPR_PLATE_REGEX", DEFAULT_PLATE_REGEX))
COOLDOWN_SECONDS = 8

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CSV_PATH = os.path.join(BASE_DIR, "data", "plates.csv")
VEHICLE_IMAGE_DIR = os.path.join(BASE_DIR, "data", "vehicles")
PLATE_IMAGE_DIR = os.path.join(BASE_DIR, "data", "plates")
SCREENSHOTS_DIR = os.path.join(BASE_DIR, "screenshots")

DETECTION_SCREENSHOT_PATH = os.path.join(SCREENSHOTS_DIR, "detection.png")
ALIGNMENT_SCREENSHOT_PATH = os.path.join(SCREENSHOTS_DIR, "alignment.png")
OCR_SCREENSHOT_PATH = os.path.join(SCREENSHOTS_DIR, "ocr.png")


def correct_camera_orientation(frame):
    return frame


def ensure_csv_file(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.exists(path):
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["plate", "timestamp"])


def ensure_output_dirs():
    os.makedirs(VEHICLE_IMAGE_DIR, exist_ok=True)
    os.makedirs(PLATE_IMAGE_DIR, exist_ok=True)
    os.makedirs(SCREENSHOTS_DIR, exist_ok=True)


def find_plate_candidates(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blur, 100, 200)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    candidates = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < MIN_AREA:
            continue

        rect = cv2.minAreaRect(cnt)
        (_, _), (w, h), _ = rect
        if w <= 0 or h <= 0:
            continue

        ar = max(w, h) / max(1.0, min(w, h))
        if AR_MIN <= ar <= AR_MAX:
            candidates.append(rect)

    return candidates


def order_points(pts):
    pts = np.array(pts, dtype=np.float32)
    s = pts.sum(axis=1)
    diff = np.diff(pts, axis=1)

    top_left = pts[np.argmin(s)]
    bottom_right = pts[np.argmax(s)]
    top_right = pts[np.argmin(diff)]
    bottom_left = pts[np.argmax(diff)]

    return np.array([top_left, top_right, bottom_right, bottom_left], dtype=np.float32)


def warp_plate(frame, rect):
    box = cv2.boxPoints(rect)
    src = order_points(box)
    dst = np.array(
        [
            [0, 0],
            [W_OUT - 1, 0],
            [W_OUT - 1, H_OUT - 1],
            [0, H_OUT - 1],
        ],
        dtype=np.float32,
    )
    matrix = cv2.getPerspectiveTransform(src, dst)
    return cv2.warpPerspective(frame, matrix, (W_OUT, H_OUT))


def read_plate_text(plate_img):
    gray = cv2.cvtColor(plate_img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    text = pytesseract.image_to_string(
        thresh,
        config="--psm 8 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
    )
    text = text.upper().replace(" ", "").replace("-", "")
    return text, thresh


def extract_valid_plate(text):
    match = PLATE_RE.search(text)
    if not match:
        return None
    return match.group(0)


def append_plate_log(path, plate):
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([plate, time.strftime("%Y-%m-%d %H:%M:%S")])


def save_required_screenshots(frame, rect, aligned_plate, thresh):
    detection_vis = frame.copy()
    box = cv2.boxPoints(rect).astype(int)
    cv2.polylines(detection_vis, [box], True, (0, 255, 0), 2)

    cv2.imwrite(DETECTION_SCREENSHOT_PATH, detection_vis)
    cv2.imwrite(ALIGNMENT_SCREENSHOT_PATH, aligned_plate)
    cv2.imwrite(OCR_SCREENSHOT_PATH, thresh)


def process_saved_vehicle_image(image_path):
    frame = cv2.imread(image_path)
    if frame is None:
        return None, None, None, None, None

    candidates = find_plate_candidates(frame)
    if not candidates:
        return None, None, None, None, None

    rect = max(candidates, key=lambda r: r[1][0] * r[1][1])
    aligned_plate = warp_plate(frame, rect)
    raw_text, thresh = read_plate_text(aligned_plate)
    valid_plate = extract_valid_plate(raw_text)

    save_required_screenshots(frame, rect, aligned_plate, thresh)

    timestamp_tag = time.strftime("%Y%m%d_%H%M%S")
    if valid_plate:
        plate_filename = f"plate_{valid_plate}_{timestamp_tag}.png"
    else:
        plate_filename = f"plate_UNKNOWN_{timestamp_tag}.png"
    plate_path = os.path.join(PLATE_IMAGE_DIR, plate_filename)
    cv2.imwrite(plate_path, aligned_plate)

    return valid_plate, raw_text, plate_path, aligned_plate, thresh


def main():
    ensure_csv_file(CSV_PATH)
    ensure_output_dirs()

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        raise RuntimeError("Camera not opened")

    last_saved_plate = None
    last_saved_time = 0.0

    aligned_plate = None
    thresh = None
    message = "Press c to capture vehicle image"
    message_color = (0, 200, 255)

    while True:
        ok, frame = cap.read()
        if not ok:
            break

        frame = correct_camera_orientation(frame)
        vis = frame.copy()
        cv2.putText(vis, message, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.75, message_color, 2)
        cv2.putText(
            vis,
            "Press c: capture vehicle image | Press q: quit",
            (20, 72),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2,
        )
        cv2.putText(
            vis,
            "Flow after capture: Detection -> Alignment -> OCR -> Regex -> CSV",
            (20, 100),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (255, 255, 255),
            2,
        )

        cv2.imshow("ANPR Full Pipeline", vis)
        if aligned_plate is not None:
            cv2.imshow("Aligned Plate", aligned_plate)
        if thresh is not None:
            cv2.imshow("OCR Threshold", thresh)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("c"):
            timestamp_tag = time.strftime("%Y%m%d_%H%M%S")
            vehicle_filename = f"vehicle_{timestamp_tag}.jpg"
            vehicle_path = os.path.join(VEHICLE_IMAGE_DIR, vehicle_filename)
            cv2.imwrite(vehicle_path, frame)

            valid_plate, raw_text, plate_path, aligned_plate, thresh = process_saved_vehicle_image(vehicle_path)
            if plate_path is None:
                append_plate_log(CSV_PATH, "UNKNOWN")
                message = f"Vehicle saved: {vehicle_filename} | Plate not detected"
                message_color = (0, 165, 255)
            elif valid_plate:
                now = time.time()
                if valid_plate != last_saved_plate or (now - last_saved_time) > COOLDOWN_SECONDS:
                    append_plate_log(CSV_PATH, valid_plate)
                    last_saved_plate = valid_plate
                    last_saved_time = now
                message = f"Saved vehicle + plate image | VALID: {valid_plate}"
                message_color = (0, 255, 0)
            elif raw_text:
                append_plate_log(CSV_PATH, raw_text)
                message = f"Saved vehicle + plate image | OCR: {raw_text}"
                message_color = (0, 165, 255)
            else:
                append_plate_log(CSV_PATH, "UNKNOWN")
                message = f"Vehicle saved: {vehicle_filename} | No OCR text"
                message_color = (0, 165, 255)

        if key == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
