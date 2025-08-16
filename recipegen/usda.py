from __future__ import annotations
import os, requests
from typing import Optional, Dict, Any, List

NID_ENERGY_KCAL = 1008
NID_CARBS = 1005
NID_PROTEIN = 1003
NID_FAT = 1004
NID_FIBER = 1079

API_BASE = "https://api.nal.usda.gov/fdc"

def _get_api_key(explicit: Optional[str]) -> Optional[str]:
    return explicit or os.getenv("USDA_API_KEY") or None

def _best_result(results: List[dict]) -> Optional[dict]:
    if not results:
        return None
    preferred = ["SR Legacy", "Foundation", "Survey (FNDDS)"]
    for p in preferred:
        for r in results:
            if r.get("dataType") == p:
                return r
    return results[0]

def _extract_per100_from_foodNutrients(food: dict) -> Optional[Dict[str, float]]:
    nutrients = {n.get("nutrient", {}).get("id") or n.get("nutrientId"): n.get("amount") for n in food.get("foodNutrients", [])}
    if not nutrients:
        return None
    def get(nid): 
        val = nutrients.get(nid)
        try:
            return float(val) if val is not None else None
        except:
            return None
    energy = get(NID_ENERGY_KCAL)
    fat = get(NID_FAT)
    carbs = get(NID_CARBS)
    fiber = get(NID_FIBER)
    protein = get(NID_PROTEIN)
    if any(v is not None for v in (fat, carbs, fiber, protein, energy)):
        return {
            "calories": energy if energy is not None else 0.0,
            "fat_g": fat if fat is not None else 0.0,
            "carbs_g": carbs if carbs is not None else 0.0,
            "fiber_g": fiber if fiber is not None else 0.0,
            "protein_g": protein if protein is not None else 0.0,
        }
    return None

def _extract_from_labelNutrients(food: dict) -> Optional[Dict[str, float]]:
    label = food.get("labelNutrients")
    serv = food.get("servingSize")
    serv_unit = (food.get("servingSizeUnit") or "").lower()
    if not label or not serv or serv_unit not in ("g", "gram", "grams"):
        return None
    try:
        serv = float(serv)
    except:
        return None
    def get_label(name):
        node = label.get(name) or {}
        val = node.get("value")
        try:
            return float(val) if val is not None else None
        except:
            return None
    energy = get_label("calories")
    fat = get_label("fat")
    carbs = get_label("carbohydrates")
    fiber = get_label("fiber")
    protein = get_label("protein")
    factor = 100.0 / serv
    def scale(x): return round(x * factor, 4) if x is not None else 0.0
    if any(v is not None for v in (energy, fat, carbs, fiber, protein)):
        return {
            "calories": scale(energy),
            "fat_g": scale(fat),
            "carbs_g": scale(carbs),
            "fiber_g": scale(fiber),
            "protein_g": scale(protein),
        }
    return None

def search_per100g(query: str, api_key: Optional[str] = None, timeout: int = 10) -> Optional[Dict[str, float]]:
    key = _get_api_key(api_key)
    if not key:
        return None
    try:
        resp = requests.get(f"{API_BASE}/v1/foods/search", params={"api_key": key, "query": query, "pageSize": 5}, timeout=timeout)
        if resp.status_code != 200:
            return None
        data = resp.json()
        results = data.get("foods") or []
        best = _best_result(results)
        if not best:
            return None
        per100 = _extract_per100_from_foodNutrients(best)
        if per100:
            return per100
        fdc_id = best.get("fdcId")
        if not fdc_id:
            return None
        detail = requests.get(f"{API_BASE}/v1/foods/{fdc_id}", params={"api_key": key}, timeout=timeout)
        if detail.status_code != 200:
            return None
        food = detail.json()
        per100 = _extract_per100_from_foodNutrients(food)
        if per100:
            return per100
        per100 = _extract_from_labelNutrients(food)
        return per100
    except Exception:
        return None
