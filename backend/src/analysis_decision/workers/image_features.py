"""Deterministic image feature extraction (Technology Stack §13: Pillow +
OpenCV) feeding the Image Worker's LLM judgment call.

**Flagged limitation:** the Technology Stack's Ollama model selection
(Qwen 3 8B Instruct) is text-only, not multimodal — no vision-capable
model is pinned anywhere in the frozen architecture. Rather than silently
skip Visual Identity evaluation, this extracts objective, deterministic
features (dominant color palette, dimensions, aspect ratio) and gives
the Verbal-capable LLM a *structured textual description* of the image
to judge against Visual Identity Assertions. This is real, working
analysis for color/palette/dimension-shaped Assertions, but cannot judge
genuinely visual-semantic Assertions (logo placement, photography
style/mood) — a documented capability gap, not a silent one. Swapping in
a vision-capable Ollama model (e.g. `llava`) later is an additive change
to `image_worker.py` alone, not an architectural one.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ImageFeatures:
    width: int
    height: int
    aspect_ratio: float
    dominant_colors_hex: list[str]


def extract_image_features(image_bytes: bytes, *, palette_size: int = 5) -> ImageFeatures:
    from PIL import Image

    with Image.open(__import__("io").BytesIO(image_bytes)) as img:
        img = img.convert("RGB")
        width, height = img.size
        quantized = img.quantize(colors=palette_size)
        palette = quantized.getpalette() or []
        color_counts = sorted(quantized.getcolors() or [], key=lambda c: c[0], reverse=True)

        hex_colors: list[str] = []
        for _count, index in color_counts[:palette_size]:
            r, g, b = palette[index * 3 : index * 3 + 3]
            hex_colors.append(f"#{r:02x}{g:02x}{b:02x}")

    return ImageFeatures(
        width=width, height=height, aspect_ratio=round(width / height, 3) if height else 0.0,
        dominant_colors_hex=hex_colors,
    )


def describe_features(features: ImageFeatures) -> str:
    return (
        f"Image dimensions: {features.width}x{features.height}px (aspect ratio {features.aspect_ratio}).\n"
        f"Dominant color palette (most to least prevalent): {', '.join(features.dominant_colors_hex)}."
    )
