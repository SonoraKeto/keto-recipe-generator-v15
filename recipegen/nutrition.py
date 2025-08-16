from __future__ import annotations
from typing import Optional, Dict
import yaml, pathlib
from .builtins import BUILTIN_OVERRIDES
from rapidfuzz import process, fuzz

DATA = pathlib.Path(__file__).resolve().parent.parent / 'data'

def load_yaml(p: pathlib.Path) -> dict:
    return yaml.safe_load(p.read_text()) if p.exists() else {}

def load_overrides() -> dict:
    return load_yaml(DATA / 'ingredient_overrides.yml')

def load_mix_map() -> dict:
    return load_yaml(DATA / 'mix_map.yml')

def fuzzy_get(mapping: dict, name: str, threshold=90):
    if not mapping: return None
    keys = list(mapping.keys())
    best = process.extractOne(name, keys, scorer=fuzz.WRatio)
    if not best: return None
    match, score, _ = best
    return mapping[match] if score >= threshold else None

def choose_mix_id(ingredient_name: str) -> Optional[str]:
    m = load_mix_map()
    if not m: return None
    val = fuzzy_get(m, ingredient_name.lower(), threshold=92)
    if isinstance(val, str): return val
    return None

def override_per100(ingredient_name: str) -> Optional[Dict[str, float]]:
    ov = {**BUILTIN_OVERRIDES, **(load_overrides() or {})}
    hit = ov.get(ingredient_name) or ov.get(ingredient_name.lower())
    if not hit:
        hit = fuzzy_get(ov, ingredient_name, threshold=92)
    if not hit: return None
    if 'per_100g' in hit: return hit['per_100g']
    return None
