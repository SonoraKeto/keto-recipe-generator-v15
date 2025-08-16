from __future__ import annotations
from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape
import json, pathlib

def jinja_env(template_path: pathlib.Path) -> Environment:
    return Environment(
        loader=FileSystemLoader(str(template_path.parent)),
        autoescape=select_autoescape(['html','xml']),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
    )

def render_html(template_path: pathlib.Path, context):
    env = jinja_env(template_path)
    tpl = env.get_template(template_path.name)
    return tpl.render(**context)

def make_json_ld(context: dict) -> str:
    nps = context['nutrition_per_serving']
    obj = {
        "@context": "https://schema.org",
        "@type": "Recipe",
        "name": context.get("title",""),
        "image": context.get("image",""),
        "recipeYield": context.get("servings"),
        "nutrition": {
            "@type": "NutritionInformation",
            "calories": f"{nps.get('calories',0)} kcal",
            "carbohydrateContent": f"{nps.get('carbs_g',0)} g",
            "fiberContent": f"{nps.get('fiber_g',0)} g",
            "proteinContent": f"{nps.get('protein_g',0)} g",
            "fatContent": f"{nps.get('fat_g',0)} g",
        }
    }
    return json.dumps(obj, indent=2)
