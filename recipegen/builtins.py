# Built-in pantry macros & densities (per 100g) used as fallback.
BUILTIN_OVERRIDES = {
  "vegetable oil": {
    "per_100g": {"calories": 884, "fat_g": 100, "carbs_g": 0, "fiber_g": 0, "protein_g": 0},
    "density": {"tbsp_g": 13.6, "tsp_g": 4.5, "cup_g": 218}
  },
  "olive oil": {
    "per_100g": {"calories": 884, "fat_g": 100, "carbs_g": 0, "fiber_g": 0, "protein_g": 0},
    "density": {"tbsp_g": 13.5, "tsp_g": 4.5, "cup_g": 216}
  },
  "avocado oil": {
    "per_100g": {"calories": 884, "fat_g": 100, "carbs_g": 0, "fiber_g": 0, "protein_g": 0},
    "density": {"tbsp_g": 13.6, "tsp_g": 4.5, "cup_g": 218}
  },
  "salt": {
    "per_100g": {"calories": 0, "fat_g": 0, "carbs_g": 0, "fiber_g": 0, "protein_g": 0},
    "density": {"tsp_g": 6, "tbsp_g": 18}
  },
  "black pepper": {
    "per_100g": {"calories": 251, "fat_g": 3.3, "carbs_g": 64, "fiber_g": 25, "protein_g": 10.4},
    "density": {"tsp_g": 2.3, "tbsp_g": 6.9}
  },
  "chili powder": {
    "per_100g": {"calories": 282, "fat_g": 14.3, "carbs_g": 49.7, "fiber_g": 34.8, "protein_g": 12.0},
    "density": {"tsp_g": 2.6, "tbsp_g": 7.8}
  },
  "ground cumin": {
    "per_100g": {"calories": 375, "fat_g": 22.3, "carbs_g": 44.2, "fiber_g": 10.5, "protein_g": 17.8},
    "density": {"tsp_g": 2.1, "tbsp_g": 6.3}
  },
  "garlic powder": {
    "per_100g": {"calories": 331, "fat_g": 0.7, "carbs_g": 73.0, "fiber_g": 9.0, "protein_g": 17.0},
    "density": {"tsp_g": 3.1, "tbsp_g": 9.3}
  },
  "onion powder": {
    "per_100g": {"calories": 342, "fat_g": 1.0, "carbs_g": 79.1, "fiber_g": 15.2, "protein_g": 10.4},
    "density": {"tsp_g": 2.4, "tbsp_g": 7.2}
  },
  "apple cider vinegar": {
    "per_100g": {"calories": 22, "fat_g": 0, "carbs_g": 0.9, "fiber_g": 0, "protein_g": 0},
    "density": {"tsp_g": 5, "tbsp_g": 15, "cup_g": 240}
  },
  "white vinegar": {
    "per_100g": {"calories": 18, "fat_g": 0, "carbs_g": 0, "fiber_g": 0, "protein_g": 0},
    "density": {"tsp_g": 5, "tbsp_g": 15, "cup_g": 240}
  },
  "lime juice": {
    "per_100g": {"calories": 25, "fat_g": 0.1, "carbs_g": 8.4, "fiber_g": 0.4, "protein_g": 0.4},
    "density": {"tsp_g": 5, "tbsp_g": 15, "cup_g": 240}
  },
  "lemon juice": {
    "per_100g": {"calories": 22, "fat_g": 0.2, "carbs_g": 6.9, "fiber_g": 0.3, "protein_g": 0.4},
    "density": {"tsp_g": 5, "tbsp_g": 15, "cup_g": 240}
  }
}

BUILTIN_DENSITIES = {
  "vegetable oil": {"tbsp_g": 13.6, "tsp_g": 4.5, "cup_g": 218},
  "olive oil": {"tbsp_g": 13.5, "tsp_g": 4.5, "cup_g": 216},
  "avocado oil": {"tbsp_g": 13.6, "tsp_g": 4.5, "cup_g": 218},
  "salt": {"tsp_g": 6, "tbsp_g": 18},
  "black pepper": {"tsp_g": 2.3, "tbsp_g": 6.9},
  "chili powder": {"tsp_g": 2.6, "tbsp_g": 7.8},
  "ground cumin": {"tsp_g": 2.1, "tbsp_g": 6.3},
  "garlic powder": {"tsp_g": 3.1, "tbsp_g": 9.3},
  "onion powder": {"tsp_g": 2.4, "tbsp_g": 7.2},
  "apple cider vinegar": {"tsp_g": 5, "tbsp_g": 15, "cup_g": 240},
  "white vinegar": {"tsp_g": 5, "tbsp_g": 15, "cup_g": 240},
  "lime juice": {"tsp_g": 5, "tbsp_g": 15, "cup_g": 240},
  "lemon juice": {"tsp_g": 5, "tbsp_g": 15, "cup_g": 240}
}


# Average weights (grams) for size/count-based items
SIZE_WEIGHTS = {
  "onion": {"small": 70, "medium": 110, "large": 150},
  "garlic": {"clove": 3},
  "jalapeno": {"each": 14, "medium": 14},
  "egg": {"large": 50, "each": 50},
  "lime": {"each": 67, "medium": 67},
  "lemon": {"each": 84, "medium": 84}
}
