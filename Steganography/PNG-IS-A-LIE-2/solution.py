#!/usr/bin/env python3
"""
PNG is a lie (part 2/2) - beginner friendly helper script

What this script does:
1. Opens the PNG recovered in part 1 (default: extracted.png)
2. Isolates RGB bit plane 0 (least-significant bit of R, G, B)
3. Combines those three planes using OR
4. Rebuilds the QR as a clean module grid
5. Repairs the 3 finder patterns and adds a quiet zone
6. Saves a cleaned QR image
7. Also creates a scanner-friendly QR re-encoded from the decoded URL
8. Prints the zbarimg command you can run

This script is intentionally written in a readable way so solvers can follow it.
"""

from pathlib import Path
import shutil
import subprocess

import numpy as np
from PIL import Image
import qrcode


# ----------------------------
# Settings found during solving
# ----------------------------
BASE_DIR = Path(__file__).resolve().parent
INPUT_IMAGE = BASE_DIR / "extracted.png"

# The QR almost fills the whole image, so we trim a small border first.
CROP_LEFT = 36
CROP_TOP = 36
CROP_SIZE = 928

# QR Version 16 -> 81 x 81 modules
QR_VERSION = 16
MODULE_COUNT = 17 + 4 * QR_VERSION

# While rebuilding each QR cell, we only sample the center of the cell.
# This helps ignore noisy edges.
CENTER_SAMPLE_RATIO = 0.65

# If at least this fraction of sampled pixels are "on", we mark that QR cell black.
MODULE_THRESHOLD = 0.35

# Final output scale and border (quiet zone)
OUTPUT_SCALE = 8
QUIET_ZONE_MODULES = 6

# This is the text we got after decoding the repaired QR during solving.
# We re-encode it at the end so zbarimg can reliably scan a perfect QR too.
DECODED_URL = "https://www.youtube.com/watch?v=lpiB2wMc49g?flqg=THC{Y'411_s0_r1Ckr0113D}"


# ----------------------------
# Helper functions
# ----------------------------
def save_gray(array, path):
    Image.fromarray(array.astype(np.uint8), mode="L").save(path)


def make_finder_pattern():
    """Return the standard 7x7 QR finder pattern with 1=black, 0=white."""
    finder = np.ones((7, 7), dtype=np.uint8)
    finder[1:6, 1:6] = 0
    finder[2:5, 2:5] = 1
    return finder


def render_qr_grid(grid, scale=8, quiet_zone_modules=6):
    """Render a QR grid (1=black, 0=white) into a large clean image."""
    h, w = grid.shape
    canvas = np.zeros((h + 2 * quiet_zone_modules, w + 2 * quiet_zone_modules), dtype=np.uint8)
    canvas[quiet_zone_modules:quiet_zone_modules + h, quiet_zone_modules:quiet_zone_modules + w] = grid

    # Convert 1=black,0=white grid to image pixels: black=0, white=255
    image = (255 * (1 - canvas)).astype(np.uint8)
    pil = Image.fromarray(image, mode="L")
    pil = pil.resize((pil.width * scale, pil.height * scale), Image.Resampling.NEAREST)
    return pil


def repair_finder_patterns(grid):
    """Repair the three big QR corner markers."""
    finder = make_finder_pattern()
    n = grid.shape[0]

    # Clear an 8x8 area first so the separators around the finder become white.
    grid[:8, :8] = 0
    grid[:8, n - 8:] = 0
    grid[n - 8:, :8] = 0

    # Put the real 7x7 finder squares back.
    grid[:7, :7] = finder
    grid[:7, n - 7:] = finder
    grid[n - 7:, :7] = finder

    return grid


def extract_rgb_bit0_or(input_path):
    """Get the least significant bit of R, G, B and combine them using OR."""
    img = Image.open(input_path).convert("RGB")
    arr = np.array(img)

    r0 = arr[:, :, 0] & 1
    g0 = arr[:, :, 1] & 1
    b0 = arr[:, :, 2] & 1

    # In this challenge, the useful QR pixels become visible when we OR the 3 channels.
    # 1 means the hidden bit is present in at least one color channel.
    hidden = (r0 | g0 | b0).astype(np.uint8)

    return hidden, r0, g0, b0


def rebuild_qr_from_crop(hidden_bits):
    """
    Rebuild the QR as clean square modules.

    hidden_bits is a binary image where 1 means the hidden bit is present.
    """
    crop = hidden_bits[CROP_TOP:CROP_TOP + CROP_SIZE, CROP_LEFT:CROP_LEFT + CROP_SIZE]
    cell_size = CROP_SIZE / MODULE_COUNT

    grid = np.zeros((MODULE_COUNT, MODULE_COUNT), dtype=np.uint8)

    for row in range(MODULE_COUNT):
        y0 = row * cell_size
        y1 = (row + 1) * cell_size
        yc = (y0 + y1) / 2.0
        half_h = (y1 - y0) * CENTER_SAMPLE_RATIO / 2.0
        ya = max(0, int(round(yc - half_h)))
        yb = min(crop.shape[0], int(round(yc + half_h)))

        for col in range(MODULE_COUNT):
            x0 = col * cell_size
            x1 = (col + 1) * cell_size
            xc = (x0 + x1) / 2.0
            half_w = (x1 - x0) * CENTER_SAMPLE_RATIO / 2.0
            xa = max(0, int(round(xc - half_w)))
            xb = min(crop.shape[1], int(round(xc + half_w)))

            block = crop[ya:yb, xa:xb]
            block_mean = float(block.mean()) if block.size else 0.0

            # If enough pixels in this cell are "on", mark the module black.
            # In our QR grid: 1 means black, 0 means white.
            grid[row, col] = 1 if block_mean >= MODULE_THRESHOLD else 0

    return grid


def make_perfect_qr_from_text(text, output_path):
    """Create a perfect scanner-friendly QR from known decoded text."""
    qr = qrcode.QRCode(
        version=QR_VERSION,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=6,
    )
    qr.add_data(text)
    qr.make(fit=False)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(output_path)


def maybe_run_zbarimg(image_path):
    """Run zbarimg if it is installed, otherwise just print the command."""
    cmd = ["zbarimg", str(image_path)]
    print("\nRun this command to decode the final QR:")
    print(" ".join(cmd))

    if shutil.which("zbarimg"):
        print("\n[zbarimg output]")
        subprocess.run(cmd, check=False)
    else:
        print("\nzbarimg was not found in this environment, so I only printed the command.")


# ----------------------------
# Main flow
# ----------------------------
def main():
    if not INPUT_IMAGE.exists():
        raise SystemExit(f"Input image not found: {INPUT_IMAGE}")

    out_dir = INPUT_IMAGE.parent

    raw_or_path = out_dir / "01_rgb_bit0_or_raw.png"
    rebuilt_path = out_dir / "02_qr_rebuilt_cleaned.png"
    perfect_path = out_dir / "03_qr_scanner_friendly.png"

    hidden, r0, g0, b0 = extract_rgb_bit0_or(INPUT_IMAGE)

    # Save the raw OR image so solvers can compare it with what StegSolve shows.
    save_gray(hidden * 255, raw_or_path)

    # Rebuild the QR grid from the noisy bit-plane image.
    grid = rebuild_qr_from_crop(hidden)

    # Repair the 3 finder patterns.
    grid = repair_finder_patterns(grid)

    # Render a clean QR image from the rebuilt grid.
    cleaned = render_qr_grid(grid, scale=OUTPUT_SCALE, quiet_zone_modules=QUIET_ZONE_MODULES)
    cleaned.save(rebuilt_path)

    # Make a perfect QR from the already-decoded URL so scanners can read it easily.
    make_perfect_qr_from_text(DECODED_URL, perfect_path)

    print("Done.")
    print(f"Saved raw RGB bit-0 OR image : {raw_or_path}")
    print(f"Saved cleaned rebuilt QR     : {rebuilt_path}")
    print(f"Saved scanner-friendly QR    : {perfect_path}")
    print(f"Decoded URL from solving     : {DECODED_URL}")

    maybe_run_zbarimg(perfect_path)


if __name__ == "__main__":
    main()
