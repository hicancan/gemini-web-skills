"""
Reverse Alpha Blending — remove Gemini invisible watermark.
Usage: uv run --with Pillow --with numpy scripts/remove_watermark.py <input> [--alpha 0.01]

Reference: GargantuaX/gemini-watermark-remover (4225 stars)
Algorithm: original = (watermarked - alpha * 255) / (1 - alpha)
"""
import argparse
import os
import sys
import numpy as np
from PIL import Image


def remove_watermark(arr: np.ndarray, alpha: float = 0.01) -> np.ndarray:
    """Apply reverse alpha blending to remove Gemini watermark."""
    img = arr.astype(np.float32) / 255.0
    a = min(max(alpha, 0), 0.99)
    one_minus = 1.0 - a
    result = img.copy()
    for c in range(3):
        result[..., c] = np.clip((img[..., c] - a) / one_minus, 0, 1)
    return (result * 255).astype(np.uint8)


def main():
    parser = argparse.ArgumentParser(description="Remove Gemini invisible watermark")
    parser.add_argument("input", help="Input PNG path")
    parser.add_argument("--alpha", type=float, default=0.01,
                        help="Watermark opacity (default: 0.01)")
    parser.add_argument("--output", "-o", help="Output path (default: input_cleaned.png)")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"ERROR: {args.input} not found", file=sys.stderr)
        sys.exit(1)

    out = args.output or args.input.replace(".png", "_cleaned.png")

    img = Image.open(args.input).convert("RGB")
    arr = np.array(img)
    cleaned = remove_watermark(arr, args.alpha)
    Image.fromarray(cleaned).save(out)

    orig_kb = os.path.getsize(args.input) / 1024
    clean_kb = os.path.getsize(out) / 1024
    print(f"OK: {img.size[0]}x{img.size[1]} | α={args.alpha} | {orig_kb:.0f}KB → {clean_kb:.0f}KB | → {out}")


if __name__ == "__main__":
    main()
