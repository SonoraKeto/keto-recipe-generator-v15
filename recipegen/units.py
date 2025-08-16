from __future__ import annotations
import re
from typing import Optional, Dict
import yaml, pathlib
from .builtins import BUILTIN_DENSITIES, SIZE_WEIGHTS

DATA = pathlib.Path(__file__).resolve().parent.parent / 'data'

def _clean_name(s: str) -> str:
    s = s.lower()
    s = re.sub(r'\(.*?\)', '', s)
    s = s.split(',')[0]
    s = re.sub(r'\b(chopped|minced|diced|sliced|fresh|raw|peeled|ground)\b', '', s)
    return re.sub(r'\s+', ' ', s).strip()

def load_yaml(p: pathlib.Path) -> dict:
    return yaml.safe_load(p.read_text()) if p.exists() else {}

def normalize_volume_to_grams(name: str, amount: float, unit: str) -> Optional[float]:
    unit = (unit or '').lower()
    if unit in ('g','gram','grams'): return float(amount)

    # -- size/count units (e.g., 'medium onion', '1 clove garlic', '1 each jalapeno')
    size_unit = (unit or '').lower()
    base_name = _clean_name(name)
    if size_unit in ('small','medium','large','clove','each','whole'):
        weights = None
        for key, table in SIZE_WEIGHTS.items():
            if key in base_name:
                weights = table
                break
        if weights and size_unit in weights:
            return float(amount) * float(weights[size_unit])
        if weights and size_unit in ('each','whole') and 'medium' in weights:
            return float(amount) * float(weights['medium'])


# handle size/count words (e.g., 'medium onion', '1 clove garlic', '1 each jalapeno')
size_unit = unit.lower()
base_name = _clean_name(name)
if size_unit in ('small','medium','large','clove','each','whole'):
    weights = None
    for key, table in SIZE_WEIGHTS.items():
        if key in base_name:
            weights = table
            break
    if weights and size_unit in weights:
        return float(amount) * float(weights[size_unit])
    # fallback: 'whole' or 'each' map to 'medium' when available
    if weights and size_unit in ('each','whole') and 'medium' in weights:
        return float(amount) * float(weights['medium'])

    if unit == 'kg': return float(amount) * 1000.0

    if unit in ('cup','cups','c','tbsp','tablespoon','tablespoons','tsp','teaspoon','teaspoons'):
        overrides = load_yaml(DATA / 'ingredient_overrides.yml')
        dens_over = load_yaml(DATA / 'density_overrides.yml')
        commons   = load_yaml(DATA / 'common_densities.yml')
        merged_common = {**BUILTIN_DENSITIES, **commons}

        key_exact = name
        key_norm = name.lower().strip()

        dens = None
        if key_exact in overrides and 'density' in overrides[key_exact]:
            dens = overrides[key_exact]['density']
        elif key_norm in overrides and 'density' in overrides[key_norm]:
            dens = overrides[key_norm]['density']
        elif key_exact in dens_over:
            dens = dens_over[key_exact]
        elif key_norm in dens_over:
            dens = dens_over[key_norm]
        elif key_exact in merged_common:
            dens = merged_common[key_exact]
        elif key_norm in merged_common:
            dens = merged_common[key_norm]

        if not dens:
            return None

        if unit in ('cup','cups','c'):
            g = dens.get('cup_g')
        elif unit in ('tbsp','tablespoon','tablespoons'):
            g = dens.get('tbsp_g')
        else:
            g = dens.get('tsp_g')

        if g is None:
            return None
        return float(amount) * float(g)

    return None