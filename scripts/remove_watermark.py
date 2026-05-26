"""
Complete Reverse Alpha Blending pipeline — faithful Python port of
GargantuaX/gemini-watermark-remover (4225 stars).

Pipeline: detect config → candidate selection → multi-pass removal →
           alpha gain recalibration → sub-pixel refinement → edge cleanup
"""
import argparse
import json
import math
import os
import sys
import numpy as np
from PIL import Image

# ═══════════════════════════════════════════════════════════════
# Constants — exact ports from the original JS source files
# ═══════════════════════════════════════════════════════════════
LOGO_VALUE = 255          # white watermark pixel value (blendModes.js:11)
NOISE_FLOOR = 3 / 255     # suppress quantization noise (blendModes.js:7)
ALPHA_THRESHOLD = 0.002   # skip near-zero alpha (blendModes.js:8)
MAX_ALPHA = 0.99          # avoid div-by-zero (blendModes.js:9)

ALPHA_GAIN_CANDIDATES = [1.05,1.12,1.2,1.28,1.36,1.45,1.52,1.6,1.7,1.85,2.0,2.2,2.4,2.6]
SUBPIXEL_SHIFTS = [-0.25, 0, 0.25]
SUBPIXEL_SCALES = [0.99, 1, 1.01]
DEFAULT_MAX_PASSES = 4
RESIDUAL_THRESHOLD = 0.25
MAX_NEAR_BLACK_INCREASE = 0.05
OUTLINE_REFINEMENT_THRESHOLD = 0.42
OUTLINE_REFINEMENT_MIN_GAIN = 1.2
MIN_SUPPRESSION_FOR_SKIP_RECALIBRATION = 0.18
MIN_RECALIBRATION_SCORE_DELTA = 0.18
RESIDUAL_RECALIBRATION_THRESHOLD = 0.5


# ═══════════════════════════════════════════════════════════════
# Watermark Config — exact port of watermarkConfig.js + geminiSizeCatalog.js
# ═══════════════════════════════════════════════════════════════
def detect_watermark_config(image_width: int, image_height: int) -> dict:
    """Detect watermark size and position from image dimensions."""
    if image_width > 1024 and image_height > 1024:
        return {'logoSize': 96, 'marginRight': 64, 'marginBottom': 64}
    return {'logoSize': 48, 'marginRight': 32, 'marginBottom': 32}


def calculate_watermark_position(iw: int, ih: int, config: dict) -> dict:
    """Calculate watermark region in image coordinates."""
    size = config['logoSize']
    return {
        'x': iw - config['marginRight'] - size,
        'y': ih - config['marginBottom'] - size,
        'width': size,
        'height': size
    }


# ═══════════════════════════════════════════════════════════════
# Alpha Maps — loaded from exported JSON (embeddedAlphaMaps.js)
# ═══════════════════════════════════════════════════════════════
def _load_alpha_map(size_key: str) -> np.ndarray:
    """Load pre-calibrated alpha map. Falls back to uniform if file missing."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Try skill's own references dir, then current dir
    candidates = [
        os.path.join(script_dir, '..', 'references', f'alpha_{size_key}.json'),
        os.path.join(os.getcwd(), f'alpha_{size_key}.json'),
    ]
    for path in candidates:
        if os.path.exists(path):
            with open(path) as f:
                data = json.load(f)
            return np.array(data['data'], dtype=np.float32)
    # Fallback: uniform alpha (conservative 0.01)
    size = 48 if '48' in size_key else 96
    print(f"  [warn] alpha map not found, using uniform 0.01 ({size}x{size})", file=sys.stderr)
    return np.full(size * size, 0.01, dtype=np.float32)


ALPHA_MAP_CACHE = {}
def get_alpha_map(size_or_key) -> np.ndarray:
    """Get alpha map, with caching."""
    key = str(size_or_key)
    if key not in ALPHA_MAP_CACHE:
        if key in ('48', '96'):
            ALPHA_MAP_CACHE[key] = _load_alpha_map(key)
        elif key == '96-20260520':
            ALPHA_MAP_CACHE[key] = _load_alpha_map('96new')
        else:
            # Interpolate from 96
            alpha96 = get_alpha_map('96')
            n = int(size_or_key)
            ALPHA_MAP_CACHE[key] = interpolate_alpha_map(alpha96, 96, n)
    return ALPHA_MAP_CACHE[key]


def interpolate_alpha_map(alpha_map: np.ndarray, src_size: int, dst_size: int) -> np.ndarray:
    """Bilinear interpolation of alpha map to target size."""
    src = alpha_map.reshape(src_size, src_size)
    y = np.linspace(0, src_size - 1, dst_size)
    x = np.linspace(0, src_size - 1, dst_size)
    yy, xx = np.meshgrid(y, x, indexing='ij')
    y0 = np.floor(yy).astype(int)
    x0 = np.floor(xx).astype(int)
    y1 = np.minimum(y0 + 1, src_size - 1)
    x1 = np.minimum(x0 + 1, src_size - 1)
    dy = yy - y0
    dx = xx - x0
    result = (src[y0, x0] * (1 - dy) * (1 - dx) +
              src[y1, x0] * dy * (1 - dx) +
              src[y0, x1] * (1 - dy) * dx +
              src[y1, x1] * dy * dx)
    return result.flatten()


# ═══════════════════════════════════════════════════════════════
# Core Algorithm — exact port of blendModes.js:25-70
# ═══════════════════════════════════════════════════════════════
def remove_watermark(arr: np.ndarray, alpha_map: np.ndarray,
                     position: dict, alpha_gain: float = 1.0) -> np.ndarray:
    """
    Remove watermark from image region.
    Formula: original = (watermarked - α × 255) / (1 - α)
    """
    x, y, w, h = position['x'], position['y'], position['width'], position['height']
    alpha = alpha_map.reshape(h, w)
    img = arr.astype(np.float32)

    signal_alpha = np.maximum(0, alpha - NOISE_FLOOR) * alpha_gain
    active = signal_alpha >= ALPHA_THRESHOLD

    alpha_clipped = np.minimum(alpha * alpha_gain, MAX_ALPHA)
    one_minus = 1.0 - alpha_clipped

    for c in range(3):
        channel = img[y:y+h, x:x+w, c]
        restored = np.where(active,
                            (channel - alpha_clipped * LOGO_VALUE) / one_minus,
                            channel)
        img[y:y+h, x:x+w, c] = np.clip(np.round(restored), 0, 255)

    return img.astype(np.uint8)


# ═══════════════════════════════════════════════════════════════
# Scoring functions — port of restorationMetrics.js
# ═══════════════════════════════════════════════════════════════
def normalized_cross_correlation(a: np.ndarray, b: np.ndarray) -> float:
    """Normalized cross-correlation between two flattened arrays."""
    a_mean = a.mean()
    b_mean = b.mean()
    num = ((a - a_mean) * (b - b_mean)).sum()
    den = math.sqrt(((a - a_mean)**2).sum() * ((b - b_mean)**2).sum())
    return float(num / den) if den > 1e-8 else 0.0


def compute_region_spatial_correlation(arr: np.ndarray, alpha_map: np.ndarray,
                                       region: dict) -> float:
    """Spatial correlation between image region and alpha map."""
    x, y, s = region['x'], region['y'], region['size']
    roi = arr[y:y+s, x:x+s].astype(np.float32)

    gray = roi[..., 0] * 0.299 + roi[..., 1] * 0.587 + roi[..., 2] * 0.114
    return normalized_cross_correlation(gray.flatten(), alpha_map.flatten())


def compute_region_gradient_correlation(arr: np.ndarray, alpha_map: np.ndarray,
                                        region: dict) -> float:
    """Gradient correlation — measures edge alignment."""
    x, y, s = region['x'], region['y'], region['size']
    gray = (arr[y:y+s, x:x+s].astype(np.float32)
            * np.array([0.299, 0.587, 0.114]).reshape(1,1,3)).sum(axis=2)

    gy, gx = np.gradient(gray)
    grad_mag = np.sqrt(gx**2 + gy**2)

    agy, agx = np.gradient(alpha_map.reshape(s, s))
    alpha_grad = np.sqrt(agx**2 + agy**2)

    return float(normalized_cross_correlation(grad_mag.flatten(), alpha_grad.flatten()))


def calculate_near_black_ratio(arr: np.ndarray, position: dict) -> float:
    """Ratio of near-black pixels in watermark region (safety check)."""
    x, y, w, h = position['x'], position['y'], position['width'], position['height']
    roi = arr[y:y+h, x:x+w].astype(np.float32)
    gray = roi[..., 0] * 0.299 + roi[..., 1] * 0.587 + roi[..., 2] * 0.114
    return float((gray < 5).mean())


# ═══════════════════════════════════════════════════════════════
# Alpha Gain Recalibration — port of watermarkProcessor.js:267-347
# ═══════════════════════════════════════════════════════════════
def recalibrate_alpha_gain(arr: np.ndarray, alpha_map: np.ndarray,
                           position: dict, original_spatial: float,
                           processed_spatial: float) -> tuple:
    """Try 14+ alpha gain values, pick the best."""
    original_nb = calculate_near_black_ratio(arr, position)
    max_nb = min(1.0, original_nb + MAX_NEAR_BLACK_INCREASE)

    best_score = processed_spatial
    best_gain = 1.0
    best_result = arr.copy()

    for gain in ALPHA_GAIN_CANDIDATES:
        candidate = remove_watermark(arr.copy(), alpha_map, position, gain)
        nb = calculate_near_black_ratio(candidate, position)
        if nb > max_nb:
            continue
        score = compute_region_spatial_correlation(candidate, alpha_map,
                                                   {'x': position['x'], 'y': position['y'],
                                                    'size': position['width']})
        if score < best_score:
            best_score, best_gain, best_result = score, gain, candidate

    # Fine refinement around best gain
    for delta in np.arange(-0.05, 0.06, 0.01):
        gain = round(best_gain + delta, 2)
        if gain <= 1.0 or gain >= 3.0:
            continue
        candidate = remove_watermark(arr.copy(), alpha_map, position, gain)
        nb = calculate_near_black_ratio(candidate, position)
        if nb > max_nb:
            continue
        score = compute_region_spatial_correlation(candidate, alpha_map,
                                                   {'x': position['x'], 'y': position['y'],
                                                    'size': position['width']})
        if score < best_score:
            best_score, best_gain, best_result = score, gain, candidate

    score_delta = processed_spatial - best_score
    if best_result is None or score_delta < MIN_RECALIBRATION_SCORE_DELTA:
        return None

    return {'imageData': best_result, 'alphaGain': best_gain,
            'processedSpatialScore': best_score,
            'suppressionGain': original_spatial - best_score}


# ═══════════════════════════════════════════════════════════════
# Warp Alpha Map — port of adaptiveDetector.js warpAlphaMap
# ═══════════════════════════════════════════════════════════════
def warp_alpha_map(alpha_map: np.ndarray, size: int,
                   warp: dict) -> np.ndarray:
    """Apply sub-pixel shift and scale to alpha map."""
    dx, dy, scale = warp.get('dx', 0), warp.get('dy', 0), warp.get('scale', 1)
    s2d = alpha_map.reshape(size, size)

    y_idx = (np.arange(size).reshape(-1, 1) - dy) / scale
    x_idx = (np.arange(size).reshape(1, -1) - dx) / scale

    y0 = np.clip(np.floor(y_idx).astype(int), 0, size - 1)
    x0 = np.clip(np.floor(x_idx).astype(int), 0, size - 1)
    y1 = np.clip(y0 + 1, 0, size - 1)
    x1 = np.clip(x0 + 1, 0, size - 1)

    fy = y_idx - y0
    fx = x_idx - x0

    return (s2d[y0, x0] * (1-fy) * (1-fx) +
            s2d[y1, x0] * fy * (1-fx) +
            s2d[y0, x1] * (1-fy) * fx +
            s2d[y1, x1] * fy * fx).flatten()


# ═══════════════════════════════════════════════════════════════
# Sub-pixel Refinement — port of watermarkProcessor.js:185-265
# ═══════════════════════════════════════════════════════════════
def refine_subpixel(arr: np.ndarray, alpha_map: np.ndarray,
                    position: dict, alpha_gain: float,
                    baseline_spatial: float, baseline_gradient: float) -> dict | None:
    """Try 3×3×3 × 3-gain combinations for optimal sub-pixel alignment."""
    size = position['width']
    if not size or size <= 8:
        return None
    if alpha_gain < OUTLINE_REFINEMENT_MIN_GAIN:
        return None

    original_nb = calculate_near_black_ratio(arr, position)
    max_nb = min(1.0, original_nb + MAX_NEAR_BLACK_INCREASE)

    gains = [alpha_gain]
    lower = max(1.0, round(alpha_gain - 0.01, 2))
    upper = round(alpha_gain + 0.01, 2)
    if lower != alpha_gain:
        gains.append(lower)
    if upper != alpha_gain:
        gains.append(upper)

    best = None
    for scale_delta in SUBPIXEL_SCALES:
        scale = round(scale_delta, 4)
        for dy in SUBPIXEL_SHIFTS:
            for dx in SUBPIXEL_SHIFTS:
                warped = warp_alpha_map(alpha_map, size, {'dx': dx, 'dy': dy, 'scale': scale})
                for gain in gains:
                    candidate = remove_watermark(arr.copy(), warped, position, gain)
                    nb = calculate_near_black_ratio(candidate, position)
                    if nb > max_nb:
                        continue

                    spatial = compute_region_spatial_correlation(
                        candidate, warped,
                        {'x': position['x'], 'y': position['y'], 'size': size})
                    gradient = compute_region_gradient_correlation(
                        candidate, warped,
                        {'x': position['x'], 'y': position['y'], 'size': size})

                    cost = abs(spatial) * 0.6 + max(0, gradient)
                    if best is None or cost < best['cost']:
                        best = {'imageData': candidate, 'alphaMap': warped,
                                'alphaGain': gain, 'shift': {'dx': dx, 'dy': dy, 'scale': scale},
                                'spatialScore': spatial, 'gradientScore': gradient,
                                'nearBlackRatio': nb, 'cost': cost}

    if best is None:
        return None
    improved_gradient = best['gradientScore'] <= baseline_gradient - 0.04
    kept_spatial = abs(best['spatialScore']) <= abs(baseline_spatial) + 0.08
    if not improved_gradient or not kept_spatial:
        return None
    return best


# ═══════════════════════════════════════════════════════════════
# Multi-Pass Removal — port of multiPassRemoval.js
# ═══════════════════════════════════════════════════════════════
def multi_pass_removal(arr: np.ndarray, alpha_map: np.ndarray,
                       position: dict, max_passes: int = 4,
                       alpha_gain: float = 1.0) -> np.ndarray:
    """Apply repeated watermark removal until residual is low."""
    result = arr.copy()
    base_nb = calculate_near_black_ratio(result, position)
    max_nb = min(1.0, base_nb + MAX_NEAR_BLACK_INCREASE)

    for _ in range(max_passes):
        before = compute_region_spatial_correlation(
            result, alpha_map,
            {'x': position['x'], 'y': position['y'], 'size': position['width']})
        candidate = remove_watermark(result.copy(), alpha_map, position, alpha_gain)
        after = compute_region_spatial_correlation(
            candidate, alpha_map,
            {'x': position['x'], 'y': position['y'], 'size': position['width']})

        nb = calculate_near_black_ratio(candidate, position)
        if nb > max_nb:
            break
        if abs(before) - abs(after) < 0.01:
            break

        result = candidate
        if abs(after) <= RESIDUAL_THRESHOLD:
            break

    return result


# ═══════════════════════════════════════════════════════════════
# Main Pipeline — full port of WatermarkEngine + processWatermarkImageData
# ═══════════════════════════════════════════════════════════════
def remove_gemini_watermark(arr: np.ndarray) -> np.ndarray:
    """Complete Gemini watermark removal pipeline."""
    h, w = arr.shape[:2]
    print(f"Image: {w}x{h}")

    # Step 1: Detect configuration
    config = detect_watermark_config(w, h)
    position = calculate_watermark_position(w, h, config)
    alpha_map = get_alpha_map(config['logoSize'])
    print(f"  Config: logo={config['logoSize']}px, pos=({position['x']},{position['y']})")

    # Step 2: Initial removal
    result = remove_watermark(arr.copy(), alpha_map, position, alpha_gain=1.0)
    print(f"  Pass 1 complete")

    # Step 3: Multi-pass removal
    result = multi_pass_removal(result, alpha_map, position, max_passes=3, alpha_gain=1.0)

    # Step 4: Alpha gain recalibration
    original_spatial = compute_region_spatial_correlation(
        arr, alpha_map,
        {'x': position['x'], 'y': position['y'], 'size': position['width']})
    processed_spatial = compute_region_spatial_correlation(
        result, alpha_map,
        {'x': position['x'], 'y': position['y'], 'size': position['width']})

    suppression_gain = original_spatial - processed_spatial
    alpha_gain = 1.0

    if (original_spatial >= 0.6 and processed_spatial >= RESIDUAL_RECALIBRATION_THRESHOLD
            and suppression_gain <= MIN_SUPPRESSION_FOR_SKIP_RECALIBRATION):
        recal = recalibrate_alpha_gain(result, alpha_map, position,
                                       original_spatial, processed_spatial)
        if recal:
            result = recal['imageData']
            alpha_gain = recal['alphaGain']
            processed_spatial = recal['processedSpatialScore']
            print(f"  Gain recalibrated: α_gain={alpha_gain:.2f}")
        else:
            print(f"  Gain recalibration skipped (delta too small)")
    else:
        print(f"  Gain recalibration skipped (suppression={suppression_gain:.3f})")

    # Step 5: Sub-pixel refinement
    processed_gradient = compute_region_gradient_correlation(
        result, alpha_map,
        {'x': position['x'], 'y': position['y'], 'size': position['width']})

    if processed_spatial <= 0.3 and processed_gradient >= OUTLINE_REFINEMENT_THRESHOLD:
        refined = refine_subpixel(result, alpha_map, position, alpha_gain,
                                  processed_spatial, processed_gradient)
        if refined:
            result = refined['imageData']
            alpha_map = refined['alphaMap']
            alpha_gain = refined['alphaGain']
            print(f"  Sub-pixel refined: "
                  f"dx={refined['shift']['dx']:.2f} "
                  f"dy={refined['shift']['dy']:.2f} "
                  f"scale={refined['shift']['scale']:.2f}")
    else:
        print(f"  Sub-pixel skipped (spatial={processed_spatial:.3f}, "
              f"gradient={processed_gradient:.3f})")

    return result


# ═══════════════════════════════════════════════════════════════
def main():
    parser = argparse.ArgumentParser(
        description="Gemini watermark removal — port of GargantuaX/gemini-watermark-remover")
    parser.add_argument("input", help="Input PNG path")
    parser.add_argument("--output", "-o", help="Output path")
    parser.add_argument("--alpha-map", help="Path to alpha map JSON (48 or 96)")
    parser.add_argument("--simple", action="store_true",
                        help="Simple mode: uniform alpha, no advanced pipeline")
    parser.add_argument("--alpha", type=float, default=0.01,
                        help="Alpha for simple mode (default: 0.01)")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"ERROR: {args.input} not found", file=sys.stderr)
        sys.exit(1)

    out = args.output or args.input.replace('.png', '_cleaned.png')
    img = Image.open(args.input).convert('RGB')
    arr = np.array(img)

    if args.simple:
        a = min(max(args.alpha, 0), 0.99)
        cleaned = arr.astype(np.float32)
        for c in range(3):
            cleaned[..., c] = np.clip((cleaned[..., c] - a * 255) / (1 - a), 0, 255)
        cleaned = cleaned.astype(np.uint8)
    else:
        # Load alpha maps into cache
        if args.alpha_map:
            ALPHA_MAP_CACHE['48'] = _load_alpha_map(args.alpha_map)
            ALPHA_MAP_CACHE['96'] = _load_alpha_map(args.alpha_map)
        cleaned = remove_gemini_watermark(arr)

    Image.fromarray(cleaned).save(out)
    orig_kb = os.path.getsize(args.input) / 1024
    clean_kb = os.path.getsize(out) / 1024
    print(f"\nDone: {arr.shape[1]}x{arr.shape[0]}, {orig_kb:.0f}KB → {clean_kb:.0f}KB, → {out}")


if __name__ == "__main__":
    main()
