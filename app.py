from __future__ import annotations
import os, pathlib, shutil, zipfile, io, re
from typing import Dict, Any, List, Optional
from flask import Flask, render_template, request, send_file
from recipegen.parsers import parse_recipe_pdf
from recipegen.nfp_parser import extract_panel_text, parse_nfp_text_to_per100g
from recipegen.units import normalize_volume_to_grams
from recipegen.nutrition import override_per100, choose_mix_id
from recipegen.images import compress_to_webp
from recipegen.render import render_html, make_json_ld
import recipegen.usda as usda
from werkzeug.utils import secure_filename

ROUND = 1

CLEAN_RX = re.compile(r'\b(chopped|minced|diced|sliced|fresh|raw|peeled|ground)\b', re.I)

def _clean_name(s: str) -> str:
    s = re.sub(r'\(.*?\)', '', s)
    s = s.split(',')[0]
    s = CLEAN_RX.sub('', s)
    s = re.sub(r'\s+', ' ', s)
    return s.strip()
app = Flask(__name__, template_folder='templates', static_folder='static')
BASE = pathlib.Path(__file__).resolve().parent

def _slugish(s: str) -> str:
    s = s.lower()
    s = re.sub(r'[^a-z0-9]+', '-', s)
    return re.sub(r'-+', '-', s).strip('-')

def find_image_for(stem: str, images_dir: pathlib.Path):
    """Return the first image whose stem matches the PDF's stem (case-insensitive, punctuation-insensitive)."""
    want = _slugish(stem)
    for p in images_dir.iterdir():
        if not p.is_file(): 
            continue
        if p.suffix.lower() not in ('.webp','.jpg','.jpeg','.png'):
            continue
        if _slugish(p.stem) == want:
            return p
    return None

def multiply_per100(per100: Dict[str, float], grams: float) -> Dict[str, float]:
    f = grams / 100.0
    return {k: (round(v * f, ROUND) if v is not None else None) for k,v in per100.items()}

def sum_macros(items: List[Dict[str, float]]) -> Dict[str, float]:
    keys = ('calories','fat_g','carbs_g','fiber_g','protein_g')
    out = {k: 0.0 for k in keys}
    for it in items:
        for k in keys:
            v = it.get(k)
            if v is not None:
                out[k] += v
    return {k: round(v, ROUND) for k,v in out.items()}

def compute_net(per_serving: Dict[str, float]) -> Optional[float]:
    c = per_serving.get('carbs_g')
    f = per_serving.get('fiber_g')
    if c is None or f is None: return None
    return round(c - f, ROUND)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', message=None, download_url=None, success=True)

@app.route('/generate', methods=['POST'])
def generate():
    try:
        work = BASE / 'uploads' / secure_filename(str(os.getpid()))
        if work.exists(): shutil.rmtree(work)
        (work / 'mix_panels').mkdir(parents=True, exist_ok=True)
        (work / 'images').mkdir(parents=True, exist_ok=True)
        (work / 'pdfs').mkdir(parents=True, exist_ok=True)
        (work / 'out').mkdir(parents=True, exist_ok=True)

        template_file = request.files['template']
        tpl_path = work / secure_filename(template_file.filename)
        template_file.save(tpl_path)

        for f in request.files.getlist('recipes'):
            if f.filename.lower().endswith('.pdf'):
                f.save(work / 'pdfs' / secure_filename(f.filename))

        for f in request.files.getlist('images'):
            if any(f.filename.lower().endswith(e) for e in ('.jpg','.jpeg','.png','.webp')):
                f.save(work / 'images' / secure_filename(f.filename))

        for f in request.files.getlist('mix_panels'):
            if any(f.filename.lower().endswith(e) for e in ('.pdf','.png','.jpg','.jpeg','.webp')):
                f.save(work / 'mix_panels' / secure_filename(f.filename))

        data_dir = BASE / 'data'
        data_dir.mkdir(exist_ok=True)
        for key in ['ingredient_overrides','density_overrides','mix_map']:
            file = request.files.get(key)
            if file and file.filename:
                file.save(data_dir / secure_filename(file.filename))

        usda_key = request.form.get('usda_key') or ''
        if usda_key:
            (data_dir / 'usda_api_key.txt').write_text(usda_key.strip())

        units = request.form.get('units','us')
        site_base_url = request.form.get('site_base_url') or None
        emit_jsonld = 'emit_jsonld' in request.form

        pdfs = sorted((work / 'pdfs').glob('*.pdf'))
        panels_dir = work / 'mix_panels'

        for pdf in pdfs:
            stem = pdf.stem
            img = find_image_for(stem, work / 'images')
            if not img:
                return render_template('index.html', message=f"No image found for {stem}.", success=False, download_url=None)

            parsed = parse_recipe_pdf(pdf)
            servings = parsed['servings']

            nutrient_items = []
            normalized_ings = []
            for ing in parsed['ingredients']:
                qname = _clean_name(ing['name'])
                per100 = override_per100(qname)
                if not per100:
                    mix_id = choose_mix_id(qname)
                    if mix_id:
                        cand = None
                        for ext in ('.pdf','.png','.jpg','.jpeg','.webp'):
                            q = panels_dir / f"{mix_id}{ext}"
                            if q.exists(): cand = q; break
                        if cand:
                            text = extract_panel_text(cand)
                            parsed_panel = parse_nfp_text_to_per100g(text)
                            per100 = parsed_panel['per_100g']
                if not per100:
                    per100 = usda.search_per100g(qname, api_key=usda_key or None)

                if not per100:
                    return render_template('index.html', message=f"Missing nutrition data for '{ing['name']}'. Add override/mix or provide USDA key.", success=False, download_url=None)

                g = 0.0
                if ing.get('amount') and ing.get('unit'):
                    g = normalize_volume_to_grams(qname, ing['amount'], ing['unit']) or 0.0
                    if g == 0.0 and ing.get('unit') not in ('','g','kg'):
                        return render_template('index.html', message=f"Need density for {ing['name']} to convert {ing['amount']} {ing['unit']} to grams.", success=False, download_url=None)

                amt_macros = multiply_per100(per100, g) if g else {k: 0.0 for k in ('calories','fat_g','carbs_g','fiber_g','protein_g')}
                nutrient_items.append(amt_macros)

                disp = f"{ing['name']} — {int(round(g))} g" if units=='metric' and g>0 else                        (f"{ing['name']} — {ing['amount']:g} {ing['unit']}" if ing.get('amount') and ing.get('unit') else ing['name'])
                normalized_ings.append({**ing, 'amount_g': g, 'display': disp})

            totals = sum_macros(nutrient_items)
            per_serving = {k: round(v/servings, ROUND) for k,v in totals.items()}
            per_serving['net_carbs_g'] = compute_net(per_serving)

            out_dir = work / 'out' / 'recipes' / stem
            out_dir.mkdir(parents=True, exist_ok=True)
            compress_to_webp(img, out_dir / 'image.webp')

            context = {
                'title': stem.replace('-', ' ').title(),
                'description': '',
                'canonical_url': None if not site_base_url else f"{site_base_url.rstrip('/')}/recipes/{stem}/",
                'image': 'image.webp',
                'servings': servings,
                'ingredients': normalized_ings,
                'instructions': parsed['instructions'],
                'nutrition_per_serving': per_serving,
                'emit_jsonld': emit_jsonld,
                'json_ld': make_json_ld({
                    'title': stem.replace('-', ' ').title(),
                    'image': 'image.webp',
                    'servings': servings,
                    'nutrition_per_serving': per_serving
                }) if emit_jsonld else ""
            }

            html = render_html(tpl_path, context)
            (out_dir / 'index.html').write_text(html, encoding='utf-8')

        out_zip = io.BytesIO()
        with zipfile.ZipFile(out_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
            for path in (work / 'out').rglob('*'):
                if path.is_file():
                    zf.write(path, path.relative_to(work).as_posix())
        out_zip.seek(0)
        return send_file(out_zip, mimetype='application/zip', as_attachment=True, download_name='dist.zip')
    except Exception as e:
        app.logger.exception('Generate failed')
        return render_template('index.html', message=str(e), success=False, download_url=None)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7860, debug=True)
