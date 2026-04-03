import pyautogui
import cv2
import numpy as np
import time
import requests
import os
import subprocess
import pytesseract
import ctypes
import winreg

# ================= CONFIG =================
TEMPLATE_PATH = "SimplerApproach/Notepads.png"
SAVE_DIR = os.path.join(os.path.expanduser("~"), "Desktop", "tjm-project")
SCREENWIDTH, SCREENHEIGHT = pyautogui.size()
TEMP_BLACK_IMAGE = os.path.join(os.getcwd(), "temp_black_bg.png")

# If Tesseract is not in your PATH, set the line below:
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

if os.path.exists(SAVE_DIR):
    os.system(f'rmdir /S /Q "{SAVE_DIR}"')  # Clear old saves
os.makedirs(SAVE_DIR)


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
    pyautogui.hotkey("win", "d")
    time.sleep(1)


def clear_selection():
    pyautogui.click(SCREENWIDTH / 2, SCREENHEIGHT / 2)
    time.sleep(0.2)


def take_screenshot():
    screenshot = pyautogui.screenshot()
    return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)


# ================= DETECTION =================
def find_icon(template_path, threshold=0.7):
    screenshot = take_screenshot()
    scale_factor = 1.0

    scr_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)

    # OCR Detection
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
                return cx, cy
    except:
        pass

    # Template Matching
    print("  [DEBUG] Running template matching...")
    template = cv2.imread(template_path, 0)
    if template is None:
        print(f"  [ERROR] Template file {template_path} not found!")
        return None

    best_val = 0
    best_match = None

    for scale in np.linspace(0.7, 1.3, 10):
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
        return (x + w // 2) / scale_factor, (y + h // 2) / scale_factor

    print(f"  [DEBUG] No icon found. Best score: {best_val:.2f}")
    return None


# ================= AUTOMATION =================
def open_notepad():
    print("  [DEBUG] Searching for Notepad icon...")
    coords = find_icon(TEMPLATE_PATH)

    if coords:
        print(f"  [INFO] Icon found at {coords}. Opening...")
        pyautogui.doubleClick(coords)
        time.sleep(2)  # Give it time to open
        return True

    print("  [ERROR] Icon not found on desktop.")
    return False


def fetch_posts():
    url = "https://jsonplaceholder.typicode.com/posts"
    # Using a robust User-Agent to avoid ConnectionReset (10054)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        print(f"  [API] Fetching data...")
        res = requests.get(url, headers=headers, timeout=15)
        res.raise_for_status()
        data = res.json()
        print(f"  [SUCCESS] Received {len(data)} posts.")
        return data[:1]  # Limit to 1 for testing

    except Exception as e:
        print(f"  [ERROR] API Request failed: {e}")
        return [
            {
                "id": 1,
                "title": "Network Error Fallback",
                "body": "Please check your connection.",
            }
        ]


def save_and_close_notepad(post):
    try:
        # 1. Type Content
        content = f"Title: {post['title']}\n\n{post['body']}"
        subprocess.run(["clip.exe"], input=content.encode("utf-16"), check=False)
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.5)

        # 2. Trigger Save Dialog
        print("  [INFO] Opening save dialog...")
        pyautogui.hotkey("ctrl", "s")
        time.sleep(1.5)

        # 3. Set Save Location
        pyautogui.hotkey("ctrl", "l")  # Address bar
        time.sleep(0.5)
        clean_path = SAVE_DIR.replace("/", "\\")
        pyautogui.write(clean_path)
        pyautogui.press("enter")
        time.sleep(0.5)

        # 4. Set Filename
        pyautogui.press("tab", presses=1, interval=0.3)  # Move to file name field
        pyautogui.hotkey("alt", "n")  # Focus file name field
        time.sleep(0.3)
        filename = f"post_{post['id']}.txt"
        pyautogui.write(filename)
        time.sleep(0.5)

        # 5. Confirm Save
        pyautogui.press("enter")
        time.sleep(1)

        # 6. Close
        print("  [INFO] Closing Notepad...")
        pyautogui.hotkey("alt", "f4")
        time.sleep(0.5)
        pyautogui.press("n")  # In case of "Already exists" or error prompt
        return True

    except Exception as e:
        print(f"  [ERROR] Save failed: {e}")
        pyautogui.hotkey("alt", "f4")
        return False


# ================= MAIN =================
def main():
    # Fetch posts first while the network is clear
    posts = fetch_posts()

    original_wallpaper = get_current_wallpaper()
    create_black_bg()

    try:
        print("\n[STEP 1] Preparing environment...")
        set_wallpaper(TEMP_BLACK_IMAGE)
        show_desktop()

        for idx, post in enumerate(posts, 1):
            print(f"\n--- Processing Post {idx} ---")
            clear_selection()
            if open_notepad():
                save_and_close_notepad(post)
                print(f"  [SUCCESS] Post {idx} finished.")
            else:
                print(f"  [FAILED] Skipping post {idx} - icon missing.")

    finally:
        print("\n[STEP 3] Restoring original system state...")
        if original_wallpaper:
            set_wallpaper(original_wallpaper)
        if os.path.exists(TEMP_BLACK_IMAGE):
            os.remove(TEMP_BLACK_IMAGE)
        print("  Finished.")


if __name__ == "__main__":
    main()
