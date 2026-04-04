"""
Screenshot annotation helper for vision-based desktop automation
This script captures the desktop and annotates it with icon detection results.
Run this with the Notepad icon in different positions to generate annotated screenshots.
"""

import pyautogui
import cv2
import numpy as np
import os
import time
from main import (
    find_icon,
    take_screenshot,
    TEMPLATE_PATH,
    SCREENWIDTH,
    SCREENHEIGHT,
)


def annotate_screenshot_with_detection(screenshot, coords, position_name="unknown"):
    """Annotate a screenshot with detection results"""
    annotated = screenshot.copy()

    if coords:
        x, y = int(coords[0]), int(coords[1])
        # Draw a circle around detected position
        cv2.circle(annotated, (x, y), 40, (0, 255, 0), 3)
        cv2.circle(annotated, (x, y), 60, (0, 255, 0), 2)

        # Draw crosshairs
        cv2.line(annotated, (x - 20, y), (x + 20, y), (0, 255, 0), 2)
        cv2.line(annotated, (x, y - 20), (x, y + 20), (0, 255, 0), 2)

        # Add text annotation
        text = f"Detected at ({x}, {y})"
        cv2.putText(
            annotated,
            text,
            (x - 50, y - 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
        )
        cv2.putText(
            annotated,
            position_name,
            (50, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 0),
            2,
        )

        return annotated, True
    else:
        # Add "not found" text
        cv2.putText(
            annotated,
            "Icon NOT detected",
            (SCREENWIDTH // 2 - 150, SCREENHEIGHT // 2),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.5,
            (0, 0, 255),
            3,
        )
        cv2.putText(
            annotated,
            position_name,
            (50, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 0, 255),
            2,
        )
        return annotated, False


def capture_annotated_screenshot(position_name, output_dir="annotated_screenshots"):
    """Capture and annotate a screenshot"""
    os.makedirs(output_dir, exist_ok=True)

    print(f"\n[CAPTURE] {position_name}")
    print(f"Position the Notepad icon in the {position_name} area")
    print(f"Press ENTER when ready to capture... ", end="", flush=True)
    input()

    # Capture screenshot
    screenshot = take_screenshot()

    # Detect icon
    print(f"Detecting icon...", end="", flush=True)
    coords = find_icon(TEMPLATE_PATH)
    print(f" Done")

    # Annotate
    annotated, found = annotate_screenshot_with_detection(
        screenshot, coords, position_name
    )

    # Save
    filename = f"{position_name.replace(' ', '_').lower()}_detection.png"
    filepath = os.path.join(output_dir, filename)
    annotated_bgr = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)
    cv2.imwrite(filepath, annotated_bgr)

    print(f"✓ Saved: {filepath}")
    print(f"  Detection: {'SUCCESS' if found else 'FAILED'}")
    if coords:
        print(f"  Coordinates: ({int(coords[0])}, {int(coords[1])})")

    return filepath, found


def main():
    print("=" * 60)
    print("Vision-Based Desktop Automation - Screenshot Capture")
    print("=" * 60)

    positions = ["top_left_area", "center_of_screen", "bottom_right_area"]

    results = []

    for position in positions:
        try:
            filepath, found = capture_annotated_screenshot(position)
            results.append((position, found, filepath))
        except Exception as e:
            print(f"✗ Error capturing {position}: {e}")
            results.append((position, False, None))

    # Summary
    print(f"\n{'=' * 60}")
    print("CAPTURE SUMMARY")
    print(f"{'=' * 60}")

    for position, found, filepath in results:
        status = "✓ SUCCESS" if found else "✗ FAILED"
        print(f"{status}: {position}")
        if filepath:
            print(f"         → {filepath}")

    successful = sum(1 for _, found, _ in results if found)
    print(f"\nTotal: {successful}/{len(results)} successful captures")
    print("=" * 60)


if __name__ == "__main__":
    main()
