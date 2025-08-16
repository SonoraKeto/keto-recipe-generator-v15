from __future__ import annotations
import pathlib
from PIL import Image

def compress_to_webp(src: pathlib.Path, dst: pathlib.Path, max_side=1600, quality=80):
    img = Image.open(src).convert('RGB')
    w, h = img.size
    scale = min(1.0, float(max_side)/max(w,h))
    if scale < 1.0:
        img = img.resize((int(w*scale), int(h*scale)), Image.LANCZOS)
    dst.parent.mkdir(parents=True, exist_ok=True)
    img.save(dst, format='WEBP', quality=80, method=6)
    return dst
