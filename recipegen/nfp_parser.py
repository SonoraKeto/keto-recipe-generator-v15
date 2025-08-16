from __future__ import annotations
import re, pathlib
from typing import Dict, Any
import pdfplumber
from PIL import Image
import pytesseract

NUM = r'([0-9]+(?:\.[0-9]+)?)'

SERV_RE = re.compile(r'serving\s*size[^0-9]*' + NUM + '\s*g', re.I)
CAL_RE  = re.compile(r'calories[^0-9]*([0-9]+)', re.I)
FAT_RE  = re.compile(r'total\s*fat[^0-9]*' + NUM + '\s*g', re.I)
CARB_RE = re.compile(r'total\s*carbohydrate[^0-9]*' + NUM + '\s*g', re.I)
FIB_RE  = re.compile(r'(dietary\s*fiber|fiber)[^0-9]*' + NUM + '\s*g', re.I)
PROT_RE = re.compile(r'protein[^0-9]*' + NUM + '\s*g', re.I)

def _extract_text_pdf(pdf_path: pathlib.Path) -> str:
    blocks = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            t = page.extract_text() or ""
            blocks.append(t)
    return "\n".join(blocks)

def _extract_text_image(img_path: pathlib.Path) -> str:
    img = Image.open(img_path)
    return pytesseract.image_to_string(img)

def extract_panel_text(path: pathlib.Path) -> str:
    ext = path.suffix.lower()
    if ext == '.pdf':
        return _extract_text_pdf(path)
    elif ext in ('.png','.jpg','.jpeg','.webp'):
        return _extract_text_image(path)
    else:
        raise ValueError(f"Unsupported panel file: {path}")

def parse_nfp_text_to_per100g(text: str) -> Dict[str, Any]:
    def _grab(rx, idx=1, default=None, cast=float):
        m = rx.search(text)
        return cast(m.group(idx)) if m else default
    serving_g = _grab(SERV_RE, default=None)
    calories  = _grab(CAL_RE, default=None, cast=int)
    fat_g     = _grab(FAT_RE)
    carbs_g   = _grab(CARB_RE)
    fiber_g   = _grab(FIB_RE)
    protein_g = _grab(PROT_RE)

    if not serving_g:
        raise ValueError("Could not find serving size (g) in Nutrition Facts panel.")

    def per100(x): return round(x * 100.0 / serving_g, 4) if x is not None else None
    return {'serving_g': serving_g, 'per_100g': {
        'calories': per100(calories),
        'fat_g': per100(fat_g),
        'carbs_g': per100(carbs_g),
        'fiber_g': per100(fiber_g),
        'protein_g': per100(protein_g),
    }}
