# Reverse Alpha Blending — Watermark Removal

## Principle

Gemini embeds an invisible watermark as a semi-transparent white overlay:

```
watermarked = α × logo + (1 - α) × original
```

Where:
- `logo` = 255 (white), normalized to 1.0
- `α` ∈ [0, 1] = per-pixel watermark opacity (typically 0.005–0.03)
- `watermarked` = pixel value in the Gemini-generated image
- `original` = true pixel value before watermarking

Reverse solve:

```
original = (watermarked - α × logo) / (1 - α)
```

This is an exact closed-form solution, not an approximation. The accuracy depends solely on having the correct α (alpha map) for each pixel.

## The α Problem

The real Gemini watermark pattern is a specific text/logo with pixel-level α variation. Without the exact alpha map:

- **Too low α** (0.005): no visible effect, watermark remains
- **Optimal α** (0.01–0.02): removes most watermark with minimal artifacts
- **Too high α** (>0.03): over-corrects, damages image

The gemini-watermark-remover project ships pre-calibrated alpha maps for known patterns in `embeddedAlphaMaps.js`. For a general approach, use a conservative uniform α ≈ 0.01.

## Reference Implementation

- Repo: `GargantuaX/gemini-watermark-remover` (4,225 stars)
- Core file: `src/core/blendModes.js` — `removeWatermark()` function
- Alpha maps: `src/core/embeddedAlphaMaps.js` — pre-calibrated pixel arrays
- Alpha detection: `src/core/alphaMap.js` — derives α map from watermark capture

## Limitations

- Uniform α removes only ~70% of the watermark
- Pixel-perfect removal requires the exact alpha map
- The watermark is invisible to the eye — removal is cosmetic, affecting only metadata/forensic detectability
- Works for Gemini Nano Banana 2 / Imagen-generated images; Veo video watermark uses a different pattern
