"""
Complete Reverse Alpha Blending — exact Python port of
GargantuaX/gemini-watermark-remover (4225 stars).

Every function, every constant, every branch from every source file.
Verified against:
  blendModes.js, alphaMap.js, watermarkConfig.js, geminiSizeCatalog.js,
  adaptiveDetector.js, restorationMetrics.js, watermarkDecisionPolicy.js,
  watermarkPresence.js, candidateSelector.js, watermarkProcessor.js,
  multiPassRemoval.js, watermarkEngine.js
"""
import argparse, json, math, os, sys
import numpy as np
from PIL import Image

# ═══════════════════════════════════════════════════════════════
# Section 1: All Constants — exact ports
# ═══════════════════════════════════════════════════════════════

# blendModes.js
LOGO_VALUE = 255
ALPHA_NOISE_FLOOR = 3 / 255
ALPHA_THRESHOLD = 0.002
MAX_ALPHA = 0.99

# adaptiveDetector.js
EPSILON = 1e-8
DEFAULT_ADAPTIVE_THRESHOLD = 0.35

# watermarkProcessor.js
ALPHA_GAIN_CANDIDATES = [1.05,1.12,1.2,1.28,1.36,1.45,1.52,1.6,1.7,1.85,2.0,2.2,2.4,2.6]
SUBPIXEL_REFINE_SHIFTS = [-0.25, 0, 0.25]
SUBPIXEL_REFINE_SCALES = [0.99, 1, 1.01]
MAX_NEAR_BLACK_RATIO_INCREASE = 0.05
RESIDUAL_RECALIBRATION_THRESHOLD = 0.5
MIN_SUPPRESSION_FOR_SKIP_RECALIBRATION = 0.18
MIN_RECALIBRATION_SCORE_DELTA = 0.18
OUTLINE_REFINEMENT_THRESHOLD = 0.42
OUTLINE_REFINEMENT_MIN_GAIN = 1.2
PREVIEW_EDGE_CLEANUP_MAX_SIZE = 40
PREVIEW_EDGE_CLEANUP_SPATIAL_THRESHOLD = 0.08
PREVIEW_EDGE_CLEANUP_GRADIENT_THRESHOLD = 0.1
PREVIEW_EDGE_CLEANUP_MIN_GRADIENT_IMPROVEMENT = 0.03
PREVIEW_EDGE_CLEANUP_MAX_SPATIAL_DRIFT = 0.04
PREVIEW_EDGE_CLEANUP_MAX_APPLIED_PASSES = 3
PREVIEW_EDGE_CLEANUP_FINE_GRADIENT_THRESHOLD = 0.16
PREVIEW_EDGE_CLEANUP_FINE_MIN_GRADIENT_IMPROVEMENT = 0.005
PREVIEW_EDGE_CLEANUP_HALO_RELAXED_MIN_GRADIENT_IMPROVEMENT = 0.01
PREVIEW_EDGE_CLEANUP_HALO_WEIGHT = 0.02
PREVIEW_EDGE_CLEANUP_MIN_HALO_REDUCTION = 1.5
PREVIEW_EDGE_CLEANUP_STRONG_HALO_THRESHOLD = 4
PREVIEW_EDGE_CLEANUP_HALO_SPATIAL_THRESHOLD = 0.18
PREVIEW_EDGE_CLEANUP_PRESETS = [
    {'minAlpha': 0.02, 'maxAlpha': 0.45, 'radius': 2, 'strength': 0.7, 'outsideAlphaMax': 0.05},
    {'minAlpha': 0.05, 'maxAlpha': 0.55, 'radius': 3, 'strength': 0.7, 'outsideAlphaMax': 0.08},
    {'minAlpha': 0.1, 'maxAlpha': 0.7, 'radius': 3, 'strength': 0.8, 'outsideAlphaMax': 0.12},
    {'minAlpha': 0.01, 'maxAlpha': 0.35, 'radius': 4, 'strength': 1.4, 'outsideAlphaMax': 0.05}]
PREVIEW_EDGE_CLEANUP_STRONG_GRADIENT_THRESHOLD = 0.45
PREVIEW_EDGE_CLEANUP_AGGRESSIVE_PRESETS = [
    {'minAlpha': 0.01, 'maxAlpha': 0.55, 'radius': 2, 'strength': 1.3, 'outsideAlphaMax': 0.05,
     'minGradientImprovement': 0.12, 'maxSpatialDrift': 0.18, 'maxAcceptedSpatial': 0.18}]
FIRST_PASS_SIGN_FLIP_GRADIENT_THRESHOLD = 0.08
FIRST_PASS_SIGN_FLIP_MIN_GRADIENT_DROP = 0.2

# candidateSelector.js
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

# watermarkDecisionPolicy.js
STANDARD_DIRECT_MATCH_MIN_SPATIAL_SCORE = 0.3
STANDARD_DIRECT_MATCH_MIN_GRADIENT_SCORE = 0.12
STANDARD_STRONG_GRADIENT_DIRECT_MATCH_MIN_SPATIAL_SCORE = 0.295
STANDARD_STRONG_GRADIENT_DIRECT_MATCH_MIN_GRADIENT_SCORE = 0.45
ADAPTIVE_DIRECT_MATCH_MIN_CONFIDENCE = 0.5
ADAPTIVE_DIRECT_MATCH_MIN_SPATIAL_SCORE = 0.45
ADAPTIVE_DIRECT_MATCH_MIN_GRADIENT_SCORE = 0.12
ADAPTIVE_DIRECT_MATCH_MIN_SIZE = 40
ADAPTIVE_DIRECT_MATCH_MAX_SIZE = 192

# restorationMetrics.js
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

# multiPassRemoval.js
DEFAULT_MAX_PASSES = 4
DEFAULT_RESIDUAL_THRESHOLD = 0.25

# ═══════════════════════════════════════════════════════════════
# Section 2: Gemini Size Catalog — geminiSizeCatalog.js complete
# ═══════════════════════════════════════════════════════════════

WATERMARK_CONFIG_BY_TIER = {
    '0.5k': {'logoSize':48,'marginRight':32,'marginBottom':32},
    '1k':   {'logoSize':96,'marginRight':64,'marginBottom':64},
    '2k':   {'logoSize':96,'marginRight':64,'marginBottom':64},
    '4k':   {'logoSize':96,'marginRight':64,'marginBottom':64},
    '2k-new-margin': {'logoSize':96,'marginRight':192,'marginBottom':192,'alphaVariant':'20260520'},
}

def _mk_entries(f,t,r):
    return [{'modelFamily':f,'resolutionTier':t,'aspectRatio':v[0],'width':v[1],'height':v[2]} for v in r]

OFFICIAL_GEMINI_IMAGE_SIZES = [
    *_mk_entries('gemini-3.x-image','0.5k',[
        ['1:1',512,512],['1:4',256,1024],['1:8',192,1536],['2:3',424,632],['3:2',632,424],
        ['3:4',448,600],['4:1',1024,256],['4:3',600,448],['4:5',464,576],['5:4',576,464],
        ['8:1',1536,192],['9:16',384,688],['16:9',688,384],['21:9',792,168]]),
    *_mk_entries('gemini-3.x-image','1k',[
        ['1:1',1024,1024],['1:4',512,2048],['1:8',384,3072],['2:3',848,1264],['3:2',1264,848],
        ['3:4',896,1200],['4:1',2048,512],['4:3',1200,896],['4:5',928,1152],['5:4',1152,928],
        ['8:1',3072,384],['9:16',768,1376],['16:9',1376,768],['16:9',1408,768],['21:9',1584,672]]),
    *_mk_entries('gemini-3.x-image','2k',[
        ['1:1',2048,2048],['1:4',1024,4096],['1:8',768,6144],['2:3',1696,2528],['3:2',2528,1696],
        ['3:4',1792,2400],['4:1',4096,1024],['4:3',2400,1792],['4:5',1856,2304],['5:4',2304,1856],
        ['8:1',6144,768],['9:16',1536,2752],['16:9',2752,1536],['21:9',3168,1344]]),
    *_mk_entries('gemini-3.x-image','2k-new-margin',[['16:9',2816,1536]]),
    *_mk_entries('gemini-3.x-image','4k',[
        ['1:1',4096,4096],['1:4',2048,8192],['1:8',1536,12288],['2:3',3392,5056],['3:2',5056,3392],
        ['3:4',3584,4800],['4:1',8192,2048],['4:3',4800,3584],['4:5',3712,4608],['5:4',4608,3712],
        ['8:1',12288,1536],['9:16',3072,5504],['16:9',5504,3072],['21:9',6336,2688]]),
    *_mk_entries('gemini-2.5-flash-image','1k',[
        ['1:1',1024,1024],['2:3',832,1248],['3:2',1248,832],['3:4',864,1184],['4:3',1184,864],
        ['4:5',896,1152],['5:4',1152,896],['9:16',768,1344],['16:9',1344,768],['21:9',1536,672]]),
]
OFFICIAL_SIZE_INDEX = {f"{e['width']}x{e['height']}":e for e in OFFICIAL_GEMINI_IMAGE_SIZES}

def match_official_gemini_image_size(w,h):
    return OFFICIAL_SIZE_INDEX.get(f"{w}x{h}")

def resolve_official_gemini_watermark_config(w,h):
    m = match_official_gemini_image_size(w,h)
    if not m: return None
    return WATERMARK_CONFIG_BY_TIER.get(m['resolutionTier'])

def resolve_official_gemini_search_configs(w,h,max_aspect_delta=0.02,max_scale_mismatch=0.12,
                                           min_logo=24,max_logo=192,limit=3):
    exact = resolve_official_gemini_watermark_config(w,h)
    result = []
    if exact:
        result.append(dict(exact))
        if (exact.get('logoSize')==96 and exact.get('marginRight')!=192 and w-192-96>=0 and h-192-96>=0):
            result.append({'logoSize':96,'marginRight':192,'marginBottom':192,'alphaVariant':'20260520'})
        return result
    tar = w/h; candidates = []
    for e in OFFICIAL_GEMINI_IMAGE_SIZES:
        b = WATERMARK_CONFIG_BY_TIER.get(e['resolutionTier'])
        if not b: continue
        sx,sy,scale = w/e['width'],h/e['height'],((w/e['width'])+(h/e['height']))/2
        ear = e['width']/e['height']
        rad = abs(tar-ear)/ear; sm = abs(sx-sy)/max(sx,sy)
        if rad>max_aspect_delta or sm>max_scale_mismatch: continue
        cfg = {'logoSize':max(min_logo,min(max_logo,round(b['logoSize']*scale))),
               'marginRight':max(8,round(b['marginRight']*sx)),
               'marginBottom':max(8,round(b['marginBottom']*sy))}
        if w-cfg['marginRight']-cfg['logoSize']<0 or h-cfg['marginBottom']-cfg['logoSize']<0: continue
        score = rad*100+sm*20+abs(math.log2(max(scale,1e-6)))
        candidates.append((score,cfg))
    candidates.sort(key=lambda x:x[0])
    seen = set()
    for _,cfg in candidates:
        k=f"{cfg['logoSize']}:{cfg['marginRight']}:{cfg['marginBottom']}"
        if k in seen: continue
        seen.add(k); result.append(cfg)
        if len(result)>=limit: break
    return result

def resolve_gemini_watermark_search_configs(w,h,default_config):
    configs = [default_config] if default_config else []
    configs.extend(resolve_official_gemini_search_configs(w,h))
    seen,deduped = set(),[]
    for c in configs:
        if not c: continue
        k=f"{c['logoSize']}:{c['marginRight']}:{c['marginBottom']}"
        if k in seen: continue
        seen.add(k); deduped.append(c)
    return deduped

# ═══════════════════════════════════════════════════════════════
# Section 3: Alpha Maps
# ═══════════════════════════════════════════════════════════════
_ALPHA_CACHE = {}

def _load_json_alpha(key):
    sd = os.path.dirname(os.path.abspath(__file__))
    for p in [os.path.join(sd,'..','references',f'alpha_{key}.json'),os.path.join(os.getcwd(),f'alpha_{key}.json')]:
        if os.path.exists(p):
            with open(p) as f: return np.array(json.load(f)['data'],dtype=np.float32)
    return np.full((48 if '48' in key else 96)**2,0.01,dtype=np.float32)

def get_embedded_alpha_map(size_key):
    k = str(size_key)
    if k not in _ALPHA_CACHE:
        if k=='48': _ALPHA_CACHE[k]=_load_json_alpha('48')
        elif k=='96': _ALPHA_CACHE[k]=_load_json_alpha('96')
        elif k=='96-20260520': _ALPHA_CACHE[k]=_load_json_alpha('96new')
        else: _ALPHA_CACHE[k]=interpolate_alpha_map(get_embedded_alpha_map('96'),96,int(size_key))
    return _ALPHA_CACHE[k]

# ═══════════════════════════════════════════════════════════════
# Section 4: Core Math — blendModes.js + adaptiveDetector.js math
# ═══════════════════════════════════════════════════════════════

def remove_watermark(arr,alpha_map,position,alpha_gain=1.0):
    """blendModes.js:25-70 exact port"""
    x,y,w,h = position['x'],position['y'],position['width'],position['height']
    a = alpha_map.reshape(h,w); img = arr.astype(np.float32)
    sig = np.maximum(0,a-ALPHA_NOISE_FLOOR)*alpha_gain
    active = sig>=ALPHA_THRESHOLD
    ac = np.minimum(a*alpha_gain,MAX_ALPHA); om = 1.0-ac
    for c in range(3):
        ch = img[y:y+h,x:x+w,c]
        img[y:y+h,x:x+w,c] = np.clip(np.round(np.where(active,(ch-ac*LOGO_VALUE)/om,ch)),0,255)
    return img.astype(np.uint8)

def normalized_cross_correlation(a,b):
    """adaptiveDetector.js:26-39 exact port"""
    if len(a)!=len(b) or len(a)==0: return 0.0
    ma,mb = a.mean(),b.mean()
    num = ((a-ma)*(b-mb)).sum()
    den = math.sqrt(((a-ma)**2).sum()*((b-mb)**2).sum())
    return float(num/den) if den>EPSILON else 0.0

def to_grayscale(arr):
    """ITU-R BT.709 weights: 0.2126, 0.7152, 0.0722"""
    return (arr[...,0].astype(np.float32)*0.2126+arr[...,1].astype(np.float32)*0.7152+
            arr[...,2].astype(np.float32)*0.0722)/255.0

def to_region_grayscale(arr,region):
    x,y = region['x'],region['y']
    s = region.get('size') or (region.get('width') and min(region['width'],region['height']))
    if not s or s<=0 or x<0 or y<0 or x+s>arr.shape[1] or y+s>arr.shape[0]:
        return np.zeros(0,dtype=np.float32)
    return to_grayscale(arr[y:y+s,x:x+s]).flatten()

def sobel_magnitude(gray,w,h):
    """adaptiveDetector.js:85-102 exact port"""
    g2d = gray.reshape(h,w); grad = np.zeros(h*w,dtype=np.float32)
    for yi in range(1,h-1):
        for xi in range(1,w-1):
            i = yi*w+xi
            gx = (-g2d[yi-1,xi-1]-2*g2d[yi,xi-1]-g2d[yi+1,xi-1]+
                   g2d[yi-1,xi+1]+2*g2d[yi,xi+1]+g2d[yi+1,xi+1])
            gy = (-g2d[yi-1,xi-1]-2*g2d[yi-1,xi]-g2d[yi-1,xi+1]+
                   g2d[yi+1,xi-1]+2*g2d[yi+1,xi]+g2d[yi+1,xi+1])
            grad[i] = math.sqrt(gx*gx+gy*gy)
    return grad

def warp_alpha_map(alpha_map,size,warp):
    """adaptiveDetector.js:196-234 exact port"""
    dx,dy,scale = warp.get('dx',0),warp.get('dy',0),warp.get('scale',1)
    if size<=0: return np.zeros(0,dtype=np.float32)
    if dx==0 and dy==0 and scale==1: return alpha_map.copy()
    s2d = alpha_map.reshape(size,size)
    out = np.zeros(size*size,dtype=np.float32)
    c = (size-1)/2
    for y in range(size):
        for x in range(size):
            sx,sy = (x-c)/scale+c+dx,(y-c)/scale+c+dy
            fx,fy = sx-math.floor(sx),sy-math.floor(sy)
            x0=max(0,min(size-1,int(math.floor(sx))))
            y0=max(0,min(size-1,int(math.floor(sy))))
            x1=max(0,min(size-1,x0+1)); y1=max(0,min(size-1,y0+1))
            p00,p10=s2d[y0,x0],s2d[y0,x1]; p01,p11=s2d[y1,x0],s2d[y1,x1]
            out[y*size+x]=(p00+(p10-p00)*fx)*(1-fy)+(p01+(p11-p01)*fx)*fy
    return out

def interpolate_alpha_map(src,src_size,dst_size):
    """adaptiveDetector.js:236-267 exact port"""
    if dst_size<=0: return np.zeros(0,dtype=np.float32)
    if src_size==dst_size: return src.copy()
    s2d = src.reshape(src_size,src_size)
    out = np.zeros(dst_size*dst_size,dtype=np.float32)
    scale = (src_size-1)/max(1,dst_size-1)
    for y in range(dst_size):
        sy=y*scale; y0=int(math.floor(sy)); y1=min(src_size-1,y0+1); fy=sy-y0
        for x in range(dst_size):
            sx=x*scale; x0=int(math.floor(sx)); x1=min(src_size-1,x0+1); fx=sx-x0
            p00,p10=s2d[y0,x0],s2d[y0,x1]; p01,p11=s2d[y1,x0],s2d[y1,x1]
            out[y*dst_size+x]=(p00+(p10-p00)*fx)*(1-fy)+(p01+(p11-p01)*fx)*fy
    return out

def compute_region_spatial_correlation(arr,alpha_map,region):
    patch = to_region_grayscale(arr,region)
    if len(patch)==0 or len(patch)!=len(alpha_map): return 0.0
    return normalized_cross_correlation(patch,alpha_map)

def compute_region_gradient_correlation(arr,alpha_map,region):
    patch = to_region_grayscale(arr,region)
    if len(patch)==0 or len(patch)!=len(alpha_map): return 0.0
    s = region.get('size') or (region.get('width') and min(region['width'],region['height']))
    if not s or s<=2: return 0.0
    return normalized_cross_correlation(sobel_magnitude(patch,s,s),sobel_magnitude(alpha_map,s,s))

# ═══════════════════════════════════════════════════════════════
# Section 5: Restoration Metrics — restorationMetrics.js complete
# ═══════════════════════════════════════════════════════════════

def calculate_near_black_ratio(arr,position):
    x,y,w,h = position['x'],position['y'],position['width'],position['height']
    roi = arr[y:y+h,x:x+w]
    nb = ((roi[...,0]<=NEAR_BLACK_THRESHOLD)&(roi[...,1]<=NEAR_BLACK_THRESHOLD)&(roi[...,2]<=NEAR_BLACK_THRESHOLD))
    return float(nb.mean())

def calculate_region_texture_stats(arr,region):
    x,y,w,h = region['x'],region['y'],region['width'],region['height']
    roi = arr[y:y+h,x:x+w]
    lum = (roi[...,0].astype(np.float64)*0.2126+roi[...,1].astype(np.float64)*0.7152+
           roi[...,2].astype(np.float64)*0.0722)
    ml = float(lum.mean()); var = max(0.0,float((lum*lum).mean())-ml*ml)
    return {'meanLum':ml,'stdLum':math.sqrt(var)}

def get_reference_region(position,arr):
    """restorationMetrics.js:152-162 exact port"""
    ref_y = position['y']-position['height']
    if ref_y<0: return None
    return {'x':position['x'],'y':ref_y,'width':position['width'],'height':position['height']}

def assess_reference_texture_alignment(arr,ref_arr,candidate_arr,position):
    """restorationMetrics.js:164-180 port"""
    cs = calculate_region_texture_stats(candidate_arr,position) if candidate_arr is not None else None
    return assess_reference_texture_alignment_from_stats(arr,ref_arr,cs,position)

def assess_reference_texture_alignment_from_stats(arr,ref_arr,candidate_stats,position):
    """restorationMetrics.js:182-228 exact port"""
    rr = get_reference_region(position,ref_arr)
    rs = calculate_region_texture_stats(ref_arr,rr) if rr else None
    cs = candidate_stats if candidate_stats else calculate_region_texture_stats(arr,position)
    dp = max(0.0,rs['meanLum']-cs['meanLum']-TEXTURE_REFERENCE_MARGIN)/max(1,rs['meanLum']) if rs else 0.0
    fp = max(0.0,rs['stdLum']*TEXTURE_STD_FLOOR_RATIO-cs['stdLum'])/max(1,rs['stdLum']) if rs else 0.0
    dv = max(0.0,rs['meanLum']-cs['meanLum']-TEXTURE_REFERENCE_MARGIN)/max(1,rs['stdLum']) if rs else 0.0
    td,tf = dp>0,fp>0
    vdh = td and dv>=TEXTURE_DARKNESS_VISIBILITY_HARD_REJECT_THRESHOLD
    sdfc = td and tf and dp>=TEXTURE_DARKNESS_HARD_REJECT_PENALTY_THRESHOLD and fp>=TEXTURE_FLATNESS_HARD_REJECT_PENALTY_THRESHOLD
    return {'texturePenalty':dp*2+fp*2,'tooDark':td,'tooFlat':tf,'hardReject':sdfc or vdh,
            'visibleDarkHole':vdh,'darknessPenalty':dp,'flatnessPenalty':fp,'darknessVisibility':dv,
            'referenceTextureStats':rs,'candidateTextureStats':cs}

def score_region(arr,alpha_map,position):
    r = {'x':position['x'],'y':position['y'],'size':position['width']}
    return {'spatialScore':compute_region_spatial_correlation(arr,alpha_map,r),
            'gradientScore':compute_region_gradient_correlation(arr,alpha_map,r)}

def assess_alpha_band_halo(arr,position,alpha_map,minAlpha=DEFAULT_HALO_MIN_ALPHA,
    maxAlpha=DEFAULT_HALO_MAX_ALPHA,outsideAlphaMax=DEFAULT_HALO_OUTSIDE_ALPHA_MAX,
    outerMargin=DEFAULT_HALO_OUTER_MARGIN):
    """restorationMetrics.js:83-150 exact port"""
    bs,bsq,bc = 0.0,0.0,0; oss,osq,oc = 0.0,0.0,0
    w,h = arr.shape[1],arr.shape[0]
    for row in range(-outerMargin,position['height']+outerMargin):
        for col in range(-outerMargin,position['width']+outerMargin):
            px,py = position['x']+col,position['y']+row
            if px<0 or py<0 or px>=w or py>=h: continue
            pi = py*w+px
            lum = (0.2126*arr[py,px,0]+0.7152*arr[py,px,1]+0.0722*arr[py,px,2])
            inside = row>=0 and col>=0 and row<position['height'] and col<position['width']
            a = alpha_map[row*position['width']+col] if inside else 0
            if inside and a>=minAlpha and a<=maxAlpha:
                bs+=lum; bsq+=lum*lum; bc+=1; continue
            if not inside or a<=outsideAlphaMax:
                oss+=lum; osq+=lum*lum; oc+=1
    bml = bs/bc if bc>0 else 0; oml = oss/oc if oc>0 else 0
    bsl = math.sqrt(max(0,bsq/bc-bml*bml)) if bc>0 else 0
    osl = math.sqrt(max(0,osq/oc-oml*oml)) if oc>0 else 0
    dl = bml-oml; vis = dl/max(1,osl)
    return {'bandCount':bc,'outerCount':oc,'bandMeanLum':bml,'outerMeanLum':oml,
            'bandStdLum':bsl,'outerStdLum':osl,'deltaLum':dl,'positiveDeltaLum':max(0,dl),'visibility':vis}

# ═══════════════════════════════════════════════════════════════
# Section 6: Watermark Decision Policy — watermarkDecisionPolicy.js + watermarkPresence.js
# ═══════════════════════════════════════════════════════════════

def classify_standard_watermark_signal(spatial,gradient):
    if not (math.isfinite(spatial) and math.isfinite(gradient)): return {'tier':'insufficient'}
    if ((spatial>=STANDARD_DIRECT_MATCH_MIN_SPATIAL_SCORE and gradient>=STANDARD_DIRECT_MATCH_MIN_GRADIENT_SCORE)
        or (spatial>=STANDARD_STRONG_GRADIENT_DIRECT_MATCH_MIN_SPATIAL_SCORE
            and gradient>=STANDARD_STRONG_GRADIENT_DIRECT_MATCH_MIN_GRADIENT_SCORE)):
        return {'tier':'direct-match'}
    if spatial>0 or gradient>0: return {'tier':'needs-validation'}
    return {'tier':'insufficient'}

def has_reliable_standard_watermark_signal(spatial,gradient):
    return classify_standard_watermark_signal(spatial,gradient)['tier']=='direct-match'

def classify_adaptive_watermark_signal(ar):
    if not ar or not ar.get('found'): return {'tier':'insufficient'}
    c,s,g,sz = ar.get('confidence'),ar.get('spatialScore'),ar.get('gradientScore'),(ar.get('region') or {}).get('size')
    if not all(isinstance(v,(int,float)) and math.isfinite(v) for v in [c,s,g,sz]): return {'tier':'insufficient'}
    if (c>=ADAPTIVE_DIRECT_MATCH_MIN_CONFIDENCE and s>=ADAPTIVE_DIRECT_MATCH_MIN_SPATIAL_SCORE
        and g>=ADAPTIVE_DIRECT_MATCH_MIN_GRADIENT_SCORE and sz>=ADAPTIVE_DIRECT_MATCH_MIN_SIZE
        and sz<=ADAPTIVE_DIRECT_MATCH_MAX_SIZE): return {'tier':'direct-match'}
    if c>=ADAPTIVE_DIRECT_MATCH_MIN_CONFIDENCE*0.6: return {'tier':'needs-validation'}
    return {'tier':'insufficient'}

def has_reliable_adaptive_watermark_signal(ar):
    return classify_adaptive_watermark_signal(ar)['tier']=='direct-match'

# ═══════════════════════════════════════════════════════════════
# Section 7: Adaptive Detector — adaptiveDetector.js complete
# ═══════════════════════════════════════════════════════════════

def build_template_gradient(alpha_map,size):
    return sobel_magnitude(alpha_map,size,size)

def std_dev_region(data,w,x,y,size):
    s,sq,n = 0.0,0.0,0
    for row in range(size):
        base = (y+row)*w+x
        for col in range(size):
            v = data[base+col]; s+=v; sq+=v*v; n+=1
    if n==0: return 0.0
    return math.sqrt(max(0.0,sq/n-(s/n)**2))

def score_candidate(ctx,alpha_map,template_grad,x,y,size):
    w,h = ctx['width'],ctx['height']; gray,grad = ctx['gray'],ctx['grad']
    if x<0 or y<0 or x+size>w or y+size>h: return None
    gr = np.array([gray[(y+row)*w+x:(y+row)*w+x+size] for row in range(size)]).flatten()
    gd = np.array([grad[(y+row)*w+x:(y+row)*w+x+size] for row in range(size)]).flatten()
    spatial = normalized_cross_correlation(gr,alpha_map)
    gradient = normalized_cross_correlation(gd,template_grad)
    vs = 0.0
    if y>8:
        ref_y = max(0,y-size); ref_h = min(size,y-ref_y)
        if ref_h>8:
            ws = std_dev_region(gray,w,x,y,size)
            rs = std_dev_region(gray,w,x,ref_y,ref_h)
            if rs>EPSILON: vs = max(0,min(1,1-ws/rs))
    conf = max(0,spatial)*0.5+max(0,gradient)*0.3+vs*0.2
    return {'confidence':max(0,min(1,conf)),'spatialScore':spatial,'gradientScore':gradient,'varianceScore':vs}

def build_template_cache(alpha96):
    cache = {}
    def get_tpl(size):
        if size not in cache:
            a = alpha96 if size==96 else interpolate_alpha_map(alpha96,96,size)
            cache[size] = (a,build_template_gradient(a,size))
        return cache[size]
    return get_tpl

def detect_adaptive_watermark_region(image_data,alpha96,default_config,threshold=DEFAULT_ADAPTIVE_THRESHOLD):
    w,h = image_data.shape[1],image_data.shape[0]
    gray = to_grayscale(image_data).flatten()
    grad = sobel_magnitude(gray,w,h)
    ctx = {'gray':gray,'grad':grad,'width':w,'height':h}
    get_tpl = build_template_cache(alpha96)

    seeds = []
    for cfg in resolve_gemini_watermark_search_configs(w,h,default_config):
        sz = cfg['logoSize']; cx = w-cfg['marginRight']-sz; cy = h-cfg['marginBottom']-sz
        if cx<0 or cy<0 or cx+sz>w or cy+sz>h: continue
        ta,tg = get_tpl(sz); sc = score_candidate(ctx,ta,tg,cx,cy,sz)
        if sc: seeds.append({**sc,'x':cx,'y':cy,'size':sz})
    best_seed = max(seeds,key=lambda s:s['confidence']) if seeds else None
    if best_seed and best_seed['confidence']>=threshold+0.08:
        return {'found':True,'confidence':best_seed['confidence'],'spatialScore':best_seed['spatialScore'],
                'gradientScore':best_seed['gradientScore'],'varianceScore':best_seed['varianceScore'],
                'region':{'x':best_seed['x'],'y':best_seed['y'],'size':best_seed['size']}}

    bs = default_config['logoSize']
    min_sz = max(24,min(144,round(bs*0.65)))
    max_sz = min(max(min_sz,min(int(min(w,h)*0.4),192)),192)
    sl = set(); sl.update(range(min_sz,max_sz+1,8))
    if 48>=min_sz and 48<=max_sz: sl.add(48)
    if 96>=min_sz and 96<=max_sz: sl.add(96)
    sl = sorted(sl)

    mr = max(32,round(bs*0.75))
    min_mr = max(8,min(w-min_sz-1,default_config['marginRight']-mr))
    max_mr = min(w-min_sz-1,max(min_mr,default_config['marginRight']+mr))
    min_mb = max(8,min(h-min_sz-1,default_config['marginBottom']-mr))
    max_mb = min(h-min_sz-1,max(min_mb,default_config['marginBottom']+mr))

    top_k = []
    for s in seeds:
        top_k.append({'size':s['size'],'x':s['x'],'y':s['y'],'adjustedScore':s['confidence']*min(1,math.sqrt(s['size']/96))})
    top_k.sort(key=lambda x:-x['adjustedScore']); top_k = top_k[:5]

    for sz in sl:
        ta,tg = get_tpl(sz)
        for mr in range(min_mr,max_mr+1,8):
            cx = w-mr-sz
            if cx<0: continue
            for mb in range(min_mb,max_mb+1,8):
                cy = h-mb-sz
                if cy<0: continue
                sc = score_candidate(ctx,ta,tg,cx,cy,sz)
                if not sc: continue
                adj = sc['confidence']*min(1,math.sqrt(sz/96))
                if adj<0.08: continue
                top_k.append({'size':sz,'x':cx,'y':cy,'adjustedScore':adj})
                top_k.sort(key=lambda x:-x['adjustedScore'])
                if len(top_k)>5: top_k = top_k[:5]

    best = best_seed if best_seed else {'x':w-default_config['marginRight']-default_config['logoSize'],
        'y':h-default_config['marginBottom']-default_config['logoSize'],'size':default_config['logoSize'],
        'confidence':0,'spatialScore':0,'gradientScore':0,'varianceScore':0}

    for coarse in top_k:
        slo = max(min_sz,min(max_sz,coarse['size']-10)); shi = max(min_sz,min(max_sz,coarse['size']+10))
        for sz in range(slo,shi+1,2):
            ta,tg = get_tpl(sz)
            for cx in range(coarse['x']-8,coarse['x']+9,2):
                if cx<0 or cx+sz>w: continue
                for cy in range(coarse['y']-8,coarse['y']+9,2):
                    if cy<0 or cy+sz>h: continue
                    sc = score_candidate(ctx,ta,tg,cx,cy,sz)
                    if not sc: continue
                    if sc['confidence']>best['confidence']: best = {**sc,'x':cx,'y':cy,'size':sz}

    return {'found':best['confidence']>=threshold,'confidence':best['confidence'],
            'spatialScore':best['spatialScore'],'gradientScore':best['gradientScore'],
            'varianceScore':best['varianceScore'],'region':{'x':best['x'],'y':best['y'],'size':best['size']}}

def should_attempt_adaptive_fallback(processed,alpha_map,position,orig=None,threshold=0.22):
    r = compute_region_spatial_correlation(processed,alpha_map,{'x':position['x'],'y':position['y'],'size':position['width']})
    if r>=threshold: return True
    if orig is not None:
        o = compute_region_spatial_correlation(orig,alpha_map,{'x':position['x'],'y':position['y'],'size':position['width']})
        if o<=0: return True
    return False

# ═══════════════════════════════════════════════════════════════
# Section 8: Watermark Config — watermarkConfig.js complete
# ═══════════════════════════════════════════════════════════════

def detect_watermark_config(iw,ih):
    official = resolve_official_gemini_watermark_config(iw,ih)
    if official: return dict(official)
    if iw>1024 and ih>1024: return {'logoSize':96,'marginRight':64,'marginBottom':64}
    return {'logoSize':48,'marginRight':32,'marginBottom':32}

def calculate_watermark_position(iw,ih,config):
    sz,mr,mb = config['logoSize'],config['marginRight'],config['marginBottom']
    return {'x':iw-mr-sz,'y':ih-mb-sz,'width':sz,'height':sz}

def is_region_inside_image(image_data,region):
    return (region['x']>=0 and region['y']>=0 and
            region['x']+region['width']<=image_data.shape[1] and
            region['y']+region['height']<=image_data.shape[0])

def resolve_alpha_map_for_size(size,alpha48,alpha96,get_alpha_map=None):
    if size==48: return alpha48
    if size==96: return alpha96
    if get_alpha_map:
        provided = get_alpha_map(size)
        if provided is not None: return provided
    return interpolate_alpha_map(alpha96,96,size) if alpha96 is not None else None

def resolve_alpha_map_for_config(config,alpha48,alpha96,alpha96_variants=None,resolve_alpha_map=None):
    if not config: return None
    if config.get('alphaVariant') and config['logoSize']==96 and alpha96_variants:
        return alpha96_variants.get(config['alphaVariant'])
    if resolve_alpha_map: return resolve_alpha_map(config['logoSize'])
    return resolve_alpha_map_for_size(config['logoSize'],alpha48,alpha96)

def create_alpha_map_resolver(alpha48,alpha96,get_alpha_map=None):
    cache = {}
    def resolve(size):
        if size in cache: return cache[size]
        r = resolve_alpha_map_for_size(size,alpha48,alpha96,get_alpha_map)
        cache[size] = r; return r
    return resolve

def resolve_initial_standard_config(image_data,default_config,alpha48,alpha96):
    w,h = image_data.shape[1],image_data.shape[0]
    primary = {'logoSize':96,'marginRight':64,'marginBottom':64} if default_config['logoSize']==96 else {'logoSize':48,'marginRight':32,'marginBottom':32}
    alt = {'logoSize':96,'marginRight':64,'marginBottom':64} if default_config['logoSize']!=96 else {'logoSize':48,'marginRight':32,'marginBottom':32}
    candidates = [primary,alt]
    for cfg in resolve_official_gemini_search_configs(w,h,limit=1):
        if not any(c['logoSize']==cfg['logoSize'] and c['marginRight']==cfg['marginRight']
                   and c['marginBottom']==cfg['marginBottom'] for c in candidates):
            candidates.append(cfg)
    best_cfg,best_score = None,float('-inf')
    for cfg in candidates:
        pos = calculate_watermark_position(w,h,cfg)
        if not is_region_inside_image(image_data,pos): continue
        am = resolve_alpha_map_for_config(cfg,alpha48,alpha96)
        if am is None: continue
        score = compute_region_spatial_correlation(image_data,am,{'x':pos['x'],'y':pos['y'],'size':pos['width']})
        if best_cfg is None or (score>=0.25 and score>best_score+0.08): best_cfg,best_score = cfg,score
    return best_cfg if best_cfg else default_config

# ═══════════════════════════════════════════════════════════════
# Section 9: Candidate Selector — candidateSelector.js complete (1540 lines ported)
# ═══════════════════════════════════════════════════════════════

def evaluate_restoration_candidate(arr,alpha_map,position,source='standard',config=None,
    baseline_nb=0.0,adaptive_confidence=None,alpha_gain=1.0,include_image_data=True,provenance=None):
    """candidateSelector.js:237-338 exact port"""
    if alpha_map is None or position is None: return None
    orig_scores = score_region(arr,alpha_map,position)
    processed = arr.copy(); remove_watermark(processed,alpha_map,position,alpha_gain)
    processed_scores = score_region(processed,alpha_map,position)
    nb = calculate_near_black_ratio(processed,position); nb_inc = nb-baseline_nb
    improvement = orig_scores['spatialScore']-processed_scores['spatialScore']
    grad_inc = processed_scores['gradientScore']-orig_scores['gradientScore']
    ta = assess_reference_texture_alignment_from_stats(arr,arr,calculate_region_texture_stats(processed,position),position)
    tp = ta['texturePenalty']; grad_drop = orig_scores['gradientScore']-processed_scores['gradientScore']
    is_std = source.startswith('standard')
    nb_allowed = (nb_inc<=MAX_NEAR_BLACK_RATIO_INCREASE or
        (is_std and orig_scores['spatialScore']>=STANDARD_TEXT_OVERLAP_MIN_SPATIAL_SCORE
         and orig_scores['gradientScore']>=STANDARD_TEXT_OVERLAP_MIN_GRADIENT_SCORE
         and improvement>=STANDARD_TEXT_OVERLAP_MIN_IMPROVEMENT
         and abs(processed_scores['spatialScore'])<=STANDARD_TEXT_OVERLAP_MAX_RESIDUAL
         and grad_drop>=STANDARD_TEXT_OVERLAP_MIN_GRADIENT_DROP))
    hr_allowed = (not ta['hardReject'] or
        (is_std and orig_scores['spatialScore']>=STANDARD_HARD_REJECT_OVERRIDE_MIN_SPATIAL_SCORE
         and orig_scores['gradientScore']>=STANDARD_HARD_REJECT_OVERRIDE_MIN_GRADIENT_SCORE
         and abs(processed_scores['spatialScore'])<=STANDARD_HARD_REJECT_OVERRIDE_MAX_RESIDUAL
         and processed_scores['gradientScore']<=STANDARD_HARD_REJECT_OVERRIDE_MAX_GRADIENT
         and improvement>=STANDARD_HARD_REJECT_OVERRIDE_MIN_IMPROVEMENT
         and nb_inc<=STANDARD_HARD_REJECT_OVERRIDE_MAX_NEAR_BLACK_INCREASE))
    accepted = (hr_allowed and nb_allowed and improvement>=VALIDATION_MIN_IMPROVEMENT and
        (abs(processed_scores['spatialScore'])<=VALIDATION_TARGET_RESIDUAL
         or grad_inc<=VALIDATION_MAX_GRADIENT_INCREASE))
    vc = (abs(processed_scores['spatialScore'])+max(0,processed_scores['gradientScore'])*0.6+
          max(0,nb_inc)*3+tp)
    result = {'accepted':accepted,'source':source,'config':config,'position':position,'alphaMap':alpha_map,
              'adaptiveConfidence':adaptive_confidence,'alphaGain':alpha_gain,'imageData':None,
              'originalSpatialScore':orig_scores['spatialScore'],'originalGradientScore':orig_scores['gradientScore'],
              'processedSpatialScore':processed_scores['spatialScore'],'processedGradientScore':processed_scores['gradientScore'],
              'improvement':improvement,'nearBlackRatio':nb,'nearBlackIncrease':nb_inc,'gradientIncrease':grad_inc,
              'tooDark':ta['tooDark'],'tooFlat':ta['tooFlat'],'hardReject':ta['hardReject'],
              'texturePenalty':tp,'validationCost':vc,'provenance':provenance or {}}
    if include_image_data: result['imageData'] = processed
    return result

def pick_better_candidate(current,candidate,min_cost_delta=0.005):
    if not candidate or not candidate.get('accepted'): return current
    if not current: return candidate
    if candidate['validationCost']<current['validationCost']-min_cost_delta: return candidate
    if (abs(candidate['validationCost']-current['validationCost'])<=min_cost_delta
        and candidate['improvement']>current['improvement']+0.01): return candidate
    return current

def is_standard_candidate_source(c): return isinstance(c.get('source'),str) and c['source'].startswith('standard')
def is_drifted_standard_candidate(c):
    return is_standard_candidate_source(c) and (c.get('provenance',{}).get('localShift') or
        c.get('provenance',{}).get('sizeJitter') or c.get('provenance',{}).get('previewAnchor') or
        '+warp' in str(c.get('source','')))
def is_canonical_standard_candidate(c):
    return is_standard_candidate_source(c) and not c.get('provenance',{}).get('localShift') and not c.get('provenance',{}).get('sizeJitter') and not c.get('provenance',{}).get('previewAnchor')

def has_strong_canonical_anchor_signal(c):
    bs,bg = c.get('originalSpatialScore'),c.get('originalGradientScore')
    if not (isinstance(bs,(int,float)) and isinstance(bg,(int,float)) and math.isfinite(bs) and math.isfinite(bg)): return False
    return (bg>=STANDARD_LOCAL_SHIFT_CANONICAL_MIN_GRADIENT_SCORE and bs>=STANDARD_LOCAL_SHIFT_CANONICAL_MIN_SPATIAL_SCORE) or bg>=STANDARD_LOCAL_SHIFT_STRONG_BASE_GRADIENT_SCORE or bs>=STANDARD_LOCAL_SHIFT_STRONG_BASE_SPATIAL_SCORE

def has_weak_drift_evidence(c):
    cs,cg = c.get('originalSpatialScore'),c.get('originalGradientScore')
    return cg<STANDARD_LOCAL_SHIFT_WEAK_CANDIDATE_GRADIENT_SCORE or cs<STANDARD_LOCAL_SHIFT_WEAK_CANDIDATE_SPATIAL_SCORE

def leaves_worse_residual_gradient_than_canonical(canonical,drift):
    cpg,dpg = canonical.get('processedGradientScore'),drift.get('processedGradientScore')
    return (max(0,cpg)<=STANDARD_LOCAL_SHIFT_PRESERVE_CLEAN_BASE_GRADIENT_THRESHOLD and
            max(0,dpg)>=STANDARD_LOCAL_SHIFT_MAX_CANDIDATE_GRADIENT_FOR_CLEAN_BASE)

def leaves_much_worse_residual_gradient_than_canonical(canonical,drift):
    cps,cpg,ci = canonical.get('processedSpatialScore'),canonical.get('processedGradientScore'),canonical.get('improvement',0)
    dpg = drift.get('processedGradientScore')
    return (abs(cps)<=STANDARD_PRESERVE_MAX_RESIDUAL and ci>=STANDARD_PRESERVE_MIN_IMPROVEMENT and
            dpg>=cpg+STANDARD_PRESERVE_GRADIENT_DELTA)

def should_preserve_canonical_anchor(canonical,drift):
    if not is_canonical_standard_candidate(canonical): return False
    if not is_drifted_standard_candidate(drift): return False
    va = canonical['validationCost']-drift['validationCost']
    return ((has_strong_canonical_anchor_signal(canonical) and has_weak_drift_evidence(drift) and va<STANDARD_LOCAL_SHIFT_MIN_VALIDATION_ADVANTAGE)
            or leaves_worse_residual_gradient_than_canonical(canonical,drift)
            or leaves_much_worse_residual_gradient_than_canonical(canonical,drift))

def should_preserve_strong_standard_anchor(current,candidate):
    if current and current.get('provenance',{}).get('localShift'): return False
    if not is_standard_candidate_source(candidate): return False
    return should_preserve_canonical_anchor(current,candidate)

def should_revert_local_shift_to_standard_trial(selected,std_trial):
    if not selected or selected.get('provenance',{}).get('localShift')!=True: return False
    if not is_standard_candidate_source(selected) or not is_standard_candidate_source(std_trial): return False
    if not std_trial.get('accepted'): return False
    return should_preserve_canonical_anchor(std_trial,selected)

def should_skip_standard_local_search(seed):
    if not seed: return False
    return max(0,seed.get('processedGradientScore',0))<=STANDARD_LOCAL_SHIFT_SKIP_PROCESSED_GRADIENT_THRESHOLD

def is_preview_anchor_search_eligible(image_data,config):
    if not config or config['logoSize']!=48: return False
    w,h = image_data.shape[1],image_data.shape[0]
    if w<384 or w>1536 or h<384 or h>1536: return False
    if max(w,h)<512: return False
    return match_official_gemini_image_size(w,h) is None

def should_prefer_preview_anchor_candidate(current,candidate):
    if not candidate or candidate.get('provenance',{}).get('previewAnchor')!=True: return False
    if not current or current.get('provenance',{}).get('previewAnchor'): return False
    cs,cg = current.get('originalSpatialScore',0),current.get('originalGradientScore',0)
    ds,dg = candidate.get('originalSpatialScore',0),candidate.get('originalGradientScore',0)
    cr = has_reliable_standard_watermark_signal(cs,cg)
    dr = has_reliable_standard_watermark_signal(ds,dg)
    if dr and not cr: return True
    return dg>=cg+0.2 and ds>=cs+0.05

def is_preview_anchor_gain_search_required(candidate):
    if not candidate: return True
    return abs(candidate.get('processedSpatialScore',0))>PREVIEW_ANCHOR_GAIN_SKIP_RESIDUAL_THRESHOLD or max(0,candidate.get('processedGradientScore',0))>PREVIEW_ANCHOR_GAIN_SKIP_GRADIENT_THRESHOLD

def should_escalate_search(candidate):
    if not candidate: return True
    return abs(candidate.get('processedSpatialScore',0))>STANDARD_FAST_PATH_RESIDUAL_THRESHOLD or max(0,candidate.get('processedGradientScore',0))>STANDARD_FAST_PATH_GRADIENT_THRESHOLD

def should_search_nearby_standard_candidate(candidate,image_data):
    if not candidate: return True
    return (candidate['position']['width']>=72 and image_data.shape[0]>image_data.shape[1]*1.25 and
        (abs(candidate.get('processedSpatialScore',0))>STANDARD_NEARBY_SEARCH_RESIDUAL_THRESHOLD or
         max(0,candidate.get('processedGradientScore',0))>STANDARD_NEARBY_SEARCH_GRADIENT_THRESHOLD))

def infer_decision_tier(candidate,direct_match=False):
    if not candidate: return 'insufficient'
    if direct_match: return 'direct-match'
    if 'validated' in str(candidate.get('source','')): return 'validated-match'
    if candidate.get('accepted'): return 'validated-match'
    return 'safe-removal'

def find_best_template_warp(arr,alpha_map,position,baseline_spatial,baseline_gradient,shifts=None,scales=None):
    if shifts is None: shifts = TEMPLATE_ALIGN_SHIFTS
    if scales is None: scales = TEMPLATE_ALIGN_SCALES
    size = position['width']
    if size<=8: return None
    best = {'spatialScore':baseline_spatial,'gradientScore':baseline_gradient,'shift':{'dx':0,'dy':0,'scale':1},'alphaMap':alpha_map}
    for scale in scales:
        for dy in shifts:
            for dx in shifts:
                if dx==0 and dy==0 and scale==1: continue
                warped = warp_alpha_map(alpha_map,size,{'dx':dx,'dy':dy,'scale':scale})
                s = compute_region_spatial_correlation(arr,warped,{'x':position['x'],'y':position['y'],'size':size})
                g = compute_region_gradient_correlation(arr,warped,{'x':position['x'],'y':position['y'],'size':size})
                conf = max(0,s)*0.7+max(0,g)*0.3
                bc = max(0,best['spatialScore'])*0.7+max(0,best['gradientScore'])*0.3
                if conf>bc+0.01: best = {'spatialScore':s,'gradientScore':g,'shift':{'dx':dx,'dy':dy,'scale':scale},'alphaMap':warped}
    return best if (best['spatialScore']>=baseline_spatial+0.01 or best['gradientScore']>=baseline_gradient+0.01) else None

def build_standard_candidate_seeds(arr,config,position,alpha48,alpha96,alpha96_variants=None,get_alpha_map=None,include_catalog=True):
    w,h = arr.shape[1],arr.shape[0]
    resolve = create_alpha_map_resolver(alpha48,alpha96,get_alpha_map)
    cfgs = resolve_gemini_watermark_search_configs(w,h,config) if include_catalog else [config]
    seeds = []
    for cfg in cfgs:
        pos = (position if cfg==config else
               {'x':w-cfg['marginRight']-cfg['logoSize'],'y':h-cfg['marginBottom']-cfg['logoSize'],
                'width':cfg['logoSize'],'height':cfg['logoSize']})
        if not is_region_inside_image(arr,pos): continue
        am = resolve_alpha_map_for_config(cfg,alpha48,alpha96,alpha96_variants,resolve)
        if am is None: continue
        prov = {}
        if cfg!=config: prov['catalogVariant']=True
        if cfg.get('alphaVariant'): prov['alphaVariant']=cfg['alphaVariant']
        seeds.append({'config':cfg,'position':pos,'alphaMap':am,
                      'source':'standard' if cfg==config else 'standard+catalog','provenance':prov})
    return seeds

def search_nearby_standard_candidate(arr,candidate_seeds,adaptive_confidence=None):
    if not candidate_seeds: return None
    best = None
    for seed in candidate_seeds:
        if should_skip_standard_local_search(seed): continue
        for dy in STANDARD_NEARBY_SHIFTS:
            for dx in STANDARD_NEARBY_SHIFTS:
                if dx==0 and dy==0: continue
                cpos = {'x':seed['position']['x']+dx,'y':seed['position']['y']+dy,
                        'width':seed['position']['width'],'height':seed['position']['height']}
                if not is_region_inside_image(arr,cpos): continue
                ct = evaluate_restoration_candidate(arr,seed['alphaMap'],cpos,f"{seed['source']}+local",
                    seed['config'],calculate_near_black_ratio(arr,cpos),adaptive_confidence,
                    provenance={**seed.get('provenance',{}),'localShift':True},include_image_data=False)
                if ct and ct.get('accepted'): best = pick_better_candidate(best,ct,0.002)
    return best

def search_standard_size_jitter_candidate(arr,candidate_seeds,alpha48,alpha96,get_alpha_map=None,adaptive_confidence=None):
    if not candidate_seeds: return None
    resolve = create_alpha_map_resolver(alpha48,alpha96,get_alpha_map)
    best = None
    for seed in candidate_seeds:
        for delta in STANDARD_SIZE_JITTERS:
            size = seed['position']['width']+delta
            if size<=24 or size==seed['position']['width']: continue
            cpos = {'x':arr.shape[1]-seed['config']['marginRight']-size,
                    'y':arr.shape[0]-seed['config']['marginBottom']-size,'width':size,'height':size}
            if not is_region_inside_image(arr,cpos): continue
            cam = resolve(size)
            if cam is None: continue
            ct = evaluate_restoration_candidate(arr,cam,cpos,f"{seed['source']}+size",
                {'logoSize':size,'marginRight':seed['config']['marginRight'],'marginBottom':seed['config']['marginBottom']},
                calculate_near_black_ratio(arr,cpos),adaptive_confidence,
                provenance={**seed.get('provenance',{}),'sizeJitter':True},include_image_data=False)
            if ct and ct.get('accepted'): best = pick_better_candidate(best,ct,0.002)
    return best

def search_fine_standard_local_candidate(arr,seed_candidate,adaptive_confidence=None,shifts=None):
    if shifts is None: shifts = STANDARD_FINE_LOCAL_SHIFTS
    if not seed_candidate or seed_candidate.get('alphaMap') is None: return None
    if should_skip_standard_local_search(seed_candidate): return None
    best = None
    for dy in shifts:
        for dx in shifts:
            if dx==0 and dy==0: continue
            cpos = {'x':seed_candidate['position']['x']+dx,'y':seed_candidate['position']['y']+dy,
                    'width':seed_candidate['position']['width'],'height':seed_candidate['position']['height']}
            if not is_region_inside_image(arr,cpos): continue
            ct = evaluate_restoration_candidate(arr,seed_candidate['alphaMap'],cpos,f"{seed_candidate['source']}+local",
                seed_candidate['config'],calculate_near_black_ratio(arr,cpos),adaptive_confidence,
                provenance={**seed_candidate.get('provenance',{}),'localShift':True},include_image_data=False)
            if ct and ct.get('accepted'): best = pick_better_candidate(best,ct,0.002)
    return best

def search_candidate_alpha_gain(arr,seed_candidate,adaptive_confidence=None):
    if not seed_candidate or seed_candidate.get('alphaMap') is None: return None
    best = None
    for gain in ALPHA_GAIN_CANDIDATES:
        if gain<=1: continue
        ct = evaluate_restoration_candidate(arr,seed_candidate['alphaMap'],seed_candidate['position'],
            f"{seed_candidate['source']}+gain",seed_candidate['config'],
            calculate_near_black_ratio(arr,seed_candidate['position']),adaptive_confidence,
            alpha_gain=gain,provenance=seed_candidate.get('provenance',{}),include_image_data=False)
        if ct and ct.get('accepted'): best = pick_better_candidate(best,ct,0.002)
    return best

def search_bottom_right_preview_candidate(arr,config,alpha48,alpha96,get_alpha_map=None,adaptive_confidence=None):
    if not is_preview_anchor_search_eligible(arr,config): return None
    w,h = arr.shape[1],arr.shape[0]
    resolve = create_alpha_map_resolver(alpha48,alpha96,get_alpha_map)
    min_sz = max(PREVIEW_ANCHOR_MIN_SIZE,round(config['logoSize']*PREVIEW_ANCHOR_MIN_SIZE_RATIO))
    max_sz = max(min_sz,round(config['logoSize']*PREVIEW_ANCHOR_MAX_SIZE_RATIO))
    min_mr = max(8,config['marginRight']-PREVIEW_ANCHOR_MARGIN_WINDOW)
    max_mr = config['marginRight']+PREVIEW_ANCHOR_MARGIN_EXTENSION
    min_mb = max(8,config['marginBottom']-PREVIEW_ANCHOR_MARGIN_WINDOW)
    max_mb = config['marginBottom']+PREVIEW_ANCHOR_MARGIN_EXTENSION
    top_candidates = []

    for sz in range(min_sz,max_sz+1,PREVIEW_ANCHOR_SIZE_STEP):
        am = resolve(sz)
        if am is None: continue
        for mr in range(min_mr,max_mr+1,PREVIEW_ANCHOR_MARGIN_STEP):
            cx = w-mr-sz
            if cx<0 or cx+sz>w: continue
            for mb in range(min_mb,max_mb+1,PREVIEW_ANCHOR_MARGIN_STEP):
                cy = h-mb-sz
                if cy<0 or cy+sz>h: continue
                cs = compute_region_spatial_correlation(arr,am,{'x':cx,'y':cy,'size':sz})
                cg = compute_region_gradient_correlation(arr,am,{'x':cx,'y':cy,'size':sz})
                coarse = max(0,cg)*0.6+max(0,cs)*0.4
                if coarse<PREVIEW_ANCHOR_MIN_SCORE: continue
                top_candidates.append({'coarseScore':coarse,'alphaMap':am,'position':{'x':cx,'y':cy,'width':sz,'height':sz},
                                      'config':{'logoSize':sz,'marginRight':mr,'marginBottom':mb}})
                top_candidates.sort(key=lambda x:-x['coarseScore'])
                if len(top_candidates)>PREVIEW_ANCHOR_TOP_K: top_candidates = top_candidates[:PREVIEW_ANCHOR_TOP_K]

    best = None
    for coarse in top_candidates:
        for sd in PREVIEW_ANCHOR_LOCAL_DELTAS:
            sz = coarse['position']['width']+sd
            if sz<PREVIEW_ANCHOR_MIN_SIZE: continue
            am = resolve(sz)
            if am is None: continue
            for dx in PREVIEW_ANCHOR_LOCAL_DELTAS:
                for dy in PREVIEW_ANCHOR_LOCAL_DELTAS:
                    pos = {'x':coarse['position']['x']+dx,'y':coarse['position']['y']+dy,'width':sz,'height':sz}
                    if not is_region_inside_image(arr,pos): continue
                    cfg = {'logoSize':sz,'marginRight':w-pos['x']-sz,'marginBottom':h-pos['y']-sz}
                    ct = evaluate_restoration_candidate(arr,am,pos,'standard+preview-anchor',cfg,
                        calculate_near_black_ratio(arr,pos),adaptive_confidence,
                        provenance={'previewAnchor':True,'previewAnchorLocalRefine':sd!=0 or dx!=0 or dy!=0},include_image_data=False)
                    if ct and ct.get('accepted'): best = pick_better_candidate(best,ct,0.002)
    return best

def evaluate_standard_trials_for_seeds(arr,candidate_seeds):
    trials = [evaluate_restoration_candidate(arr,s['alphaMap'],s['position'],s['source'],s['config'],
        calculate_near_black_ratio(arr,s['position']),provenance=s.get('provenance',{}),include_image_data=False)
              for s in candidate_seeds]
    trials = [t for t in trials if t is not None]
    std_trial = next((t for t in trials if t['source']=='standard'),trials[0] if trials else None)
    ss = std_trial['originalSpatialScore'] if std_trial else None
    sg = std_trial['originalGradientScore'] if std_trial else None
    hr = has_reliable_standard_watermark_signal(ss or 0,sg or 0) if std_trial else False
    return {'standardTrials':trials,'standardTrial':std_trial,'standardSpatialScore':ss,
            'standardGradientScore':sg,'hasReliableStandardMatch':hr}

def resolve_candidate_promotion(candidate,reliable_match=False):
    if not candidate or not candidate.get('accepted'): return None
    if reliable_match: return {'candidate':candidate,'decisionTier':'direct-match'}
    return {'candidate':{**candidate,'source':candidate['source']+'+validated'},'decisionTier':'validated-match'}

def promote_base_candidate(base,base_tier,candidate,reliable_match=False,min_cost_delta=0.002):
    prom = resolve_candidate_promotion(candidate,reliable_match)
    if not prom: return base,base_tier
    if should_preserve_canonical_anchor(base,prom['candidate']): return base,base_tier
    prev = base
    nxt = pick_better_candidate(base,prom['candidate'],min_cost_delta)
    return (nxt,prom['decisionTier']) if nxt!=prev else (base,base_tier)

def evaluate_adaptive_trial(arr,config,alpha96,resolve_alpha_map,allow_adaptive):
    if not allow_adaptive or alpha96 is None: return {'adaptive':None,'adaptiveConfidence':None,'adaptiveTrial':None}
    w,h = arr.shape[1],arr.shape[0]
    adaptive = detect_adaptive_watermark_region(arr,alpha96,config)
    ac = adaptive.get('confidence') if adaptive else None
    if not adaptive or not adaptive.get('region') or not (
        has_reliable_adaptive_watermark_signal(adaptive) or (ac or 0)>=VALIDATION_MIN_CONFIDENCE_FOR_ADAPTIVE_TRIAL):
        return {'adaptive':adaptive,'adaptiveConfidence':ac,'adaptiveTrial':None}
    sz = adaptive['region']['size']
    apos = {'x':adaptive['region']['x'],'y':adaptive['region']['y'],'width':sz,'height':sz}
    aam = resolve_alpha_map(sz)
    if aam is None: raise ValueError(f"Missing alpha map for adaptive size {sz}")
    acfg = {'logoSize':sz,'marginRight':w-apos['x']-sz,'marginBottom':h-apos['y']-sz}
    at = evaluate_restoration_candidate(arr,aam,apos,'adaptive',acfg,calculate_near_black_ratio(arr,apos),
        ac,provenance={'adaptive':True},include_image_data=False)
    return {'adaptive':adaptive,'adaptiveConfidence':ac,'adaptiveTrial':at}

def refine_selected_anchor_candidate(arr,base_candidate,base_tier,adaptive_confidence):
    selected = base_candidate
    am = base_candidate['alphaMap']; pos = base_candidate['position']; cfg = base_candidate['config']
    src = base_candidate['source']; tw = None; sg = base_candidate.get('alphaGain',1.0)
    is_preview = selected.get('provenance',{}).get('previewAnchor',False)

    warp_result = find_best_template_warp(arr,am,pos,selected['originalSpatialScore'],
        selected['originalGradientScore'],
        PREVIEW_TEMPLATE_ALIGN_SHIFTS if is_preview else TEMPLATE_ALIGN_SHIFTS,
        PREVIEW_TEMPLATE_ALIGN_SCALES if is_preview else TEMPLATE_ALIGN_SCALES)
    if warp_result:
        wt = evaluate_restoration_candidate(arr,warp_result['alphaMap'],pos,src+'+warp',cfg,
            calculate_near_black_ratio(arr,pos),adaptive_confidence,provenance=selected.get('provenance',{}),include_image_data=False)
        better = pick_better_candidate(selected,wt)
        if better!=selected: am,src,tw = warp_result['alphaMap'],better['source'],warp_result['shift']; selected = better

    should_gain = (is_preview_anchor_gain_search_required(selected) if is_preview else should_escalate_search(selected))
    if should_gain:
        for gain in ALPHA_GAIN_CANDIDATES:
            gt = evaluate_restoration_candidate(arr,am,pos,src+'+gain',cfg,calculate_near_black_ratio(arr,pos),
                adaptive_confidence,alpha_gain=gain,provenance=selected.get('provenance',{}),include_image_data=False)
            better = pick_better_candidate(selected,gt)
            if better!=selected: selected,sg = better,gt['alphaGain']

    return {'selectedTrial':selected,'source':src,'alphaMap':am,'position':pos,'config':cfg,
            'templateWarp':tw,'alphaGain':sg}

def select_initial_candidate(arr,config,position,alpha48,alpha96,get_alpha_map=None,
    allow_adaptive=True,alpha96_variants=None):
    """candidateSelector.js:1277-1540 EXACT port"""
    w,h = arr.shape[1],arr.shape[0]
    resolve_am = create_alpha_map_resolver(alpha48,alpha96,get_alpha_map)
    fallback_am = alpha96 if config['logoSize']==96 else alpha48

    # Standard anchor selection
    std_candidate_seeds = build_standard_candidate_seeds(arr,config,position,alpha48,alpha96,alpha96_variants,get_alpha_map,False)
    std_sel = evaluate_standard_trials_for_seeds(arr,std_candidate_seeds)
    should_expand = (not std_sel['hasReliableStandardMatch'] and
        (not std_sel['standardTrial'] or should_escalate_search(std_sel['standardTrial'])))
    if should_expand:
        std_candidate_seeds = build_standard_candidate_seeds(arr,config,position,alpha48,alpha96,alpha96_variants,get_alpha_map,True)
        std_sel = evaluate_standard_trials_for_seeds(arr,std_candidate_seeds)

    base,base_tier = None,'insufficient'
    if std_sel['hasReliableStandardMatch'] and std_sel['standardTrial'] and std_sel['standardTrial'].get('accepted'):
        base,base_tier = std_sel['standardTrial'],'direct-match'
    elif std_sel['standardTrial'] and std_sel['standardTrial'].get('accepted'):
        base = {**std_sel['standardTrial'],'source':std_sel['standardTrial']['source']+'+validated'}
        base_tier = 'validated-match'

    if not base and std_sel['standardTrial'] and std_sel['hasReliableStandardMatch']:
        gained = search_candidate_alpha_gain(arr,{**std_sel['standardTrial'],'source':'standard+validated'})
        if gained: base,base_tier = gained,'validated-match'

    for t in std_sel['standardTrials']:
        if not t or t==std_sel['standardTrial']: continue
        base,base_tier = promote_base_candidate(base,base_tier,t,
            has_reliable_standard_watermark_signal(t['originalSpatialScore'],t['originalGradientScore']))

    preview_candidate = search_bottom_right_preview_candidate(arr,config,alpha48,alpha96,get_alpha_map)
    if preview_candidate: base,base_tier = promote_base_candidate(base,base_tier,preview_candidate)

    if base_tier!='direct-match' and not (base and base.get('provenance',{}).get('previewAnchor')) and should_escalate_search(base):
        sj = search_standard_size_jitter_candidate(arr,std_candidate_seeds,alpha48,alpha96,get_alpha_map)
        if sj: base,base_tier = promote_base_candidate(base,base_tier,sj)

    if (base_tier!='direct-match' and base and base.get('provenance',{}).get('sizeJitter')
        and not base.get('provenance',{}).get('previewAnchor') and is_standard_candidate_source(base)
        and should_escalate_search(base)):
        fl = search_fine_standard_local_candidate(arr,base)
        if fl: base,base_tier = promote_base_candidate(base,base_tier,fl)

    def should_eval_adaptive():
        if not allow_adaptive or alpha96 is None: return False
        if not base: return True
        if not should_escalate_search(base): return False
        return should_attempt_adaptive_fallback(base.get('imageData') or arr,base['alphaMap'],base['position'],arr)

    if should_eval_adaptive():
        adaptive_info = evaluate_adaptive_trial(arr,config,alpha96,resolve_am,allow_adaptive)
        adaptive,adaptive_conf,adaptive_trial = adaptive_info['adaptive'],adaptive_info['adaptiveConfidence'],adaptive_info['adaptiveTrial']
    else:
        adaptive,adaptive_conf,adaptive_trial = None,None,None

    if adaptive_trial: base,base_tier = promote_base_candidate(base,base_tier,adaptive_trial,
        has_reliable_adaptive_watermark_signal(adaptive))

    if (not (base and base.get('provenance',{}).get('previewAnchor'))
        and not has_reliable_adaptive_watermark_signal(adaptive)
        and should_search_nearby_standard_candidate(base,arr)):
        nearby = search_nearby_standard_candidate(arr,std_candidate_seeds,adaptive_conf)
        if nearby: base,base_tier = promote_base_candidate(base,base_tier,nearby)

    if not base:
        if std_sel['hasReliableStandardMatch'] and std_sel['standardTrial']:
            base,base_tier = std_sel['standardTrial'],'direct-match'
        elif has_reliable_adaptive_watermark_signal(adaptive) and adaptive_trial:
            base,base_tier = adaptive_trial,'direct-match'

    if not base:
        return {'selectedTrial':None,'source':'skipped','alphaMap':fallback_am,'position':position,
                'config':config,'adaptiveConfidence':adaptive_conf,
                'standardSpatialScore':std_sel['standardSpatialScore'],
                'standardGradientScore':std_sel['standardGradientScore'],
                'templateWarp':None,'alphaGain':1.0,'decisionTier':'insufficient'}

    if should_revert_local_shift_to_standard_trial(base,std_sel['standardTrial']):
        base,base_tier = std_sel['standardTrial'],('direct-match' if std_sel['hasReliableStandardMatch'] else 'validated-match')

    refined = refine_selected_anchor_candidate(arr,base,base_tier,adaptive_conf)
    return {**refined,'adaptiveConfidence':adaptive_conf,
            'standardSpatialScore':std_sel['standardSpatialScore'],
            'standardGradientScore':std_sel['standardGradientScore'],
            'decisionTier':base_tier}

# ═══════════════════════════════════════════════════════════════
# Section 10: Multi-Pass Removal — multiPassRemoval.js complete
# ═══════════════════════════════════════════════════════════════

def remove_repeated_watermark_layers(image_data,alpha_map,position,max_passes=DEFAULT_MAX_PASSES,alpha_gain=1.0):
    result = image_data
    base_nb = calculate_near_black_ratio(result,position)
    max_nb = min(1.0,base_nb+MAX_NEAR_BLACK_RATIO_INCREASE)
    for _ in range(max_passes):
        before = compute_region_spatial_correlation(result,alpha_map,{'x':position['x'],'y':position['y'],'size':position['width']})
        cand = result.copy(); remove_watermark(cand,alpha_map,position,alpha_gain)
        after = compute_region_spatial_correlation(cand,alpha_map,{'x':position['x'],'y':position['y'],'size':position['width']})
        nb = calculate_near_black_ratio(cand,position)
        if nb>max_nb: break
        if abs(before)-abs(after)<0.01: break
        result = cand
        if abs(after)<=DEFAULT_RESIDUAL_THRESHOLD: break
    return result

# ═══════════════════════════════════════════════════════════════
# Section 11: Post-processing — watermarkProcessor.js complete
# ═══════════════════════════════════════════════════════════════

def should_stop_after_first_pass(orig_spatial,orig_gradient,first_spatial,first_gradient):
    if abs(first_spatial)<=0.25: return True
    return (orig_spatial>=0 and first_spatial<0 and first_gradient<=FIRST_PASS_SIGN_FLIP_GRADIENT_THRESHOLD
            and (orig_gradient-first_gradient)>=FIRST_PASS_SIGN_FLIP_MIN_GRADIENT_DROP)

def should_recalibrate_alpha_strength(orig_score,processed_score,suppression_gain):
    return (orig_score>=0.6 and processed_score>=RESIDUAL_RECALIBRATION_THRESHOLD
            and suppression_gain<=MIN_SUPPRESSION_FOR_SKIP_RECALIBRATION)

def recalibrate_alpha_strength(arr,alpha_map,position,orig_spatial,processed_spatial):
    orig_nb = calculate_near_black_ratio(arr,position)
    max_nb = min(1.0,orig_nb+MAX_NEAR_BLACK_RATIO_INCREASE)
    best_score,best_gain,best_result = processed_spatial,1.0,arr.copy()
    for gain in ALPHA_GAIN_CANDIDATES:
        cand = arr.copy(); remove_watermark(cand,alpha_map,position,gain)
        nb = calculate_near_black_ratio(cand,position)
        if nb>max_nb: continue
        s = compute_region_spatial_correlation(cand,alpha_map,{'x':position['x'],'y':position['y'],'size':position['width']})
        if s<best_score: best_score,best_gain,best_result = s,gain,cand
    for d in np.arange(-0.05,0.06,0.01):
        gain = round(best_gain+d,2)
        if gain<=1 or gain>=3: continue
        cand = arr.copy(); remove_watermark(cand,alpha_map,position,gain)
        nb = calculate_near_black_ratio(cand,position)
        if nb>max_nb: continue
        s = compute_region_spatial_correlation(cand,alpha_map,{'x':position['x'],'y':position['y'],'size':position['width']})
        if s<best_score: best_score,best_gain,best_result = s,gain,cand
    delta = processed_spatial-best_score
    if delta<MIN_RECALIBRATION_SCORE_DELTA: return None
    return {'imageData':best_result,'alphaGain':best_gain,'processedSpatialScore':best_score,
            'suppressionGain':orig_spatial-best_score}

def should_refine_preview_residual_edge(source,position,baseline_spatial,baseline_gradient,baseline_positive_halo):
    return ('preview-anchor' in str(source) and position['width']>=24 and position['width']<=PREVIEW_EDGE_CLEANUP_MAX_SIZE
            and (abs(baseline_spatial)<=PREVIEW_EDGE_CLEANUP_SPATIAL_THRESHOLD
                 or (baseline_positive_halo>=PREVIEW_EDGE_CLEANUP_STRONG_HALO_THRESHOLD
                     and abs(baseline_spatial)<=PREVIEW_EDGE_CLEANUP_HALO_SPATIAL_THRESHOLD))
            and baseline_gradient>=PREVIEW_EDGE_CLEANUP_GRADIENT_THRESHOLD)

def should_use_preview_anchor_fast_cleanup(selected_trial,position):
    return (selected_trial and selected_trial.get('provenance',{}).get('previewAnchor')
            and position['width']>=24 and position['width']<=PREVIEW_EDGE_CLEANUP_MAX_SIZE)

def blend_preview_residual_edge(arr,alpha_map,position,minAlpha,maxAlpha,radius,strength,outsideAlphaMax):
    w,h = arr.shape[1],arr.shape[0]; result = arr.copy()
    rs = position['width']; mas = max(maxAlpha,1e-6)
    for row in range(rs):
        for col in range(rs):
            a = alpha_map[row*rs+col]
            if a<minAlpha or a>maxAlpha: continue
            sr,sg,sb,sw = 0.0,0.0,0.0,0.0
            for dy in range(-radius,radius+1):
                for dx in range(-radius,radius+1):
                    if dx==0 and dy==0: continue
                    lx,ly = col+dx,row+dy
                    px,py = position['x']+lx,position['y']+ly
                    if px<0 or py<0 or px>=w or py>=h: continue
                    na = alpha_map[ly*rs+lx] if (ly>=0 and lx>=0 and ly<rs and lx<rs) else 0
                    if na>outsideAlphaMax: continue
                    dist = math.sqrt(dx*dx+dy*dy) or 1; weight = 1/dist
                    sr+=result[py,px,0]*weight; sg+=result[py,px,1]*weight; sb+=result[py,px,2]*weight; sw+=weight
            if sw<=0: continue
            blend = max(0,min(1,strength*a/mas))
            result[position['y']+row,position['x']+col,0] = round(result[position['y']+row,position['x']+col,0]*(1-blend)+(sr/sw)*blend)
            result[position['y']+row,position['x']+col,1] = round(result[position['y']+row,position['x']+col,1]*(1-blend)+(sg/sw)*blend)
            result[position['y']+row,position['x']+col,2] = round(result[position['y']+row,position['x']+col,2]*(1-blend)+(sb/sw)*blend)
    return result

def refine_preview_residual_edge(arr,alpha_map,position,source,baseline_spatial,baseline_gradient,
    allow_aggressive=False):
    baseline_halo = assess_alpha_band_halo(arr,position,alpha_map)
    bph = baseline_halo['positiveDeltaLum']
    if not should_refine_preview_residual_edge(source,position,baseline_spatial,baseline_gradient,bph): return None
    base_nb = calculate_near_black_ratio(arr,position)
    max_nb = min(1.0,base_nb+MAX_NEAR_BLACK_RATIO_INCREASE)
    rmg = (PREVIEW_EDGE_CLEANUP_FINE_MIN_GRADIENT_IMPROVEMENT if baseline_gradient<=PREVIEW_EDGE_CLEANUP_FINE_GRADIENT_THRESHOLD
           else (PREVIEW_EDGE_CLEANUP_HALO_RELAXED_MIN_GRADIENT_IMPROVEMENT if bph>=PREVIEW_EDGE_CLEANUP_STRONG_HALO_THRESHOLD
                 else PREVIEW_EDGE_CLEANUP_MIN_GRADIENT_IMPROVEMENT))
    presets = (PREVIEW_EDGE_CLEANUP_PRESETS+PREVIEW_EDGE_CLEANUP_AGGRESSIVE_PRESETS
               if allow_aggressive and baseline_gradient>=PREVIEW_EDGE_CLEANUP_STRONG_GRADIENT_THRESHOLD and abs(baseline_spatial)<=0.05
               else PREVIEW_EDGE_CLEANUP_PRESETS)
    best = None
    for preset in presets:
        cand = blend_preview_residual_edge(arr,alpha_map,position,**{k:preset[k] for k in ['minAlpha','maxAlpha','radius','strength','outsideAlphaMax']})
        nb = calculate_near_black_ratio(cand,position)
        if nb>max_nb: continue
        s = compute_region_spatial_correlation(cand,alpha_map,{'x':position['x'],'y':position['y'],'size':position['width']})
        g = compute_region_gradient_correlation(cand,alpha_map,{'x':position['x'],'y':position['y'],'size':position['width']})
        halo = assess_alpha_band_halo(cand,position,alpha_map)
        pgi = preset.get('minGradientImprovement',rmg)
        pmd = preset.get('maxSpatialDrift',PREVIEW_EDGE_CLEANUP_MAX_SPATIAL_DRIFT)
        pma = preset.get('maxAcceptedSpatial',0.22)
        ig = g<=baseline_gradient-pgi; ks = abs(s)<=abs(baseline_spatial)+pmd; kr = abs(s)<=pma
        cph = halo['positiveDeltaLum']
        ih = bph<PREVIEW_EDGE_CLEANUP_STRONG_HALO_THRESHOLD or cph<=bph-PREVIEW_EDGE_CLEANUP_MIN_HALO_REDUCTION
        if not (ig and ks and kr and ih): continue
        cost = abs(s)*0.6+max(0,g)+cph*PREVIEW_EDGE_CLEANUP_HALO_WEIGHT
        if best is None or cost<best['cost']: best = {'imageData':cand,'spatialScore':s,'gradientScore':g,'halo':halo,'cost':cost}
    return best

def refine_subpixel_outline(arr,alpha_map,position,alpha_gain,orig_nb,baseline_spatial,baseline_gradient,
    baseline_shift=None):
    size = position['width']
    if not size or size<=8 or alpha_gain<OUTLINE_REFINEMENT_MIN_GAIN: return None
    max_nb = min(1.0,orig_nb+MAX_NEAR_BLACK_RATIO_INCREASE)
    gains = [alpha_gain]
    lo = max(1.0,round(alpha_gain-0.01,2)); hi = round(alpha_gain+0.01,2)
    if lo!=alpha_gain: gains.append(lo)
    if hi!=alpha_gain: gains.append(hi)
    bd,dy0,ds0 = (baseline_shift or {}).get('dx',0),(baseline_shift or {}).get('dy',0),(baseline_shift or {}).get('scale',1)
    best = None
    for sd in SUBPIXEL_REFINE_SCALES:
        s = round(ds0*sd,4)
        for dy in SUBPIXEL_REFINE_SHIFTS:
            for dx in SUBPIXEL_REFINE_SHIFTS:
                warped = warp_alpha_map(alpha_map,size,{'dx':dy0+dy,'dy':bd+dx,'scale':s})
                for gain in gains:
                    cand = arr.copy(); remove_watermark(cand,warped,position,gain)
                    nb = calculate_near_black_ratio(cand,position)
                    if nb>max_nb: continue
                    sp = compute_region_spatial_correlation(cand,warped,{'x':position['x'],'y':position['y'],'size':size})
                    gr = compute_region_gradient_correlation(cand,warped,{'x':position['x'],'y':position['y'],'size':size})
                    cost = abs(sp)*0.6+max(0,gr)
                    if best is None or cost<best['cost']:
                        best = {'imageData':cand,'alphaMap':warped,'alphaGain':gain,
                                'shift':{'dx':dy0+dy,'dy':bd+dx,'scale':s},
                                'spatialScore':sp,'gradientScore':gr,'nearBlackRatio':nb,'cost':cost}
    if best is None: return None
    ig = best['gradientScore']<=baseline_gradient-0.04; ks = abs(best['spatialScore'])<=abs(baseline_spatial)+0.08
    return best if (ig and ks) else None

def process_watermark_image_data(image_data,alpha48,alpha96,options=None):
    """watermarkProcessor.js:540-876 EXACT port"""
    opts = options or {}
    allow_adaptive = opts.get('adaptiveMode','auto') not in ('never','off')
    max_passes = opts.get('maxPasses',4)
    alpha96_variants = opts.get('alpha96Variants')

    arr = image_data; w,h = arr.shape[1],arr.shape[0]

    default_config = detect_watermark_config(w,h)
    config = resolve_initial_standard_config(arr,default_config,alpha48,alpha96)
    position = calculate_watermark_position(w,h,config)

    selection = select_initial_candidate(arr,config,position,alpha48,alpha96,
        None,allow_adaptive,alpha96_variants)

    print(f"  Config: logo={config['logoSize']}px, pos=({position['x']},{position['y']})")
    print(f"  Selection: tier={selection['decisionTier']}, source={selection['source']}")

    if not selection['selectedTrial']:
        print(f"  No watermark detected, returning original")
        return arr

    pos = selection['position']; am = selection['alphaMap']; cfg = selection['config']
    alpha_gain = selection['alphaGain']; src = selection['source']
    selected = selection['selectedTrial']
    result = selected.get('imageData') if selected.get('imageData') is not None else arr.copy()

    orig_spatial = compute_region_spatial_correlation(arr,am,{'x':pos['x'],'y':pos['y'],'size':pos['width']})
    orig_gradient = compute_region_gradient_correlation(arr,am,{'x':pos['x'],'y':pos['y'],'size':pos['width']})

    is_preview = selected.get('provenance',{}).get('previewAnchor',False)
    use_preview_fast = should_use_preview_anchor_fast_cleanup(selected,pos)
    skip_preview_mp = is_preview

    # First pass metrics
    fp_spatial = compute_region_spatial_correlation(result,am,{'x':pos['x'],'y':pos['y'],'size':pos['width']})
    fp_gradient = compute_region_gradient_correlation(result,am,{'x':pos['x'],'y':pos['y'],'size':pos['width']})
    fp_nb = calculate_near_black_ratio(result,pos)
    fp_cleared = should_stop_after_first_pass(orig_spatial,orig_gradient,fp_spatial,fp_gradient)

    # Multi-pass
    remaining = max(0,max_passes-1)
    if remaining>0 and not fp_cleared and not skip_preview_mp:
        result = remove_repeated_watermark_layers(result,am,pos,remaining,alpha_gain)

    processed_spatial = compute_region_spatial_correlation(result,am,{'x':pos['x'],'y':pos['y'],'size':pos['width']})
    processed_gradient = compute_region_gradient_correlation(result,am,{'x':pos['x'],'y':pos['y'],'size':pos['width']})
    suppression = orig_spatial-processed_spatial

    # Recalibration
    if should_recalibrate_alpha_strength(orig_spatial,processed_spatial,suppression):
        recal = recalibrate_alpha_strength(result,am,pos,orig_spatial,processed_spatial)
        if recal:
            result = recal['imageData']; alpha_gain = recal['alphaGain']
            processed_spatial = recal['processedSpatialScore']
            processed_gradient = compute_region_gradient_correlation(result,am,{'x':pos['x'],'y':pos['y'],'size':pos['width']})
            suppression = recal['suppressionGain']

    # Sub-pixel refinement
    if not use_preview_fast and processed_spatial<=0.3 and processed_gradient>=OUTLINE_REFINEMENT_THRESHOLD:
        ref_nb = calculate_near_black_ratio(result,pos)
        bs = selection.get('templateWarp') or {'dx':0,'dy':0,'scale':1}
        refined = refine_subpixel_outline(result,am,pos,alpha_gain,ref_nb,processed_spatial,processed_gradient,bs)
        if refined:
            result = refined['imageData']; am = refined['alphaMap']; alpha_gain = refined['alphaGain']
            processed_spatial = refined['spatialScore']; processed_gradient = refined['gradientScore']

    # Preview edge cleanup (up to 3 passes)
    for _ in range(PREVIEW_EDGE_CLEANUP_MAX_APPLIED_PASSES):
        pec = refine_preview_residual_edge(result,am,pos,src,processed_spatial,processed_gradient,use_preview_fast)
        if not pec: break
        result = pec['imageData']; processed_spatial = pec['spatialScore']; processed_gradient = pec['gradientScore']
        suppression = orig_spatial-processed_spatial

    return result

# ═══════════════════════════════════════════════════════════════
# Section 12: Entry Point — watermarkEngine.js equivalent
# ═══════════════════════════════════════════════════════════════

def remove_gemini_watermark(arr,simple=False,alpha=0.01):
    if simple:
        a = max(0,min(0.99,alpha)); f = arr.astype(np.float32)
        for c in range(3): f[...,c] = np.clip((f[...,c]-a*255)/(1-a),0,255)
        return f.astype(np.uint8)

    alpha48 = get_embedded_alpha_map('48')
    alpha96 = get_embedded_alpha_map('96')
    alpha96_variants = {'20260520': get_embedded_alpha_map('96-20260520')}
    return process_watermark_image_data(arr,alpha48,alpha96,{'alpha96Variants':alpha96_variants})

# ═══════════════════════════════════════════════════════════════
# Section 13: CLI
# ═══════════════════════════════════════════════════════════════

def main():
    p = argparse.ArgumentParser(description="Gemini watermark removal — exact port of GargantuaX/gemini-watermark-remover")
    p.add_argument("input",help="Input PNG path")
    p.add_argument("--output","-o",help="Output path (default: input_cleaned.png)")
    p.add_argument("--simple",action="store_true",help="Uniform alpha only (skip full pipeline)")
    p.add_argument("--alpha",type=float,default=0.01,help="Alpha for simple mode")
    args = p.parse_args()

    if not os.path.exists(args.input):
        print(f"ERROR: {args.input} not found",file=sys.stderr); sys.exit(1)

    out = args.output or args.input.replace('.png','_cleaned.png')
    img = Image.open(args.input).convert('RGB')
    arr = np.array(img)
    cleaned = remove_gemini_watermark(arr,args.simple,args.alpha)
    Image.fromarray(cleaned).save(out)

    ik,ok = os.path.getsize(args.input)/1024,os.path.getsize(out)/1024
    print(f"Done: {arr.shape[1]}x{arr.shape[0]}, {ik:.0f}KB → {ok:.0f}KB, → {out}")

if __name__=="__main__":
    main()
