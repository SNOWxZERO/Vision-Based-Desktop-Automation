import pyautogui
import cv2
import numpy as np
import time
import requests
import os
import pytesseract
import ctypes
import winreg
import psutil
import pyperclip
from datetime import datetime

# ================= CONFIG =================
TEMPLATE_PATH = "Templates/Notepads.png"
SAVE_DIR = os.path.join(os.path.expanduser("~"), "Desktop", "tjm-project")
SCREENWIDTH, SCREENHEIGHT = pyautogui.size()
TEMP_BLACK_IMAGE = os.path.join(os.getcwd(), "temp_black_bg.png")

# If Tesseract is not in your PATH, set the line below:
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# Clear old saves
if os.path.exists(SAVE_DIR):
    os.system(f'rmdir /S /Q "{SAVE_DIR}"')
os.makedirs(SAVE_DIR)

# Screenshot directory with date
SCREENSHOT_BASE = os.path.join(os.getcwd(), "annotated_screenshots")
CURRENT_DATE = datetime.now().strftime("%m-%d-%Y %H-%M-%S")
SCREENSHOT_DIR = os.path.join(SCREENSHOT_BASE, CURRENT_DATE)
os.makedirs(SCREENSHOT_DIR, exist_ok=True)


# ================= WALLPAPER UTILS =================
def get_current_wallpaper():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop")
        wallpaper_path, _ = winreg.QueryValueEx(key, "Wallpaper")
        return wallpaper_path
    except Exception as e:
        print(f"  [ERROR] Could not backup wallpaper: {e}")
        return None


def set_wallpaper(path):
    ctypes.windll.user32.SystemParametersInfoW(20, 0, path, 3)


def create_black_bg():
    black_img = np.zeros((10, 10, 3), dtype=np.uint8)
    cv2.imwrite(TEMP_BLACK_IMAGE, black_img)


# ================= UTILS =================
def show_desktop():
    pyautogui.hotkey("alt", "tab")
    time.sleep(0.3)
    pyautogui.hotkey("win", "d")
    time.sleep(0.3)


def clear_selection():
    pyautogui.click(SCREENWIDTH / 2, SCREENHEIGHT / 2)
    time.sleep(0.2)


def take_screenshot():
    screenshot = pyautogui.screenshot()
    return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)


def save_annotated_screenshot(screenshot, coords, detection_method, post_idx):
    """Save annotated screenshot with detection info"""
    try:
        annotated = screenshot.copy()

        # Check if coords is valid (not None and contains actual values)
        has_valid_coords = (
            coords is not None and coords[0] is not None and coords[1] is not None
        )

        if has_valid_coords:
            x, y = int(coords[0]), int(coords[1])
            # Draw circles around detected position
            cv2.circle(annotated, (x, y), 40, (0, 255, 0), 3)
            cv2.circle(annotated, (x, y), 60, (0, 255, 0), 2)

            # Draw crosshairs
            cv2.line(annotated, (x - 20, y), (x + 20, y), (0, 255, 0), 2)
            cv2.line(annotated, (x, y - 20), (x, y + 20), (0, 255, 0), 2)

            # Add detection info text
            text = f"Method: {detection_method}"
            cv2.putText(
                annotated, text, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2
            )

            coords_text = f"Detected at ({x}, {y})"
            cv2.putText(
                annotated,
                coords_text,
                (50, 100),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2,
            )
        else:
            cv2.putText(
                annotated,
                "Icon NOT detected",
                (SCREENWIDTH // 2 - 200, SCREENHEIGHT // 2),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.5,
                (0, 0, 255),
                3,
            )

        # Save the annotated screenshot
        filename = f"post{post_idx}.png"
        filepath = os.path.join(SCREENSHOT_DIR, filename)

        # Use numpy to handle unicode path encoding
        success = cv2.imwrite(filepath, annotated)

        if success:
            print(f"  [DEBUG] Screenshot saved: {filepath}")
        else:
            # Fallback: Try with numpy memmap or direct write
            print("  [WARNING] cv2.imwrite failed, attempting alternative save...")

            _, buffer = cv2.imencode(".png", annotated)
            with open(filepath, "wb") as f:
                f.write(buffer)
            print(f"  [DEBUG] Screenshot saved (alternative method): {filepath}")
    except Exception as e:
        print(f"  [WARNING] Failed to save annotated screenshot: {e}")


# ================= DETECTION =================
def find_icon(template_path, threshold=0.65):
    """
    Multi-method icon detection using template matching, OCR, and edge detection.
    Returns tuple of (coordinates, detection_method) if found, (None, None) otherwise.
    """
    screenshot = take_screenshot()
    scale_factor = 1.0
    scr_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)

    # Method 1: OCR Detection (most reliable for text)
    print("  [DEBUG] Running OCR detection...")
    try:
        d = pytesseract.image_to_data(scr_gray, output_type=pytesseract.Output.DICT)
        for i, text in enumerate(d["text"]):
            if "notepad" in text.strip().lower():
                tx, ty, tw, th = (
                    d["left"][i],
                    d["top"][i],
                    d["width"][i],
                    d["height"][i],
                )
                cx = (tx + tw // 2) / scale_factor
                cy = (ty - th) / scale_factor
                print(f"  [DEBUG] OCR found Notepad at ({cx}, {cy})")
                return (cx, cy), screenshot, "OCR Detection"
    except Exception as e:
        print(f"  [DEBUG] OCR detection failed: {e}")

    # Method 2: Template Matching with multi-scale support
    print("  [DEBUG] Running template matching...")
    template = cv2.imread(template_path, 0)
    if template is None:
        print(f"  [WARNING] Template file {template_path} not found!")
    else:
        best_val = 0
        best_match = None

        for scale in np.linspace(0.6, 1.5, 15):
            resized_tpl = cv2.resize(template, None, fx=scale, fy=scale)
            if (
                resized_tpl.shape[0] > scr_gray.shape[0]
                or resized_tpl.shape[1] > scr_gray.shape[1]
            ):
                continue
            res = cv2.matchTemplate(scr_gray, resized_tpl, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(res)
            if max_val > best_val:
                best_val = max_val
                best_match = (max_loc, resized_tpl.shape[::-1])

        if best_val >= threshold:
            (x, y), (w, h) = best_match
            print(f"  [DEBUG] Template matched with score: {best_val:.2f}")
            coords = ((x + w // 2) / scale_factor, (y + h // 2) / scale_factor)
            return coords, screenshot, "Template Matching"
        else:
            print(f"  [DEBUG] Template matching score too low: {best_val:.2f}")

    print(f"  [DEBUG] No icon found through any method")
    return (None, None), screenshot, None


# ================= AUTOMATION =================
def is_notepad_running():
    """Fast: Check if Notepad is running using psutil"""
    try:
        return any(
            p.name().lower() == "notepad.exe" for p in psutil.process_iter(["name"])
        )
    except:
        return False


def open_notepad():
    """Open Notepad with retry logic (up to 3 attempts). Returns (success, screenshot, detection_method, coords)"""
    max_attempts = 3
    retry_delay = 1
    last_screenshot = None
    last_detection_method = None
    last_coords = None

    for attempt in range(1, max_attempts + 1):
        print(f"  [ATTEMPT {attempt}/{max_attempts}] Searching for Notepad icon...")
        result = find_icon(TEMPLATE_PATH)
        coords, screenshot, detection_method = result
        last_screenshot = screenshot
        last_detection_method = detection_method

        if coords is not None and coords[0] is not None:
            last_coords = coords
            print(f"  [INFO] Icon found at {coords}. Opening...")
            pyautogui.doubleClick(coords)
            time.sleep(2)  # Give it time to open

            # Validate that Notepad actually launched
            if is_notepad_running():
                print("  [SUCCESS] Notepad launched successfully")
                return True, screenshot, detection_method, coords
            else:
                print(
                    "  [WARNING] Double-click registered but Notepad not running, retrying..."
                )
        else:
            print(f"  [WARNING] Icon not found on attempt {attempt}/{max_attempts}")

        if attempt < max_attempts:
            print(f"  [INFO] Retrying in {retry_delay}s...")
            time.sleep(retry_delay)

    print(f"  [ERROR] Failed to open Notepad after {max_attempts} attempts.")
    return False, last_screenshot, last_detection_method, last_coords


def fetch_posts():
    """Fetch first 10 posts from JSONPlaceholder API"""
    url = "https://jsonplaceholder.typicode.com/posts"
    # Using a robust User-Agent to avoid ConnectionReset (10054)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        print("  [API] Fetching first 10 posts from API...")
        res = requests.get(url, headers=headers, timeout=15)
        res.raise_for_status()
        data = res.json()
        print(f"  [SUCCESS] Received {len(data)} posts, processing first 10.")
        return data[:10]  # Process first 10 posts

    except Exception as e:
        print(f"  [ERROR] API Request failed: {e}")
        print("  [WARNING] Using fallback data (1 post only)")
        return [
            {
                "id": 1,
                "title": "Network Error Fallback",
                "body": "The API was unavailable. Please check your connection and retry.",
            }
        ]


def save_and_close_notepad(post):
    """Save post content to file and close Notepad with error handling"""
    try:
        # 1. Type Content
        content = f"Title: {post['title']}\n\n{post['body']}"
        pyperclip.copy(content)
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.5)

        # 2. Trigger Save Dialog
        print("  [INFO] Opening save dialog...")
        pyautogui.hotkey("ctrl", "s")
        time.sleep(0.5)

        # 3. Set Save Location
        pyautogui.hotkey("ctrl", "l")  # Address bar
        time.sleep(0.5)
        clean_path = SAVE_DIR.replace("/", "\\")
        pyperclip.copy(clean_path)
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.1)
        pyautogui.press("enter")
        time.sleep(0.5)

        # 4. Set Filename
        pyautogui.press("tab", presses=1, interval=0.1)  # Move to file name field
        pyautogui.hotkey("alt", "n")  # Focus file name field
        time.sleep(0.3)
        filename = f"post_{post['id']}.txt"
        pyperclip.copy(filename)
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.3)

        # 5. Confirm Save (with handling for overwrite dialogs)
        pyautogui.press("enter")
        time.sleep(1)

        # 6. Close Notepad
        print("  [INFO] Closing Notepad...")
        pyautogui.hotkey("alt", "f4")
        time.sleep(0.3)

        print(
            f"  [SUCCESS] Post {post['id']} saved to {os.path.join(SAVE_DIR, filename)}"
        )
        return True

    except Exception as e:
        print(f"  [ERROR] Save failed: {e}")
        try:
            pyautogui.hotkey("alt", "f4")
            time.sleep(0.5)
            pyautogui.press("n")
        except:
            pass
        return False


# ================= MAIN =================
def main():
    print("=" * 60)
    print("Vision-Based Desktop Automation - Notepad Launcher")
    print("=" * 60)

    # Fetch posts first while the network is clear
    posts = fetch_posts()
    print(f"\n[TOTAL POSTS TO PROCESS] {len(posts)} posts")

    original_wallpaper = get_current_wallpaper()
    create_black_bg()

    successful_posts = 0
    failed_posts = 0

    try:
        print("\n[STEP 1] Preparing environment...")
        set_wallpaper(TEMP_BLACK_IMAGE)
        show_desktop()

        for idx, post in enumerate(posts, 1):
            print(f"\n{'=' * 60}")
            print(f"[POST {idx}/{len(posts)}] Processing post ID {post['id']}")
            print(f"{'=' * 60}")

            clear_selection()
            result = open_notepad()
            success, screenshot, detection_method, coords = result

            # Save annotated screenshot
            if screenshot is not None:
                save_annotated_screenshot(screenshot, coords, detection_method, idx)

            if success:
                if save_and_close_notepad(post):
                    print(f"  [✓ SUCCESS] Post {idx} finished successfully.")
                    successful_posts += 1
                else:
                    print(f"  [✗ FAILED] Post {idx} - Save operation failed.")
                    failed_posts += 1
            else:
                print(f"  [✗ FAILED] Post {idx} - Could not open Notepad.")
                failed_posts += 1

        print(f"\n{'=' * 60}")
        print(f"[SUMMARY] Completed: {successful_posts}/{len(posts)} posts")
        if failed_posts > 0:
            print(f"[WARNING] {failed_posts} posts failed")
        print(f"[SCREENSHOTS] Saved to: {SCREENSHOT_DIR}")
        print(f"{'=' * 60}")

    except Exception as e:
        print(f"\n[CRITICAL ERROR] {e}")
        import traceback

        traceback.print_exc()

    finally:
        print("\n[STEP 3] Restoring original system state...")
        if original_wallpaper:
            set_wallpaper(original_wallpaper)
        if os.path.exists(TEMP_BLACK_IMAGE):
            os.remove(TEMP_BLACK_IMAGE)
        print("  Cleanup finished.")
        print("=" * 60)


if __name__ == "__main__":
    main()
