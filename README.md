# Vision-Based Desktop Automation

Automatically detects and launches Notepad from the desktop, then creates text files from API data using vision-based icon grounding.

## What It Does

1. **Detects Notepad Icon** - Uses multi-method visual grounding (OCR, Template Matching)
2. **Launches Notepad** - Double-clicks the detected icon to open
3. **Fetches Data** - Retrieves 10 posts from [JSONPlaceholder API](https://jsonplaceholder.typicode.com/posts)
4. **Saves Files** - Writes each post to `post_{id}.txt` on Desktop
5. **Creates Screenshots** - Saves annotated screenshots showing detection method + location

## Flow

```
Fetch 10 posts → Set black wallpaper → For each post:
  • Detect Notepad icon
  • Launch (3 retry attempts)
  • Type post content
  • Save file
  • Capture annotated screenshot
  • Close Notepad
→ Restore original wallpaper
```

## Libraries

| Library | Purpose |
|---------|---------|
| `pyautogui` | Mouse/keyboard automation |
| `cv2` | Image processing & template matching |
| `pytesseract` | OCR text recognition |
| `psutil` | Process detection |
| `requests` | API calls |
| `numpy`, `Pillow` | Image handling |

## Setup

### 1. Install Tesseract OCR

```
Download: https://github.com/UB-Mannheim/tesseract/wiki
Run installer (default: C:\Program Files\Tesseract-OCR\)
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure (if needed)

Edit `main.py` if Tesseract path differs:

```python
pytesseract.pytesseract.tesseract_cmd = r"C:\Path\To\tesseract.exe"
```

## Run

```bash
# Place Notepad shortcut on desktop
python main.py
```

## Output

**Files:** `Desktop/tjm-project/post_*.txt`  
**Screenshots:** `annotated_screenshots/MM-DD-YYYY/post*.png`

- Shows detection method, location, and coordinates

## Features

✓ Multi-method detection (OCR + Template Matching)  
✓ 3-attempt retry with 1s delays  
✓ Process validation (confirms Notepad opened)  
✓ Annotated screenshots for each run  
✓ Wallpaper backup/restore  
✓ Graceful API failure handling  

## Performance

- Detection: 1-2 seconds
- Per post: 5-8 seconds  
- 10 posts: ~50-80 seconds

See `CODE_EXPLANATION.md` for detailed code walkthrough.
