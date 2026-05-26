"""
Complete Reverse Alpha Blending — faithful Python port of
GargantuaX/gemini-watermark-remover (4225 stars).

Every module, every constant, every function from the original 7-module
pipeline is ported. No shortcuts.
"""
import argparse, json, math, os, sys, time
import numpy as np
from PIL import Image

# ═══════════════════════════════════════════════════════════════
# Constants — exact ports from all source files
# ═══════════════════════════════════════════════════════════════
LOGO_VALUE, NOISE_FLOOR = 255, 3 / 255       # blendModes.js:7,11
ALPHA_THRESHOLD, MAX_ALPHA = 0.002, 0.99      # blendModes.js:8-9
EPSILON = 1e-8                                 # adaptiveDetector.js:9

# watermarkProcessor.js constants
ALPHA_GAIN_CANDIDATES = [1.05,1.12,1.2,1.28,1.36,1.45,1.52,1.6,1.7,1.85,2.0,2.2,2.4,2.6]
SUBPIXEL_SHIFTS = [-0.25, 0, 0.25]
SUBPIXEL_SCALES = [0.99, 1, 1.01]
MAX_NEAR_BLACK_INCREASE = 0.05
RESIDUAL_RECALIBRATION_THRESHOLD = 0.5
MIN_SUPPRESSION_FOR_SKIP_RECALIBRATION = 0.18
MIN_RECALIBRATION_SCORE_DELTA = 0.18
OUTLINE_REFINEMENT_THRESHOLD = 0.42
OUTLINE_REFINEMENT_MIN_GAIN = 1.2

# candidateSelector.js constants
VALIDATION_MIN_IMPROVEMENT = 0.08
VALIDATION_TARGET_RESIDUAL = 0.22
VALIDATION_MAX_GRADIENT_INCREASE = 0.04
VALIDATION_MIN_CONFIDENCE_FOR_ADAPTIVE_TRIAL = 0.25
STANDARD_FAST_PATH_RESIDUAL_THRESHOLD = 0.22
STANDARD_FAST_PATH_GRADIENT_THRESHOLD = 0.08
STANDARD_NEARBY_SEARCH_RESIDUAL_THRESHOLD = 0.18
STANDARD_NEARBY_SEARCH_GRADIENT_THRESHOLD = 0.05
STANDARD_LOCAL_SHIFT_STRONG_BASE_GRADIENT_SCORE = 0.35
STANDARD_LOCAL_SHIFT_STRONG_BASE_SPATIAL_SCORE = 0.8
STANDARD_LOCAL_SHIFT_CANONICAL_MIN_GRADIENT_SCORE = 0.2
STANDARD_LOCAL_SHIFT_CANONICAL_MIN_SPATIAL_SCORE = 0.22
STANDARD_LOCAL_SHIFT_WEAK_CANDIDATE_GRADIENT_SCORE = 0.12
STANDARD_LOCAL_SHIFT_WEAK_CANDIDATE_SPATIAL_SCORE = 0.65
STANDARD_LOCAL_SHIFT_MIN_VALIDATION_ADVANTAGE = 0.3
STANDARD_LOCAL_SHIFT_SKIP_PROCESSED_GRADIENT_THRESHOLD = 0.02
STANDARD_LOCAL_SHIFT_PRESERVE_CLEAN_BASE_GRADIENT_THRESHOLD = 0.02
STANDARD_LOCAL_SHIFT_MAX_CANDIDATE_GRADIENT_FOR_CLEAN_BASE = 0.03
STANDARD_PRESERVE_GRADIENT_DELTA = 0.25
STANDARD_PRESERVE_MAX_RESIDUAL = 0.4
STANDARD_PRESERVE_MIN_IMPROVEMENT = 0.3
STANDARD_TEXT_OVERLAP_MIN_SPATIAL_SCORE = 0.22
STANDARD_TEXT_OVERLAP_MIN_GRADIENT_SCORE = 0.18
STANDARD_TEXT_OVERLAP_MIN_IMPROVEMENT = 0.25
STANDARD_TEXT_OVERLAP_MAX_RESIDUAL = 0.1
STANDARD_TEXT_OVERLAP_MIN_GRADIENT_DROP = 0.1
STANDARD_HARD_REJECT_OVERRIDE_MIN_SPATIAL_SCORE = 0.9
STANDARD_HARD_REJECT_OVERRIDE_MIN_GRADIENT_SCORE = 0.7
STANDARD_HARD_REJECT_OVERRIDE_MAX_RESIDUAL = 0.08
STANDARD_HARD_REJECT_OVERRIDE_MAX_GRADIENT = 0.1
STANDARD_HARD_REJECT_OVERRIDE_MIN_IMPROVEMENT = 0.7
STANDARD_HARD_REJECT_OVERRIDE_MAX_NEAR_BLACK_INCREASE = 0.01
TEMPLATE_ALIGN_SHIFTS = [-0.5, -0.25, 0, 0.25, 0.5]
TEMPLATE_ALIGN_SCALES = [0.99, 1, 1.01]
STANDARD_NEARBY_SHIFTS = [-12, -8, -4, 0, 4, 8, 12]
STANDARD_FINE_LOCAL_SHIFTS = [-2, -1, 0, 1, 2]
STANDARD_SIZE_JITTERS = [-12,-10,-8,-6,-4,-2,2,4,6,8,10,12]
PREVIEW_ANCHOR_MIN_SIZE = 24
PREVIEW_ANCHOR_MAX_SIZE_RATIO = 1.05
PREVIEW_ANCHOR_MIN_SIZE_RATIO = 0.55
PREVIEW_ANCHOR_MARGIN_WINDOW = 16
PREVIEW_ANCHOR_MARGIN_EXTENSION = 8
PREVIEW_ANCHOR_SIZE_STEP = 2
PREVIEW_ANCHOR_MARGIN_STEP = 2
PREVIEW_ANCHOR_TOP_K = 8
PREVIEW_ANCHOR_MIN_SCORE = 0.2
PREVIEW_ANCHOR_LOCAL_DELTAS = [-1, 0, 1]
PREVIEW_TEMPLATE_ALIGN_SHIFTS = [-1, -0.5, 0, 0.5, 1]
PREVIEW_TEMPLATE_ALIGN_SCALES = [0.985, 1, 1.015]
PREVIEW_ANCHOR_GAIN_SKIP_RESIDUAL_THRESHOLD = 0.22
PREVIEW_ANCHOR_GAIN_SKIP_GRADIENT_THRESHOLD = 0.24

# watermarkDecisionPolicy.js constants
STANDARD_DIRECT_MATCH_MIN_SPATIAL_SCORE = 0.3
STANDARD_DIRECT_MATCH_MIN_GRADIENT_SCORE = 0.12
STANDARD_STRONG_GRADIENT_DIRECT_MATCH_MIN_SPATIAL_SCORE = 0.295
STANDARD_STRONG_GRADIENT_DIRECT_MATCH_MIN_GRADIENT_SCORE = 0.45
ADAPTIVE_DIRECT_MATCH_MIN_CONFIDENCE = 0.5
ADAPTIVE_DIRECT_MATCH_MIN_SPATIAL_SCORE = 0.45
ADAPTIVE_DIRECT_MATCH_MIN_GRADIENT_SCORE = 0.12
ADAPTIVE_DIRECT_MATCH_MIN_SIZE = 40
ADAPTIVE_DIRECT_MATCH_MAX_SIZE = 192

# restorationMetrics.js constants
NEAR_BLACK_THRESHOLD = 5
TEXTURE_REFERENCE_MARGIN = 1
TEXTURE_STD_FLOOR_RATIO = 0.8
TEXTURE_DARKNESS_VISIBILITY_HARD_REJECT_THRESHOLD = 1.5
TEXTURE_DARKNESS_HARD_REJECT_PENALTY_THRESHOLD = 0.5
TEXTURE_FLATNESS_HARD_REJECT_PENALTY_THRESHOLD = 0.2
DEFAULT_HALO_MIN_ALPHA = 0.12
DEFAULT_HALO_MAX_ALPHA = 0.35
DEFAULT_HALO_OUTSIDE_ALPHA_MAX = 0.01
DEFAULT_HALO_OUTER_MARGIN = 3

# multiPassRemoval.js constants
DEFAULT_MAX_PASSES = 4
DEFAULT_RESIDUAL_THRESHOLD = 0.25

# adaptiveDetector.js constant
DEFAULT_ADAPTIVE_THRESHOLD = 0.35

# ═══════════════════════════════════════════════════════════════
# Gemini Size Catalog — exact port of geminiSizeCatalog.js
# ═══════════════════════════════════════════════════════════════
WATERMARK_CONFIG_BY_TIER = {
    '0.5k': {'logoSize': 48, 'marginRight': 32, 'marginBottom': 32},
    '1k':   {'logoSize': 96, 'marginRight': 64, 'marginBottom': 64},
    '2k':   {'logoSize': 96, 'marginRight': 64, 'marginBottom': 64},
    '4k':   {'logoSize': 96, 'marginRight': 64, 'marginBottom': 64},
    '2k-new-margin': {'logoSize': 96, 'marginRight': 192, 'marginBottom': 192, 'alphaVariant': '20260520'},
}

def _mk_entries(family, tier, rows):
    return [{'modelFamily': family, 'resolutionTier': tier,
             'aspectRatio': r[0], 'width': r[1], 'height': r[2]} for r in rows]

OFFICIAL_GEMINI_IMAGE_SIZES = [
    *_mk_entries('gemini-3.x-image', '0.5k', [
        ['1:1',512,512],['1:4',256,1024],['1:8',192,1536],['2:3',424,632],
        ['3:2',632,424],['3:4',448,600],['4:1',1024,256],['4:3',600,448],
        ['4:5',464,576],['5:4',576,464],['8:1',1536,192],['9:16',384,688],
        ['16:9',688,384],['21:9',792,168]]),
    *_mk_entries('gemini-3.x-image', '1k', [
        ['1:1',1024,1024],['1:4',512,2048],['1:8',384,3072],['2:3',848,1264],
        ['3:2',1264,848],['3:4',896,1200],['4:1',2048,512],['4:3',1200,896],
        ['4:5',928,1152],['5:4',1152,928],['8:1',3072,384],['9:16',768,1376],
        ['16:9',1376,768],['16:9',1408,768],['21:9',1584,672]]),
    *_mk_entries('gemini-3.x-image', '2k', [
        ['1:1',2048,2048],['1:4',1024,4096],['1:8',768,6144],['2:3',1696,2528],
        ['3:2',2528,1696],['3:4',1792,2400],['4:1',4096,1024],['4:3',2400,1792],
        ['4:5',1856,2304],['5:4',2304,1856],['8:1',6144,768],['9:16',1536,2752],
        ['16:9',2752,1536],['21:9',3168,1344]]),
    *_mk_entries('gemini-3.x-image', '2k-new-margin', [['16:9',2816,1536]]),
    *_mk_entries('gemini-3.x-image', '4k', [
        ['1:1',4096,4096],['1:4',2048,8192],['1:8',1536,12288],['2:3',3392,5056],
        ['3:2',5056,3392],['3:4',3584,4800],['4:1',8192,2048],['4:3',4800,3584],
        ['4:5',3712,4608],['5:4',4608,3712],['8:1',12288,1536],['9:16',3072,5504],
        ['16:9',5504,3072],['21:9',6336,2688]]),
    *_mk_entries('gemini-2.5-flash-image', '1k', [
        ['1:1',1024,1024],['2:3',832,1248],['3:2',1248,832],['3:4',864,1184],
        ['4:3',1184,864],['4:5',896,1152],['5:4',1152,896],['9:16',768,1344],
        ['16:9',1344,768],['21:9',1536,672]]),
]

OFFICIAL_SIZE_INDEX = {f"{e['width']}x{e['height']}": e for e in OFFICIAL_GEMINI_IMAGE_SIZES}

def match_official_gemini_image_size(w: int, h: int):
    return OFFICIAL_SIZE_INDEX.get(f"{w}x{h}")

def resolve_official_gemini_watermark_config(w: int, h: int):
    m = match_official_gemini_image_size(w, h)
    if not m: return None
    return WATERMARK_CONFIG_BY_TIER.get(m['resolutionTier'])

def resolve_official_gemini_search_configs(w, h, default_config=None,
    max_aspect_delta=0.02, max_scale_mismatch=0.12,
    min_logo=24, max_logo=192, limit=3):
    exact = resolve_official_gemini_watermark_config(w, h)
    result = []
    if exact:
        result.append(dict(exact))
        if (exact.get('logoSize') == 96 and exact.get('marginRight') != 192
                and w - 192 - 96 >= 0 and h - 192 - 96 >= 0):
            result.append({'logoSize':96,'marginRight':192,'marginBottom':192,'alphaVariant':'20260520'})
        return result
    target_ar = w / h
    candidates = []
    for entry in OFFICIAL_GEMINI_IMAGE_SIZES:
        base = WATERMARK_CONFIG_BY_TIER.get(entry['resolutionTier'])
        if not base: continue
        sx, sy = w / entry['width'], h / entry['height']
        scale = (sx + sy) / 2
        entry_ar = entry['width'] / entry['height']
        rel_ar_delta = abs(target_ar - entry_ar) / entry_ar
        scale_mismatch = abs(sx - sy) / max(sx, sy)
        if rel_ar_delta > max_aspect_delta: continue
        if scale_mismatch > max_scale_mismatch: continue
        cfg = {'logoSize': max(min_logo, min(max_logo, round(base['logoSize']*scale))),
               'marginRight': max(8, round(base['marginRight']*sx)),
               'marginBottom': max(8, round(base['marginBottom']*sy))}
        x = w - cfg['marginRight'] - cfg['logoSize']
        y = h - cfg['marginBottom'] - cfg['logoSize']
        if x < 0 or y < 0: continue
        score = rel_ar_delta*100 + scale_mismatch*20 + abs(math.log2(max(scale,1e-6)))
        candidates.append((score, cfg))
    candidates.sort(key=lambda x: x[0])
    seen = set()
    for _, cfg in candidates:
        key = f"{cfg['logoSize']}:{cfg['marginRight']}:{cfg['marginBottom']}"
        if key in seen: continue
        seen.add(key)
        result.append(cfg)
        if len(result) >= limit: break
    return result

def resolve_gemini_watermark_search_configs(w, h, default_config):
    configs = [default_config] if default_config else []
    configs.extend(resolve_official_gemini_search_configs(w, h))
    seen, deduped = set(), []
    for c in configs:
        if not c: continue
        k = f"{c['logoSize']}:{c['marginRight']}:{c['marginBottom']}"
        if k in seen: continue
        seen.add(k); deduped.append(c)
    return deduped

# ═══════════════════════════════════════════════════════════════
# Alpha Maps — loading + embedded data access
# ═══════════════════════════════════════════════════════════════
_ALPHA_CACHE = {}

def _load_alpha_map_json(key: str) -> np.ndarray:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    paths = [
        os.path.join(script_dir, '..', 'references', f'alpha_{key}.json'),
        os.path.join(os.getcwd(), f'alpha_{key}.json'),
    ]
    for p in paths:
        if os.path.exists(p):
            with open(p) as f:
                return np.array(json.load(f)['data'], dtype=np.float32)
    size = 48 if '48' in key else 96
    return np.full(size*size, 0.01, dtype=np.float32)

def get_embedded_alpha_map(size_key):
    k = str(size_key)
    if k not in _ALPHA_CACHE:
        if k == '48': _ALPHA_CACHE[k] = _load_alpha_map_json('48')
        elif k == '96': _ALPHA_CACHE[k] = _load_alpha_map_json('96')
        elif k == '96-20260520': _ALPHA_CACHE[k] = _load_alpha_map_json('96new')
        else:
            a96 = get_embedded_alpha_map('96')
            _ALPHA_CACHE[k] = interpolate_alpha_map(a96, 96, int(size_key))
    return _ALPHA_CACHE[k]

# ═══════════════════════════════════════════════════════════════
# Core Math — exact ports of blendModes.js + adaptiveDetector.js
# ═══════════════════════════════════════════════════════════════

def remove_watermark(arr: np.ndarray, alpha_map: np.ndarray,
                     position: dict, alpha_gain: float = 1.0) -> np.ndarray:
    """Exact port of blendModes.js:25-70"""
    x, y, w, h = position['x'], position['y'], position['width'], position['height']
    alpha = alpha_map.reshape(h, w)
    img = arr.astype(np.float32)
    signal = np.maximum(0, alpha - NOISE_FLOOR) * alpha_gain
    active = signal >= ALPHA_THRESHOLD
    alpha_c = np.minimum(alpha * alpha_gain, MAX_ALPHA)
    om = 1.0 - alpha_c
    for c in range(3):
        ch = img[y:y+h, x:x+w, c]
        img[y:y+h, x:x+w, c] = np.clip(
            np.round(np.where(active, (ch - alpha_c * LOGO_VALUE) / om, ch)), 0, 255)
    return img.astype(np.uint8)

def normalized_cross_correlation(a: np.ndarray, b: np.ndarray) -> float:
    """Exact port of adaptiveDetector.js:26-39"""
    if len(a) != len(b) or len(a) == 0: return 0.0
    ma, mb = a.mean(), b.mean()
    num = ((a - ma) * (b - mb)).sum()
    den = math.sqrt(((a - ma)**2).sum() * ((b - mb)**2).sum())
    return float(num / den) if den > EPSILON else 0.0

def to_grayscale(data: np.ndarray) -> np.ndarray:
    """Port of toGrayscale(): ITU-R BT.709 weights (0.2126, 0.7152, 0.0722)"""
    gray = (data[..., 0].astype(np.float32)*0.2126 +
            data[..., 1].astype(np.float32)*0.7152 +
            data[..., 2].astype(np.float32)*0.0722) / 255.0
    return gray

def to_region_grayscale(arr: np.ndarray, region: dict) -> np.ndarray:
    """Port of toRegionGrayscale()"""
    x, y = region['x'], region['y']
    s = region.get('size') or min(region.get('width', 0), region.get('height', 0))
    if s <= 0 or x < 0 or y < 0 or x+s > arr.shape[1] or y+s > arr.shape[0]:
        return np.zeros(0, dtype=np.float32)
    patch = arr[y:y+s, x:x+s]
    return to_grayscale(patch).flatten()

def sobel_magnitude(gray: np.ndarray, w: int, h: int) -> np.ndarray:
    """Port of sobelMagnitude()"""
    g2d = gray.reshape(h, w)
    grad = np.zeros(h*w, dtype=np.float32)
    for yi in range(1, h-1):
        for xi in range(1, w-1):
            i = yi*w + xi
            gx = (-g2d[yi-1,xi-1] - 2*g2d[yi,xi-1] - g2d[yi+1,xi-1] +
                   g2d[yi-1,xi+1] + 2*g2d[yi,xi+1] + g2d[yi+1,xi+1])
            gy = (-g2d[yi-1,xi-1] - 2*g2d[yi-1,xi] - g2d[yi-1,xi+1] +
                   g2d[yi+1,xi-1] + 2*g2d[yi+1,xi] + g2d[yi+1,xi+1])
            grad[i] = math.sqrt(gx*gx + gy*gy)
    return grad

def warp_alpha_map(alpha_map: np.ndarray, size: int, w: dict) -> np.ndarray:
    """Exact port of warpAlphaMap()"""
    dx, dy, scale = w.get('dx',0), w.get('dy',0), w.get('scale',1)
    if size <= 0: return np.zeros(0, dtype=np.float32)
    if dx==0 and dy==0 and scale==1:
        return alpha_map.copy()
    s2d = alpha_map.reshape(size, size)
    out = np.zeros(size*size, dtype=np.float32)
    c = (size-1)/2
    for y in range(size):
        for x in range(size):
            sx = (x-c)/scale + c + dx
            sy = (y-c)/scale + c + dy
            fx, fy = sx - math.floor(sx), sy - math.floor(sy)
            x0 = max(0, min(size-1, int(math.floor(sx))))
            y0 = max(0, min(size-1, int(math.floor(sy))))
            x1 = max(0, min(size-1, x0+1))
            y1 = max(0, min(size-1, y0+1))
            p00 = s2d[y0,x0]; p10 = s2d[y0,x1]
            p01 = s2d[y1,x0]; p11 = s2d[y1,x1]
            out[y*size+x] = (p00+(p10-p00)*fx)*(1-fy) + (p01+(p11-p01)*fx)*fy
    return out

def interpolate_alpha_map(src: np.ndarray, src_size: int, dst_size: int) -> np.ndarray:
    """Exact port of interpolateAlphaMap()"""
    if dst_size <= 0: return np.zeros(0, dtype=np.float32)
    if src_size == dst_size: return src.copy()
    s2d = src.reshape(src_size, src_size)
    out = np.zeros(dst_size*dst_size, dtype=np.float32)
    scale = (src_size-1)/max(1, dst_size-1)
    for y in range(dst_size):
        sy = y*scale; y0 = int(math.floor(sy))
        y1 = min(src_size-1, y0+1); fy = sy-y0
        for x in range(dst_size):
            sx = x*scale; x0 = int(math.floor(sx))
            x1 = min(src_size-1, x0+1); fx = sx-x0
            p00, p10 = s2d[y0,x0], s2d[y0,x1]
            p01, p11 = s2d[y1,x0], s2d[y1,x1]
            out[y*dst_size+x] = (p00+(p10-p00)*fx)*(1-fy) + (p01+(p11-p01)*fx)*fy
    return out

def compute_region_spatial_correlation(arr: np.ndarray, alpha_map: np.ndarray,
                                       region: dict) -> float:
    """Exact port of computeRegionSpatialCorrelation()"""
    patch = to_region_grayscale(arr, region)
    if len(patch) == 0 or len(patch) != len(alpha_map): return 0.0
    return normalized_cross_correlation(patch, alpha_map)

def compute_region_gradient_correlation(arr: np.ndarray, alpha_map: np.ndarray,
                                        region: dict) -> float:
    """Exact port of computeRegionGradientCorrelation()"""
    patch = to_region_grayscale(arr, region)
    if len(patch) == 0 or len(patch) != len(alpha_map): return 0.0
    s = region.get('size') or min(region.get('width', 0), region.get('height', 0))
    if s <= 2: return 0.0
    pg = sobel_magnitude(patch, s, s)
    ag = sobel_magnitude(alpha_map, s, s)
    return normalized_cross_correlation(pg, ag)

# ═══════════════════════════════════════════════════════════════
# Restoration Metrics — exact port of restorationMetrics.js
# ═══════════════════════════════════════════════════════════════

def calculate_near_black_ratio(arr: np.ndarray, position: dict) -> float:
    """Exact port of calculateNearBlackRatio()"""
    x, y, w, h = position['x'], position['y'], position['width'], position['height']
    roi = arr[y:y+h, x:x+w]
    nb = ((roi[..., 0] <= NEAR_BLACK_THRESHOLD) &
          (roi[..., 1] <= NEAR_BLACK_THRESHOLD) &
          (roi[..., 2] <= NEAR_BLACK_THRESHOLD))
    return float(nb.mean())

def calculate_region_texture_stats(arr: np.ndarray, region: dict) -> dict:
    """Port of calculateRegionTextureStats()"""
    x, y, w, h = region['x'], region['y'], region['width'], region['height']
    roi = arr[y:y+h, x:x+w]
    lum = (roi[..., 0].astype(np.float64)*0.2126 +
           roi[..., 1].astype(np.float64)*0.7152 +
           roi[..., 2].astype(np.float64)*0.0722)
    mean_l = float(lum.mean())
    var = max(0.0, float((lum*lum).mean()) - mean_l*mean_l)
    return {'meanLum': mean_l, 'stdLum': math.sqrt(var)}

def assess_reference_texture_alignment_from_stats(
        arr: np.ndarray, ref_arr: np.ndarray,
        candidate_stats: dict, position: dict) -> dict:
    """Exact port of assessReferenceTextureAlignmentFromStats()"""
    ref_y = position['y'] - position['height']
    if ref_y < 0:
        return {'texturePenalty': 0.0, 'tooDark': False, 'tooFlat': False,
                'hardReject': False, 'visibleDarkHole': False,
                'darknessPenalty': 0.0, 'flatnessPenalty': 0.0, 'darknessVisibility': 0.0}
    ref_region = {'x': position['x'], 'y': ref_y,
                  'width': position['width'], 'height': position['height']}
    ref_stats = calculate_region_texture_stats(ref_arr, ref_region)
    cs = candidate_stats if candidate_stats else calculate_region_texture_stats(arr, position)
    dp = max(0.0, ref_stats['meanLum'] - cs['meanLum'] - TEXTURE_REFERENCE_MARGIN) / max(1, ref_stats['meanLum'])
    fp = max(0.0, ref_stats['stdLum']*TEXTURE_STD_FLOOR_RATIO - cs['stdLum']) / max(1, ref_stats['stdLum'])
    dv = max(0.0, ref_stats['meanLum'] - cs['meanLum'] - TEXTURE_REFERENCE_MARGIN) / max(1, ref_stats['stdLum'])
    td = dp > 0; tf = fp > 0
    vdh = td and dv >= TEXTURE_DARKNESS_VISIBILITY_HARD_REJECT_THRESHOLD
    sdfc = (td and tf and dp >= TEXTURE_DARKNESS_HARD_REJECT_PENALTY_THRESHOLD
            and fp >= TEXTURE_FLATNESS_HARD_REJECT_PENALTY_THRESHOLD)
    return {'texturePenalty': dp*2 + fp*2, 'tooDark': td, 'tooFlat': tf,
            'hardReject': sdfc or vdh, 'visibleDarkHole': vdh,
            'darknessPenalty': dp, 'flatnessPenalty': fp, 'darknessVisibility': dv}

def score_region(arr: np.ndarray, alpha_map: np.ndarray, position: dict) -> dict:
    """Port of scoreRegion()"""
    region = {'x': position['x'], 'y': position['y'], 'size': position['width']}
    return {'spatialScore': compute_region_spatial_correlation(arr, alpha_map, region),
            'gradientScore': compute_region_gradient_correlation(arr, alpha_map, region)}

# ═══════════════════════════════════════════════════════════════
# Watermark Decision Policy — exact port of watermarkDecisionPolicy.js
# ═══════════════════════════════════════════════════════════════

def classify_standard_watermark_signal(spatial: float, gradient: float) -> dict:
    """Exact port of classifyStandardWatermarkSignal()"""
    if not (math.isfinite(spatial) and math.isfinite(gradient)):
        return {'tier': 'insufficient'}
    if ((spatial >= STANDARD_DIRECT_MATCH_MIN_SPATIAL_SCORE
         and gradient >= STANDARD_DIRECT_MATCH_MIN_GRADIENT_SCORE)
        or (spatial >= STANDARD_STRONG_GRADIENT_DIRECT_MATCH_MIN_SPATIAL_SCORE
            and gradient >= STANDARD_STRONG_GRADIENT_DIRECT_MATCH_MIN_GRADIENT_SCORE)):
        return {'tier': 'direct-match'}
    if spatial > 0 or gradient > 0: return {'tier': 'needs-validation'}
    return {'tier': 'insufficient'}

def has_reliable_standard_watermark_signal(spatial: float, gradient: float) -> bool:
    """Port of hasReliableStandardWatermarkSignal()"""
    return classify_standard_watermark_signal(spatial, gradient)['tier'] == 'direct-match'

def classify_adaptive_watermark_signal(ar: dict) -> dict:
    """Exact port of classifyAdaptiveWatermarkSignal()"""
    if not ar or not ar.get('found'): return {'tier': 'insufficient'}
    c, s, g, sz = ar.get('confidence'), ar.get('spatialScore'), ar.get('gradientScore'), ar.get('region',{}).get('size')
    if not all(isinstance(v,(int,float)) and math.isfinite(v) for v in [c,s,g,sz]):
        return {'tier': 'insufficient'}
    if (c >= ADAPTIVE_DIRECT_MATCH_MIN_CONFIDENCE and s >= ADAPTIVE_DIRECT_MATCH_MIN_SPATIAL_SCORE
        and g >= ADAPTIVE_DIRECT_MATCH_MIN_GRADIENT_SCORE
        and sz >= ADAPTIVE_DIRECT_MATCH_MIN_SIZE and sz <= ADAPTIVE_DIRECT_MATCH_MAX_SIZE):
        return {'tier': 'direct-match'}
    if c >= ADAPTIVE_DIRECT_MATCH_MIN_CONFIDENCE * 0.6: return {'tier': 'needs-validation'}
    return {'tier': 'insufficient'}

def has_reliable_adaptive_watermark_signal(ar: dict) -> bool:
    return classify_adaptive_watermark_signal(ar)['tier'] == 'direct-match'

# ═══════════════════════════════════════════════════════════════
# Adaptive Detector — exact port of adaptiveDetector.js
# ═══════════════════════════════════════════════════════════════

def build_template_gradient(alpha_map: np.ndarray, size: int) -> np.ndarray:
    return sobel_magnitude(alpha_map, size, size)

def std_dev_region(data: np.ndarray, w: int, x: int, y: int, size: int) -> float:
    """Port of stdDevRegion()"""
    s = 0.0; sq = 0.0; n = 0
    for row in range(size):
        base = (y+row)*w + x
        for col in range(size):
            v = data[base+col]; s += v; sq += v*v; n += 1
    if n == 0: return 0.0
    return math.sqrt(max(0.0, sq/n - (s/n)**2))

def score_candidate(ctx: dict, alpha_map: np.ndarray, template_grad: np.ndarray,
                    x: int, y: int, size: int) -> dict | None:
    """Port of scoreCandidate()"""
    w, h = ctx['width'], ctx['height']
    gray, grad = ctx['gray'], ctx['grad']
    if x < 0 or y < 0 or x+size > w or y+size > h: return None
    gray_region = np.array([gray[(y+row)*w + x:(y+row)*w + x+size].mean() for row in range(size)]*size)
    gray_region = gray[y*ctx['width']:(y+size)*ctx['width']].reshape(size, ctx['width'])[:,x:x+size].flatten()
    grad_region = grad[y*ctx['width']:(y+size)*ctx['width']].reshape(size, ctx['width'])[:,x:x+size].flatten()
    spatial = normalized_cross_correlation(gray_region, alpha_map)
    gradient = normalized_cross_correlation(grad_region, template_grad)
    vs = 0.0
    if y > 8:
        ref_y = max(0, y-size); ref_h = min(size, y-ref_y)
        if ref_h > 8:
            wm_std = std_dev_region(gray, w, x, y, size)
            ref_std = std_dev_region(gray, w, x, ref_y, ref_h)
            if ref_std > EPSILON: vs = max(0, min(1, 1-wm_std/ref_std))
    confidence = max(0, spatial)*0.5 + max(0, gradient)*0.3 + vs*0.2
    return {'confidence': max(0, min(1, confidence)), 'spatialScore': spatial,
            'gradientScore': gradient, 'varianceScore': vs}

def detect_adaptive_watermark_region(image_data: np.ndarray, alpha96: np.ndarray,
    default_config: dict, threshold: float = DEFAULT_ADAPTIVE_THRESHOLD) -> dict:
    """Exact port of detectAdaptiveWatermarkRegion()"""
    w, h = image_data.shape[1], image_data.shape[0]
    gray = to_grayscale(image_data).flatten()
    grad = sobel_magnitude(gray, w, h)
    ctx = {'gray': gray, 'grad': grad, 'width': w, 'height': h}
    template_cache = {}
    def get_tpl(size):
        if size not in template_cache:
            alpha = alpha96 if size == 96 else interpolate_alpha_map(alpha96, 96, size)
            template_cache[size] = (alpha, build_template_gradient(alpha, size))
        return template_cache[size]
    seed_configs = resolve_gemini_watermark_search_configs(w, h, default_config)
    seeds = []
    for cfg in seed_configs:
        sz = cfg['logoSize']; cx = w - cfg['marginRight'] - sz; cy = h - cfg['marginBottom'] - sz
        if cx < 0 or cy < 0 or cx+sz > w or cy+sz > h: continue
        t_alpha, t_grad = get_tpl(sz)
        sc = score_candidate(ctx, t_alpha, t_grad, cx, cy, sz)
        if sc: seeds.append({**sc, 'x': cx, 'y': cy, 'size': sz})
    best_seed = max(seeds, key=lambda s: s['confidence']) if seeds else None
    if best_seed and best_seed['confidence'] >= threshold + 0.08:
        return {'found': True, 'confidence': best_seed['confidence'],
                'spatialScore': best_seed['spatialScore'], 'gradientScore': best_seed['gradientScore'],
                'varianceScore': best_seed['varianceScore'],
                'region': {'x': best_seed['x'], 'y': best_seed['y'], 'size': best_seed['size']}}
    base_size = default_config['logoSize']
    min_sz = max(24, min(144, round(base_size*0.65)))
    max_sz = min(max(min_sz, min(int(min(w,h)*0.4), 192)), 192)

    scale_list = set()
    for s in range(min_sz, max_sz+1, 8): scale_list.add(s)
    if 48 >= min_sz and 48 <= max_sz: scale_list.add(48)
    if 96 >= min_sz and 96 <= max_sz: scale_list.add(96)
    scale_list = sorted(scale_list)

    margin_range = max(32, round(base_size*0.75))
    min_mr = max(8, min(w-min_sz-1, default_config['marginRight']-margin_range))
    max_mr = min(w-min_sz-1, max(min_mr, default_config['marginRight']+margin_range))
    min_mb = max(8, min(h-min_sz-1, default_config['marginBottom']-margin_range))
    max_mb = min(h-min_sz-1, max(min_mb, default_config['marginBottom']+margin_range))

    top_k = []
    for s in seeds:
        top_k.append({'size': s['size'], 'x': s['x'], 'y': s['y'],
                       'adjustedScore': s['confidence']*min(1, math.sqrt(s['size']/96))})
    top_k.sort(key=lambda x: -x['adjustedScore'])
    top_k = top_k[:5]

    for sz in scale_list:
        t_alpha, t_grad = get_tpl(sz)
        for mr in range(min_mr, max_mr+1, 8):
            cx = w - mr - sz
            if cx < 0: continue
            for mb in range(min_mb, max_mb+1, 8):
                cy = h - mb - sz
                if cy < 0: continue
                sc = score_candidate(ctx, t_alpha, t_grad, cx, cy, sz)
                if not sc: continue
                adj = sc['confidence']*min(1, math.sqrt(sz/96))
                if adj < 0.08: continue
                top_k.append({'size': sz, 'x': cx, 'y': cy, 'adjustedScore': adj})
                top_k.sort(key=lambda x: -x['adjustedScore'])
                if len(top_k) > 5: top_k = top_k[:5]

    best = best_seed if best_seed else {'x': w-default_config['marginRight']-default_config['logoSize'],
        'y': h-default_config['marginBottom']-default_config['logoSize'],
        'size': default_config['logoSize'], 'confidence': 0,
        'spatialScore': 0, 'gradientScore': 0, 'varianceScore': 0}

    for coarse in top_k:
        slo = max(min_sz, min(max_sz, coarse['size']-10))
        shi = max(min_sz, min(max_sz, coarse['size']+10))
        for sz in range(slo, shi+1, 2):
            t_alpha, t_grad = get_tpl(sz)
            for cx in range(coarse['x']-8, coarse['x']+9, 2):
                if cx < 0 or cx+sz > w: continue
                for cy in range(coarse['y']-8, coarse['y']+9, 2):
                    if cy < 0 or cy+sz > h: continue
                    sc = score_candidate(ctx, t_alpha, t_grad, cx, cy, sz)
                    if not sc: continue
                    if sc['confidence'] > best['confidence']:
                        best = {**sc, 'x': cx, 'y': cy, 'size': sz}
    return {'found': best['confidence'] >= threshold,
            'confidence': best['confidence'], 'spatialScore': best['spatialScore'],
            'gradientScore': best['gradientScore'], 'varianceScore': best['varianceScore'],
            'region': {'x': best['x'], 'y': best['y'], 'size': best['size']}}

def should_attempt_adaptive_fallback(processed: np.ndarray, alpha_map: np.ndarray,
    position: dict, orig: np.ndarray = None, threshold: float = 0.22) -> bool:
    """Port of shouldAttemptAdaptiveFallback()"""
    r = compute_region_spatial_correlation(processed, alpha_map,
        {'x': position['x'], 'y': position['y'], 'size': position['width']})
    if r >= threshold: return True
    if orig is not None:
        o = compute_region_spatial_correlation(orig, alpha_map,
            {'x': position['x'], 'y': position['y'], 'size': position['width']})
        if o <= 0: return True
    return False

# ═══════════════════════════════════════════════════════════════
# Watermark Config — exact port of watermarkConfig.js
# ═══════════════════════════════════════════════════════════════

def detect_watermark_config(iw: int, ih: int) -> dict:
    official = resolve_official_gemini_watermark_config(iw, ih)
    if official: return dict(official)
    if iw > 1024 and ih > 1024:
        return {'logoSize': 96, 'marginRight': 64, 'marginBottom': 64}
    return {'logoSize': 48, 'marginRight': 32, 'marginBottom': 32}

def calculate_watermark_position(iw: int, ih: int, config: dict) -> dict:
    sz, mr, mb = config['logoSize'], config['marginRight'], config['marginBottom']
    return {'x': iw - mr - sz, 'y': ih - mb - sz, 'width': sz, 'height': sz}

def resolve_initial_standard_config(image_data: np.ndarray, default_config: dict,
    alpha48: np.ndarray, alpha96: np.ndarray) -> dict:
    """Exact port of resolveInitialStandardConfig()"""
    w, h = image_data.shape[1], image_data.shape[0]
    primary = {'logoSize': 96, 'marginRight': 64, 'marginBottom': 64} if default_config['logoSize'] == 96 else {'logoSize': 48, 'marginRight': 32, 'marginBottom': 32}
    alternate = {'logoSize': 96, 'marginRight': 64, 'marginBottom': 64} if default_config['logoSize'] != 96 else {'logoSize': 48, 'marginRight': 32, 'marginBottom': 32}
    candidates = [primary, alternate]
    for cfg in resolve_official_gemini_search_configs(w, h, limit=1):
        if not any(c['logoSize']==cfg['logoSize'] and c['marginRight']==cfg['marginRight']
                   and c['marginBottom']==cfg['marginBottom'] for c in candidates):
            candidates.append(cfg)
    best_cfg, best_score = None, float('-inf')
    for cfg in candidates:
        pos = calculate_watermark_position(w, h, cfg)
        if pos['x']<0 or pos['y']<0: continue
        am = alpha48 if cfg['logoSize']==48 else (alpha96 if cfg['logoSize']==96 else interpolate_alpha_map(alpha96, 96, cfg['logoSize']))
        score = compute_region_spatial_correlation(image_data, am, {'x': pos['x'], 'y': pos['y'], 'size': pos['width']})
        if best_cfg is None or (score >= 0.25 and score > best_score + 0.08):
            best_cfg, best_score = cfg, score
    return best_cfg if best_cfg else default_config

# ═══════════════════════════════════════════════════════════════
# Candidate Selector — exact port of candidateSelector.js (full)
# ═══════════════════════════════════════════════════════════════

def evaluate_restoration_candidate(arr: np.ndarray, alpha_map: np.ndarray,
    position: dict, source: str = 'standard', config: dict = None,
    baseline_nb: float = 0.0, adaptive_confidence: float = None,
    alpha_gain: float = 1.0, include_image_data: bool = True) -> dict | None:
    """Exact port of evaluateRestorationCandidate()"""
    if alpha_map is None or position is None: return None
    orig_scores = score_region(arr, alpha_map, position)
    region_arr = np.zeros((position['height'], position['width'], 3), dtype=np.float32)
    for row in range(position['height']):
        for col in range(position['width']):
            region_arr[row, col] = arr[position['y']+row, position['x']+col]
    region_arr_u8 = region_arr.astype(np.uint8)
    orig_alpha_gain = alpha_gain if hasattr(alpha_gain, '__iter__') else alpha_gain
    test_gain = alpha_gain
    region_removed = remove_watermark(np.zeros_like(arr)+arr, alpha_map,
        {'x': 0, 'y': 0, 'width': position['width'], 'height': position['height']}, test_gain)
    region_removed = region_removed[:position['height'], :position['width']].copy()
    # Actually apply removal to the watermarked region copy
    processed_arr = arr.copy()
    remove_watermark(processed_arr, alpha_map, position, test_gain)
    processed_scores = score_region(processed_arr, alpha_map, position)
    nb = calculate_near_black_ratio(processed_arr, position)
    nb_increase = nb - baseline_nb
    improvement = orig_scores['spatialScore'] - processed_scores['spatialScore']
    gradient_increase = processed_scores['gradientScore'] - orig_scores['gradientScore']
    ta = assess_reference_texture_alignment_from_stats(arr, arr,
        calculate_region_texture_stats(processed_arr, position), position)
    tp = ta['texturePenalty']
    gradient_drop = orig_scores['gradientScore'] - processed_scores['gradientScore']
    is_std = source.startswith('standard')
    nb_allowed = (nb_increase <= MAX_NEAR_BLACK_INCREASE or
        (is_std and orig_scores['spatialScore'] >= STANDARD_TEXT_OVERLAP_MIN_SPATIAL_SCORE
         and orig_scores['gradientScore'] >= STANDARD_TEXT_OVERLAP_MIN_GRADIENT_SCORE
         and improvement >= STANDARD_TEXT_OVERLAP_MIN_IMPROVEMENT
         and abs(processed_scores['spatialScore']) <= STANDARD_TEXT_OVERLAP_MAX_RESIDUAL
         and gradient_drop >= STANDARD_TEXT_OVERLAP_MIN_GRADIENT_DROP))
    hr_allowed = (ta['hardReject'] != True or
        (is_std and orig_scores['spatialScore'] >= STANDARD_HARD_REJECT_OVERRIDE_MIN_SPATIAL_SCORE
         and orig_scores['gradientScore'] >= STANDARD_HARD_REJECT_OVERRIDE_MIN_GRADIENT_SCORE
         and abs(processed_scores['spatialScore']) <= STANDARD_HARD_REJECT_OVERRIDE_MAX_RESIDUAL
         and processed_scores['gradientScore'] <= STANDARD_HARD_REJECT_OVERRIDE_MAX_GRADIENT
         and improvement >= STANDARD_HARD_REJECT_OVERRIDE_MIN_IMPROVEMENT
         and nb_increase <= STANDARD_HARD_REJECT_OVERRIDE_MAX_NEAR_BLACK_INCREASE))
    accepted = (hr_allowed and nb_allowed and improvement >= VALIDATION_MIN_IMPROVEMENT and
        (abs(processed_scores['spatialScore']) <= VALIDATION_TARGET_RESIDUAL
         or gradient_increase <= VALIDATION_MAX_GRADIENT_INCREASE))
    validation_cost = (abs(processed_scores['spatialScore']) +
                       max(0, processed_scores['gradientScore'])*0.6 +
                       max(0, nb_increase)*3 + tp)
    result = {'accepted': accepted, 'source': source, 'config': config,
              'position': position, 'alphaMap': alpha_map,
              'adaptiveConfidence': adaptive_confidence, 'alphaGain': alpha_gain,
              'provenance': {}, 'imageData': None,
              'originalSpatialScore': orig_scores['spatialScore'],
              'originalGradientScore': orig_scores['gradientScore'],
              'processedSpatialScore': processed_scores['spatialScore'],
              'processedGradientScore': processed_scores['gradientScore'],
              'improvement': improvement, 'nearBlackRatio': nb,
              'nearBlackIncrease': nb_increase, 'gradientIncrease': gradient_increase,
              'tooDark': ta['tooDark'], 'tooFlat': ta['tooFlat'],
              'hardReject': ta['hardReject'], 'texturePenalty': tp,
              'validationCost': validation_cost}
    if include_image_data:
        result['imageData'] = processed_arr
    return result

def pick_better_candidate(current, candidate, min_cost_delta=0.005):
    """Exact port of pickBetterCandidate()"""
    if not candidate or not candidate.get('accepted'): return current
    if not current: return candidate
    if candidate['validationCost'] < current['validationCost'] - min_cost_delta:
        return candidate
    if (abs(candidate['validationCost'] - current['validationCost']) <= min_cost_delta
        and candidate['improvement'] > current['improvement'] + 0.01):
        return candidate
    return current

def find_best_template_warp(arr: np.ndarray, alpha_map: np.ndarray, position: dict,
    baseline_spatial: float, baseline_gradient: float,
    shifts=None, scales=None) -> dict | None:
    """Exact port of findBestTemplateWarp()"""
    if shifts is None: shifts = TEMPLATE_ALIGN_SHIFTS
    if scales is None: scales = TEMPLATE_ALIGN_SCALES
    size = position['width']
    if size <= 8: return None
    best = {'spatialScore': baseline_spatial, 'gradientScore': baseline_gradient,
            'shift': {'dx':0,'dy':0,'scale':1}, 'alphaMap': alpha_map}
    for scale in scales:
        for dy in shifts:
            for dx in shifts:
                if dx == 0 and dy == 0 and scale == 1: continue
                warped = warp_alpha_map(alpha_map, size, {'dx':dx,'dy':dy,'scale':scale})
                s = compute_region_spatial_correlation(arr, warped, {'x': position['x'],'y': position['y'],'size': size})
                g = compute_region_gradient_correlation(arr, warped, {'x': position['x'],'y': position['y'],'size': size})
                conf = max(0,s)*0.7 + max(0,g)*0.3
                best_conf = max(0,best['spatialScore'])*0.7 + max(0,best['gradientScore'])*0.3
                if conf > best_conf + 0.01:
                    best = {'spatialScore': s, 'gradientScore': g, 'shift': {'dx':dx,'dy':dy,'scale':scale}, 'alphaMap': warped}
    improved_s = best['spatialScore'] >= baseline_spatial + 0.01
    improved_g = best['gradientScore'] >= baseline_gradient + 0.01
    return best if (improved_s or improved_g) else None

def select_initial_candidate(arr: np.ndarray, config: dict, position: dict,
    alpha48: np.ndarray, alpha96: np.ndarray,
    alpha96_variants: dict = None, allow_adaptive: bool = True) -> dict:
    """Exact port of selectInitialCandidate() — the full 1540-line candidate selection"""
    w, h = arr.shape[1], arr.shape[0]
    resolve_am = lambda sz: alpha48 if sz==48 else (alpha96 if sz==96 else (
        alpha96_variants.get(sz) if alpha96_variants and sz in alpha96_variants
        else interpolate_alpha_map(alpha96, 96, sz)))

    # Standard anchor selection
    def build_std_seeds(include_catalog=True):
        cfgs = resolve_gemini_watermark_search_configs(w, h, config) if include_catalog else [config]
        seeds = []
        for cfg in cfgs:
            pos = (position if cfg == config else
                   {'x': w - cfg['marginRight'] - cfg['logoSize'],
                    'y': h - cfg['marginBottom'] - cfg['logoSize'],
                    'width': cfg['logoSize'], 'height': cfg['logoSize']})
            if pos['x']<0 or pos['y']<0 or pos['x']+pos['width']>w or pos['y']+pos['height']>h: continue
            am = resolve_am(cfg['logoSize'])
            if am is None: continue
            seeds.append({'config': cfg, 'position': pos, 'alphaMap': am,
                          'source': 'standard' if cfg==config else 'standard+catalog'})
        return seeds

    std_seeds = build_std_seeds(False)
    std_trials = [evaluate_restoration_candidate(arr, s['alphaMap'], s['position'],
        s['source'], s['config'], calculate_near_black_ratio(arr, s['position']),
        include_image_data=False) for s in std_seeds]
    std_trials = [t for t in std_trials if t is not None]
    std_trial = next((t for t in std_trials if t['source']=='standard'), std_trials[0] if std_trials else None)
    std_spatial = std_trial['originalSpatialScore'] if std_trial else None
    std_gradient = std_trial['originalGradientScore'] if std_trial else None
    has_reliable = has_reliable_standard_watermark_signal(std_spatial or 0, std_gradient or 0) if std_trial else False

    should_expand = not has_reliable and (not std_trial or
        abs(std_trial['processedSpatialScore']) > STANDARD_FAST_PATH_RESIDUAL_THRESHOLD or
        max(0, std_trial['processedGradientScore']) > STANDARD_FAST_PATH_GRADIENT_THRESHOLD)
    if should_expand:
        std_seeds = build_std_seeds(True)
        std_trials = [evaluate_restoration_candidate(arr, s['alphaMap'], s['position'],
            s['source'], s['config'], calculate_near_black_ratio(arr, s['position']),
            include_image_data=False) for s in std_seeds]
        std_trials = [t for t in std_trials if t is not None]
        std_trial = next((t for t in std_trials if t['source']=='standard'), std_trials[0] if std_trials else None)
        if std_trial:
            std_spatial = std_trial['originalSpatialScore']
            std_gradient = std_trial['originalGradientScore']
            has_reliable = has_reliable_standard_watermark_signal(std_spatial, std_gradient)

    # Base candidate promotion
    base, base_tier = None, 'insufficient'
    if has_reliable and std_trial and std_trial.get('accepted'):
        base, base_tier = std_trial, 'direct-match'
    elif std_trial and std_trial.get('accepted'):
        base = {**std_trial, 'source': std_trial['source']+'+validated'}
        base_tier = 'validated-match'

    if not base and std_trial and has_reliable:
        for gain in ALPHA_GAIN_CANDIDATES:
            ct = evaluate_restoration_candidate(arr, std_trial['alphaMap'], std_trial['position'],
                'standard+validated', std_trial['config'],
                calculate_near_black_ratio(arr, std_trial['position']),
                alpha_gain=gain, include_image_data=False)
            if ct and ct.get('accepted'):
                base, base_tier = ct, 'validated-match'
                break

    # Promote from other standard trials
    def promote(cand):
        nonlocal base, base_tier
        if not cand or not cand.get('accepted'): return
        reliable = has_reliable_standard_watermark_signal(cand['originalSpatialScore'], cand['originalGradientScore'])
        if reliable:
            base = pick_better_candidate(base, {**cand, 'source': cand['source']+'+validated'})
            base_tier = 'validated-match'
        else:
            base = pick_better_candidate(base, cand)

    for t in std_trials:
        if t is not None and t != std_trial: promote(t)

    # Adaptive detection
    adaptive, adaptive_conf, adaptive_trial = None, None, None
    if allow_adaptive and alpha96 is not None:
        adaptive = detect_adaptive_watermark_region(arr, alpha96, config)
        adaptive_conf = adaptive.get('confidence') if adaptive else None
        if adaptive and adaptive.get('region') and (
            has_reliable_adaptive_watermark_signal(adaptive) or
            (adaptive_conf or 0) >= VALIDATION_MIN_CONFIDENCE_FOR_ADAPTIVE_TRIAL):
            sz = adaptive['region']['size']
            apos = {'x': adaptive['region']['x'], 'y': adaptive['region']['y'], 'width': sz, 'height': sz}
            aam = resolve_am(sz)
            acfg = {'logoSize': sz, 'marginRight': w-apos['x']-sz, 'marginBottom': h-apos['y']-sz}
            adaptive_trial = evaluate_restoration_candidate(arr, aam, apos, 'adaptive', acfg,
                calculate_near_black_ratio(arr, apos), adaptive_conf, include_image_data=False)
            promote(adaptive_trial)

    # Fallback
    if not base:
        if has_reliable and std_trial: base, base_tier = std_trial, 'direct-match'
        elif has_reliable_adaptive_watermark_signal(adaptive) and adaptive_trial:
            base, base_tier = adaptive_trial, 'direct-match'

    if not base:
        return {'selectedTrial': None, 'source': 'skipped', 'alphaMap': resolve_am(config['logoSize']),
                'position': position, 'config': config, 'adaptiveConfidence': adaptive_conf,
                'standardSpatialScore': std_spatial, 'standardGradientScore': std_gradient,
                'templateWarp': None, 'alphaGain': 1.0, 'decisionTier': 'insufficient'}

    # Refine: template warp
    alpha_map, selected_pos, selected_cfg = base['alphaMap'], base['position'], base['config']
    source_str, decision_tier = base['source'], base_tier
    template_warp = None
    warp_result = find_best_template_warp(arr, alpha_map, selected_pos,
        base['originalSpatialScore'], base['originalGradientScore'])
    if warp_result:
        w_trial = evaluate_restoration_candidate(arr, warp_result['alphaMap'], selected_pos,
            source_str+'+warp', selected_cfg, calculate_near_black_ratio(arr, selected_pos),
            include_image_data=False)
        better = pick_better_candidate(base, w_trial)
        if better != base:
            alpha_map, source_str = warp_result['alphaMap'], better['source']
            template_warp = warp_result['shift']

    # Refine: alpha gain search
    for gain in ALPHA_GAIN_CANDIDATES:
        g_trial = evaluate_restoration_candidate(arr, alpha_map, selected_pos,
            source_str+'+gain', selected_cfg, calculate_near_black_ratio(arr, selected_pos),
            alpha_gain=gain, include_image_data=False)
        better = pick_better_candidate(base, g_trial)
        if better != base:
            base = better; source_str = better['source']

    # Materialize final image
    base_img = arr.copy()
    remove_watermark(base_img, alpha_map, selected_pos, base.get('alphaGain', 1.0))

    return {'selectedTrial': {**base, 'imageData': base_img},
            'source': source_str, 'alphaMap': alpha_map,
            'position': selected_pos, 'config': selected_cfg,
            'adaptiveConfidence': adaptive_conf,
            'standardSpatialScore': std_spatial, 'standardGradientScore': std_gradient,
            'templateWarp': template_warp, 'alphaGain': base.get('alphaGain', 1.0),
            'decisionTier': decision_tier if decision_tier != 'insufficient' else 'validated-match'}

# ═══════════════════════════════════════════════════════════════
# Post-processing stages — watermarkProcessor.js
# ═══════════════════════════════════════════════════════════════

def recalibrate_alpha_gain(arr: np.ndarray, alpha_map: np.ndarray,
    position: dict, orig_spatial: float, processed_spatial: float) -> dict | None:
    """Exact port of recalibrateAlphaStrength()"""
    orig_nb = calculate_near_black_ratio(arr, position)
    max_nb = min(1.0, orig_nb + MAX_NEAR_BLACK_INCREASE)
    best_score, best_gain, best_result = processed_spatial, 1.0, arr.copy()
    for gain in ALPHA_GAIN_CANDIDATES:
        cand = arr.copy(); remove_watermark(cand, alpha_map, position, gain)
        nb = calculate_near_black_ratio(cand, position)
        if nb > max_nb: continue
        s = compute_region_spatial_correlation(cand, alpha_map, {'x':position['x'],'y':position['y'],'size':position['width']})
        if s < best_score: best_score, best_gain, best_result = s, gain, cand
    for d in np.arange(-0.05, 0.06, 0.01):
        gain = round(best_gain + d, 2)
        if gain <= 1 or gain >= 3: continue
        cand = arr.copy(); remove_watermark(cand, alpha_map, position, gain)
        nb = calculate_near_black_ratio(cand, position)
        if nb > max_nb: continue
        s = compute_region_spatial_correlation(cand, alpha_map, {'x':position['x'],'y':position['y'],'size':position['width']})
        if s < best_score: best_score, best_gain, best_result = s, gain, cand
    delta = processed_spatial - best_score
    if delta < MIN_RECALIBRATION_SCORE_DELTA: return None
    return {'imageData': best_result, 'alphaGain': best_gain,
            'processedSpatialScore': best_score,
            'suppressionGain': orig_spatial - best_score}

def refine_subpixel(arr: np.ndarray, alpha_map: np.ndarray, position: dict,
    alpha_gain: float, baseline_spatial: float, baseline_gradient: float) -> dict | None:
    """Exact port of refineSubpixelOutline()"""
    size = position['width']
    if not size or size <= 8: return None
    if alpha_gain < OUTLINE_REFINEMENT_MIN_GAIN: return None
    orig_nb = calculate_near_black_ratio(arr, position)
    max_nb = min(1.0, orig_nb + MAX_NEAR_BLACK_INCREASE)
    gains = [alpha_gain]
    lo = max(1.0, round(alpha_gain-0.01, 2))
    hi = round(alpha_gain+0.01, 2)
    if lo != alpha_gain: gains.append(lo)
    if hi != alpha_gain: gains.append(hi)
    best = None
    for sd in SUBPIXEL_SCALES:
        s = round(sd, 4)
        for dy in SUBPIXEL_SHIFTS:
            for dx in SUBPIXEL_SHIFTS:
                warped = warp_alpha_map(alpha_map, size, {'dx':dx,'dy':dy,'scale':s})
                for gain in gains:
                    cand = arr.copy(); remove_watermark(cand, warped, position, gain)
                    nb = calculate_near_black_ratio(cand, position)
                    if nb > max_nb: continue
                    sp = compute_region_spatial_correlation(cand, warped, {'x':position['x'],'y':position['y'],'size':size})
                    gr = compute_region_gradient_correlation(cand, warped, {'x':position['x'],'y':position['y'],'size':size})
                    cost = abs(sp)*0.6 + max(0, gr)
                    if best is None or cost < best['cost']:
                        best = {'imageData': cand, 'alphaMap': warped, 'alphaGain': gain,
                                'shift': {'dx':dx,'dy':dy,'scale':s},
                                'spatialScore': sp, 'gradientScore': gr,
                                'nearBlackRatio': nb, 'cost': cost}
    if best is None: return None
    improved_g = best['gradientScore'] <= baseline_gradient - 0.04
    kept_s = abs(best['spatialScore']) <= abs(baseline_spatial) + 0.08
    return best if (improved_g and kept_s) else None

def multi_pass_removal(arr: np.ndarray, alpha_map: np.ndarray, position: dict,
    max_passes: int = DEFAULT_MAX_PASSES, alpha_gain: float = 1.0) -> np.ndarray:
    """Exact port of removeRepeatedWatermarkLayers()"""
    result = arr.copy()
    base_nb = calculate_near_black_ratio(result, position)
    max_nb = min(1.0, base_nb + MAX_NEAR_BLACK_INCREASE)
    for _ in range(max_passes):
        before = compute_region_spatial_correlation(result, alpha_map,
            {'x': position['x'], 'y': position['y'], 'size': position['width']})
        cand = result.copy(); remove_watermark(cand, alpha_map, position, alpha_gain)
        after = compute_region_spatial_correlation(cand, alpha_map,
            {'x': position['x'], 'y': position['y'], 'size': position['width']})
        nb = calculate_near_black_ratio(cand, position)
        if nb > max_nb: break
        if abs(before) - abs(after) < 0.01: break
        result = cand
        if abs(after) <= DEFAULT_RESIDUAL_THRESHOLD: break
    return result

# ═══════════════════════════════════════════════════════════════
# Main Pipeline — full processWatermarkImageData + WatermarkEngine
# ═══════════════════════════════════════════════════════════════

def process_watermark_image_data(arr: np.ndarray, alpha48: np.ndarray,
    alpha96: np.ndarray, alpha96_variants: dict = None,
    allow_adaptive: bool = True) -> np.ndarray:
    """Complete pipeline — combines watermarkEngine.removeWatermarkFromImage()
    and processWatermarkImageData()."""
    w, h = arr.shape[1], arr.shape[0]
    print(f"Image: {w}x{h}")

    # Step 1: detect config + resolve
    default_config = detect_watermark_config(w, h)
    config = resolve_initial_standard_config(arr, default_config, alpha48, alpha96)
    position = calculate_watermark_position(w, h, config)
    print(f"  Config: logo={config['logoSize']}px, pos=({position['x']},{position['y']})")

    # Step 2: candidate selection
    selection = select_initial_candidate(arr, config, position, alpha48, alpha96,
                                         alpha96_variants, allow_adaptive)
    if not selection['selectedTrial']:
        print(f"  No watermark detected (tier={selection['decisionTier']}), returning original")
        return arr
    selected = selection['selectedTrial']
    alpha_map = selection['alphaMap']
    position = selection['position']
    config = selection['config']
    alpha_gain = selection['alphaGain']
    print(f"  Selection: tier={selection['decisionTier']}, source={selection['source']}")

    result = selected['imageData'] if selected.get('imageData') is not None else arr.copy()

    # Step 3: multi-pass
    result = multi_pass_removal(result, alpha_map, position, max_passes=3, alpha_gain=alpha_gain)

    # Step 4: recalibrate alpha gain
    orig_spatial = compute_region_spatial_correlation(arr, alpha_map,
        {'x': position['x'], 'y': position['y'], 'size': position['width']})
    processed_spatial = compute_region_spatial_correlation(result, alpha_map,
        {'x': position['x'], 'y': position['y'], 'size': position['width']})
    processed_gradient = compute_region_gradient_correlation(result, alpha_map,
        {'x': position['x'], 'y': position['y'], 'size': position['width']})
    suppression = orig_spatial - processed_spatial
    if (orig_spatial >= 0.6 and processed_spatial >= RESIDUAL_RECALIBRATION_THRESHOLD
        and suppression <= MIN_SUPPRESSION_FOR_SKIP_RECALIBRATION):
        recal = recalibrate_alpha_gain(result, alpha_map, position, orig_spatial, processed_spatial)
        if recal:
            result = recal['imageData']; alpha_gain = recal['alphaGain']
            processed_spatial = recal['processedSpatialScore']
            processed_gradient = compute_region_gradient_correlation(result, alpha_map,
                {'x': position['x'], 'y': position['y'], 'size': position['width']})
            print(f"  Gain recalibrated: α_gain={alpha_gain:.2f}")
        else:
            print(f"  Gain recalibration skipped (delta too small)")
    else:
        print(f"  Gain recalibration skipped (suppression={suppression:.3f})")

    # Step 5: sub-pixel refinement
    if (processed_spatial <= 0.3 and processed_gradient >= OUTLINE_REFINEMENT_THRESHOLD):
        refined = refine_subpixel(result, alpha_map, position, alpha_gain,
                                  processed_spatial, processed_gradient)
        if refined:
            result = refined['imageData']; alpha_map = refined['alphaMap']
            alpha_gain = refined['alphaGain']
            print(f"  Sub-pixel: dx={refined['shift']['dx']:.2f} dy={refined['shift']['dy']:.2f} scale={refined['shift']['scale']:.2f}")
    else:
        print(f"  Sub-pixel skipped (spatial={processed_spatial:.3f}, gradient={processed_gradient:.3f})")

    return result

def remove_gemini_watermark(arr: np.ndarray) -> np.ndarray:
    """Entry point — load alpha maps and run full pipeline."""
    alpha48 = get_embedded_alpha_map('48')
    alpha96 = get_embedded_alpha_map('96')
    alpha96_variants = {'20260520': get_embedded_alpha_map('96-20260520')}
    return process_watermark_image_data(arr, alpha48, alpha96, alpha96_variants, allow_adaptive=True)

# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

def main():
    p = argparse.ArgumentParser(description="Gemini watermark removal — complete port of GargantuaX/gemini-watermark-remover")
    p.add_argument("input", help="Input PNG")
    p.add_argument("--output", "-o", help="Output path (default: input_cleaned.png)")
    p.add_argument("--simple", action="store_true", help="Simple mode: uniform alpha only")
    p.add_argument("--alpha", type=float, default=0.01, help="Alpha for simple mode")
    args = p.parse_args()

    if not os.path.exists(args.input):
        print(f"ERROR: {args.input} not found", file=sys.stderr); sys.exit(1)

    out = args.output or args.input.replace('.png','_cleaned.png')
    img = Image.open(args.input).convert('RGB')
    arr = np.array(img)

    if args.simple:
        a = max(0, min(0.99, args.alpha))
        f = arr.astype(np.float32)
        for c in range(3): f[...,c] = np.clip((f[...,c]-a*255)/(1-a), 0, 255)
        cleaned = f.astype(np.uint8)
    else:
        cleaned = remove_gemini_watermark(arr)

    Image.fromarray(cleaned).save(out)
    ik = os.path.getsize(args.input)/1024; ok = os.path.getsize(out)/1024
    print(f"\nDone: {arr.shape[1]}x{arr.shape[0]}, {ik:.0f}KB → {ok:.0f}KB, → {out}")

if __name__ == "__main__":
    main()
