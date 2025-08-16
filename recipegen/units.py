from __future__ import annotations

import re
import yaml
import pathlib
from typing import Optional, Dict, Any

from .builtins import BUILTIN_DENSITIES, SIZE_WEIGHTS

DATA = pathlib.Path(__file__).resolve().parent.parent / 'data'


def load_yaml(p: pathlib.Path) -> Dict[str, Any]:
    try:
        if p.exists():
            with open(p, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
    except Exception:
        pass
    return {}


CLEAN_RX = re.compile(r'\b(chopped|minced|diced|sliced|fresh|raw|peeled|ground)\b', re.I)


def _clean_name(s: str) -> str:
    s = s.lower()
    s = re.sub(r'\(.*?\)', '', s)
    s = s.split(',')[0]
    s = CLEAN_RX.sub('', s)
    return re.sub(r'\s+', ' ', s).strip()


def _merged_densities() -> Dict[str, Dict[str, float]]:
    """Merge built-in densities with optional YAML files."""
    dens_over = load_yaml(DATA / 'density_overrides.yml')
    commons = load_yaml(DATA / 'common_densities.yml')
    merged: Dict[str, Dict[str, float]] = {}
    merged.update(BUILTIN_DENSITIES)         # built-in fallbacks
    merged.update(commons or {})             # user common
    merged.update(dens_over or {})           # explicit overrides win
    return merged


def normalize_volume_to_grams(name: str, amount: float, unit: Optional[str]) -> Optional[float]:
    """
    Convert (amount, unit, ingredient-name) => grams.

    Supports:
      - g/gram direct inputs
      - tsp/tbsp/cup using density tables (merged from built-ins + YAML)
      - size/count units: small/medium/large/clove/each/whole via SIZE_WEIGHTS
    Returns None if unknown.
    """
    if amount is None or unit is None:
        return None

    unit = unit.lower().strip()
    base = _clean_name(name)

    # --- direct gram inputs ---------------------------------------------------
    if unit in ('g', 'gram', 'grams'):
        try:
            return float(amount)
        except Exception:
            return None

    # --- size/count units: '1/2 medium onion', '2 large eggs', '1 clove garlic'
    if unit in ('small', 'medium', 'large', 'clove', 'each', 'whole'):
        weights = None
        for key, table in SIZE_WEIGHTS.items():
            if key in base:
                weights = table
                break
        if weights:
            if unit in weights:
                return float(amount) * float(weights[unit])
            if unit in ('each', 'whole') and 'medium' in weights:
                return float(amount) * float(weights['medium'])

    # --- volume units with densities -----------------------------------------
    merged = _merged_densities()
    dens = merged.get(base)
    if not dens and base.endswith('s'):
        dens = merged.get(base[:-1])  # singular fallback

    if dens:
        if unit in ('tsp', 'teaspoon', 'teaspoons'):
            v = dens.get('tsp_g')
            if isinstance(v, (int, float)):
                return float(amount) * float(v)
        if unit in ('tbsp', 'tablespoon', 'tablespoons'):
            v = dens.get('tbsp_g')
            if isinstance(v, (int, float)):
                return float(amount) * float(v)
        if unit in ('cup', 'cups', 'c'):
            v = dens.get('cup_g')
            if isinstance(v, (int, float)):
                return float(amount) * float(v)
        if unit in ('ml', 'milliliter', 'milliliters'):
            v = dens.get('ml_g') or dens.get('g_per_ml')
            if isinstance(v, (int, float)):
                return float(amount) * float(v)

    # Conservative fallback: treat 1 ml == 1 g for water-like liquids only
    if unit in ('ml', 'milliliter', 'milliliters') and any(k in base for k in ('water', 'vinegar', 'juice')):
        return float(amount)

    return None
