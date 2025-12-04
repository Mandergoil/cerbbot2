from __future__ import annotations

import json
import threading
import uuid
from pathlib import Path
from typing import Any, Dict, List

from flask import Flask, jsonify, request, send_from_directory

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "products.json"
LOCK = threading.Lock()

app = Flask(__name__, static_folder=None)


def _demo_products() -> List[Dict[str, Any]]:
    return [
        {
            'id': 'italia-demo',
            'name': 'Linea Vesuvio',
            'category': 'italia',
            'description': 'Drop destrutturato con pelle nera, accenti incandescenti e packaging Telegram-ready.',
            'mediaUrl': 'https://images.unsplash.com/photo-1489515217757-5fd1be406fef?auto=format&fit=crop&w=800&q=80',
        },
        {
            'id': 'milano-demo',
            'name': 'Milano Notturna',
            'category': 'milano',
            'description': 'Tailoring urbano con hardware magnetico, curato per release private in città.',
            'mediaUrl': 'https://images.unsplash.com/photo-1475180098004-ca77a66827be?auto=format&fit=crop&w=800&q=80',
        },
        {
            'id': 'spagna-demo',
            'name': 'Madrid Ritmo',
            'category': 'spagna',
            'description': 'Palette calde e inserti glow per dancefloor iberici con vibe Telegram.',
            'mediaUrl': 'https://images.unsplash.com/photo-1485827404703-89b55fcc595e?auto=format&fit=crop&w=800&q=80',
        },
    ]


def _load_products() -> List[Dict[str, Any]]:
    if not DATA_PATH.exists():
        DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
        DATA_PATH.write_text(json.dumps(_demo_products(), ensure_ascii=False, indent=2), encoding='utf-8')
    with DATA_PATH.open(encoding='utf-8') as handle:
        return json.load(handle)


def _save_products(products: List[Dict[str, Any]]) -> None:
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    with DATA_PATH.open('w', encoding='utf-8') as handle:
        json.dump(products, handle, ensure_ascii=False, indent=2)


def _validate_payload(payload: Dict[str, Any], *, partial: bool = False) -> Dict[str, Any]:
    allowed_fields = {"name", "description", "category", "mediaUrl"}
    unknown = set(payload.keys()) - allowed_fields
    if unknown:
        raise ValueError(f"Campi non ammessi: {', '.join(sorted(unknown))}")

    data = {k: (payload.get(k) or '').strip() for k in allowed_fields}
    required = {"name", "description", "category"}
    if not partial:
        missing = [field for field in required if not data[field]]
        if missing:
            raise ValueError(f"Campi obbligatori mancanti: {', '.join(missing)}")
    return {k: v for k, v in data.items() if v}


@app.get('/')
def get_index():
    return send_from_directory(BASE_DIR, 'index.html')


@app.get('/admin')
def get_admin_redirect():
    return send_from_directory(BASE_DIR, 'admin.html')


@app.get('/admin.html')
def get_admin():
    return send_from_directory(BASE_DIR, 'admin.html')


@app.get('/logo.jpg')
def get_logo():
    return send_from_directory(BASE_DIR, 'logo.jpg')


@app.get('/api/products')
def list_products():
    with LOCK:
        products = _load_products()
    return jsonify(products)


@app.post('/api/products')
def create_product():
    payload = request.get_json(force=True, silent=True) or {}
    custom_id = (payload.pop('id', None) or '').strip() or None
    try:
        data = _validate_payload(payload)
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400

    new_product = {
        'id': custom_id or f"{data.get('category', 'item')}-{uuid.uuid4().hex[:8]}",
        **data,
    }
    with LOCK:
        products = _load_products()
        products.append(new_product)
        _save_products(products)
    return jsonify(new_product), 201


@app.put('/api/products/<product_id>')
def update_product(product_id: str):
    payload = request.get_json(force=True, silent=True) or {}
    payload.pop('id', None)
    try:
        updates = _validate_payload(payload, partial=True)
    except ValueError as exc:
        return jsonify({'error': str(exc)}), 400

    with LOCK:
        products = _load_products()
        for item in products:
            if item['id'] == product_id:
                item.update(updates)
                _save_products(products)
                return jsonify(item)
    return jsonify({'error': 'Prodotto non trovato'}), 404


@app.delete('/api/products/<product_id>')
def delete_product(product_id: str):
    with LOCK:
        products = _load_products()
        filtered = [item for item in products if item['id'] != product_id]
        if len(filtered) == len(products):
            return jsonify({'error': 'Prodotto non trovato'}), 404
        _save_products(filtered)
    return jsonify({'status': 'ok'})


@app.post('/api/products/reset')
def reset_products():
    with LOCK:
        demo = _demo_products()
        _save_products(demo)
    return jsonify({'status': 'ok', 'items': demo})


if __name__ == '__main__':
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not DATA_PATH.exists():
        _save_products(_demo_products())
    app.run(debug=True, host='0.0.0.0', port=8000)
