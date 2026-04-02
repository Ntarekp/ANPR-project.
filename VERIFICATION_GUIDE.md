# OCR Verification Screenshot Guide

## Purpose
Generate a comprehensive screenshot showing the complete OCR pipeline with verifiable metadata including file paths, timestamps, and OCR results.

## Steps to Generate Verification Screenshot

### Step 1: Capture a Vehicle Image
1. Run the main ANPR application:
   ```bash
   python src/main.py
   ```

2. Point your camera at a number plate

3. When the green "Plate Extraction" card appears showing detected text, press **'c'** to capture

4. You should see three windows:
   - **ANPR Full Pipeline**: Live camera feed with detection card
   - **Aligned Plate**: Extracted and warped plate image
   - **OCR Threshold**: Binary threshold image used for OCR

5. Press **'q'** to quit

### Step 2: Generate Verification Screenshot
Run the verification script:
```bash
python src/generate_ocr_verification.py
```

This will create `screenshots/ocr_verification.png` containing:
- **Current date/time** (system timestamp)
- **File paths** to:
  - Latest vehicle image in `data/vehicles/`
  - Latest plate image in `data/plates/`
  - CSV log file at `data/plates.csv`
- **OCR Result**: Extracted text from Tesseract
- **Visual proof**:
  1. Original vehicle image
  2. Extracted plate (color)
  3. OCR threshold (binary image)
- **Tesseract configuration** details
- **Recent CSV log entries** showing logged plates

### Step 3: Take Your Screenshot
1. The verification image will display automatically
2. Use Windows Snipping Tool or Print Screen to capture:
   - The entire verification window
   - Include Windows taskbar showing system date/time
   - Include file explorer showing the data folders (optional but helpful)

## What the Screenshot Proves

✅ **OCR is working**: Shows the binary threshold image and extracted text  
✅ **File persistence**: Shows actual file paths where images are saved  
✅ **Timestamp verification**: Shows system date matching CSV entries  
✅ **Complete pipeline**: Shows detection → alignment → OCR → validation → logging  
✅ **CSV logging**: Shows recent entries from plates.csv  

## Alternative: Manual Screenshot During Live Capture

If you prefer to show the live OCR process:

1. Run `python src/main.py`
2. Point camera at a number plate
3. Wait for the detection card to show OCR results
4. Arrange windows to show:
   - Main camera feed with detection card
   - Aligned Plate window
   - OCR Threshold window
   - File explorer showing `data/vehicles/` and `data/plates/` folders
   - CSV file open in editor
5. Take screenshot showing all windows + system date/time

## Files to Include in Documentation

- `screenshots/ocr_verification.png` - Generated verification screenshot
- `data/plates.csv` - CSV log showing captured plates with timestamps
- Screenshots of the three live windows during detection
