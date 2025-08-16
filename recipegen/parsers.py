from __future__ import annotations
import re
import pathlib
import pdfplumber
from typing import List, Dict, Any

# --- Section detection --------------------------------------------------------

ING_START = re.compile(r'^\s*(ingredients?)\s*$', re.I)
STEP_START = re.compile(r'^\s*(instructions?|method|directions)\s*$', re.I)
SERVINGS_RE = re.compile(r'servings?\s*[:\-]\s*([0-9]+)', re.I)

SUBHEADER_HINTS = [
    r'^\s*for\b',                # "For the ..."
    r'^\s*to\s+make\b',         # "To make the ..."
    r':\s*$',                     # trailing colon
    r'\bfilling\b',
    r'\btopping\b',
    r'\bdough\b|\bcrust\b',
]

def looks_like_subheader(line: str) -> bool:
    s = line.strip()
    if not s:
        return True
    if len(s) <= 2:
        return True
    if re.search(r':\s*$', s):
        return True
    # If no digits and matches common heading phrases, treat as subheader
    if not re.search(r'[0-9]', s):
        for rx in SUBHEADER_HINTS:
            if re.search(rx, s, re.I):
                return True
        # Title Case short lines without units => likely a heading
        words = s.split()
        if len(words) <= 7 and all(w[:1].isupper() for w in words if w):
            return True
    return False

# --- PDF helpers --------------------------------------------------------------

def read_pdf_text(pdf_path: pathlib.Path) -> str:
    chunks: List[str] = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            t = page.extract_text() or ""
            t = t.replace('\u2022', '-')  # normalize bullets
            chunks.append(t)
    return "\n".join(chunks)

# --- Ingredient line parsing --------------------------------------------------

ING_LINE_PATTERNS = [
    re.compile(r'^\s*[-•]?\s*(.+?)\s+([0-9]+(?:\.[0-9]+)?)\s*(cups?|cup|c|tablespoons?|tbsp|teaspoons?|tsp|grams?|g|kg)\s*$', re.I),
    re.compile(r'^\s*[-•]?\s*([0-9]+(?:\.[0-9]+)?)\s*(cups?|cup|c|tablespoons?|tbsp|teaspoons?|tsp|grams?|g|kg)\s+(.+?)\s*$', re.I),
    re.compile(r'^\s*[-•]?\s*(.+?)\s*$', re.I),
]

FRACTION_MAP = {
    '¼': 0.25, '½': 0.5, '¾': 0.75,
    '⅐': 1/7, '⅑': 1/9, '⅒': 0.1,
    '⅓': 1/3, '⅔': 2/3,
    '⅕': 0.2, '⅖': 0.4, '⅗': 0.6, '⅘': 0.8,
    '⅙': 1/6, '⅚': 5/6,
    '⅛': 0.125, '⅜': 0.375, '⅝': 0.625, '⅞': 0.875,
}

def _to_float_amount(txt: str):
    txt = txt.strip()
    m = re.match(r'^(\d+)\s+(\d+)/(\d+)$', txt)  # "1 1/2"
    if m:
        whole, num, den = m.groups()
        return float(whole) + (float(num) / float(den))
    m = re.match(r'^(\d+)/(\d+)$', txt)  # "1/2"
    if m:
        num, den = m.groups()
        return float(num) / float(den)
    if len(txt) == 1 and txt in FRACTION_MAP:  # "½"
        return float(FRACTION_MAP[txt])
    try:
        return float(txt)
    except Exception:
        return None

UNIT_RX = r'(cups?|cup|c|tablespoons?|tbsp|teaspoons?|tsp|grams?|g|kg|milliliters?|ml)'

def tolerant_amount_unit_name(line: str):
    """Parse lines like '1/2 tablespoon of vegetable oil' or '1 1/2 cups almond flour'."""
    m = re.match(r'^\s*[-•]?\s*([\d]+(?:\.[\d]+)?(?:\s+[\d]+/[\d]+)?|[\d]+/[\d]+|[¼½¾⅐⅑⅒⅓⅔⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞])\s*' + UNIT_RX + r'(?:\s+of)?\s+(.+?)\s*$', line, re.I)
    if not m:
        return None
    amt_txt, unit, name = m.group(1), m.group(2), m.group(3)
    amt = _to_float_amount(amt_txt)
    if amt is None:
        return None
    return {'name': name.strip(), 'amount': amt, 'unit': unit.lower()}


def tolerant_amount_size_name(line: str):
    # e.g., "1/2 medium onion, chopped" or "2 large eggs"
    m = re.match(r'^\s*[-•]?\s*([\d]+(?:\.[\d]+)?(?:\s+[\d]+/[\d]+)?|[\d]+/[\d]+|[¼½¾⅐⅑⅒⅓⅔⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞])\s*(small|medium|large|clove|each|whole)\s+(.+?)\s*$', line, re.I)
    if not m:
        return None
    amt_txt, size, name = m.group(1), m.group(2), m.group(3)
    amt = _to_float_amount(amt_txt)
    if amt is None:
        return None
    return {'name': name.strip(), 'amount': amt, 'unit': size.lower()}

def parse_ingredient_line(line: str):
    # Prefer tolerant parser first (handles fractions & 'of')
    t = tolerant_amount_size_name(line) or tolerant_amount_unit_name(line)
    if t:
        return t
    for pat in ING_LINE_PATTERNS:
        m = pat.match(line)
        if m:
            groups = [g for g in m.groups() if g is not None]
            # Skip free-text headings
            if pat.pattern.startswith('^\s*[-•]?\s*(.+?)\s*$') and looks_like_subheader(line):
                return None
            if len(groups) == 3:
                if groups[0].replace('.', '', 1).isdigit():
                    amount = float(groups[0]); unit = groups[1]; name = groups[2]
                elif groups[1].replace('.', '', 1).isdigit():
                    name = groups[0]; amount = float(groups[1]); unit = groups[2]
                else:
                    name = groups[0]; amount = None; unit = None
            elif len(groups) == 1:
                name = groups[0]; amount = None; unit = None
            else:
                name = groups[0]
                amount = float(groups[1]) if len(groups) > 1 else None
                unit = groups[2] if len(groups) > 2 else None
            return {'name': name.strip(), 'amount': amount, 'unit': (unit or '').lower()}
    return None

# --- High-level PDF -> structured recipe -------------------------------------

def parse_recipe_pdf(pdf_path: pathlib.Path) -> Dict[str, Any]:
    text = read_pdf_text(pdf_path)
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    servings = None
    ingredients: List[Dict[str, Any]] = []
    steps: List[str] = []

    mode = None
    for line in lines:
        m = SERVINGS_RE.search(line)
        if m:
            try:
                servings = int(m.group(1))
            except Exception:
                pass

        if ING_START.match(line):
            mode = 'ing'
            continue
        if STEP_START.match(line):
            mode = 'step'
            continue

        if mode == 'ing':
            parsed = parse_ingredient_line(line)
            if parsed:
                ingredients.append(parsed)
        elif mode == 'step':
            if len(line) > 0:
                steps.append(line)

    if not ingredients:
        # Fallback: try to parse any lines that look like ingredients
        for line in lines:
            parsed = parse_ingredient_line(line)
            if parsed:
                ingredients.append(parsed)

    if not ingredients:
        raise ValueError(f"No ingredients detected in {pdf_path.name}. Ensure headings 'Ingredients'/'Instructions' exist.")

    return {
        'servings': servings or 1,
        'ingredients': ingredients,
        'instructions': steps or []
    }
