import os
import urllib.parse
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify, render_template_string
import requests
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

load_dotenv()

OPENWEBUI_URL = os.getenv("OPENWEBUI_URL", "http://localhost:8080")
OPENWEBUI_API_KEY = os.getenv("OPENWEBUI_API_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

if not GOOGLE_API_KEY:
    raise RuntimeError("Missing GOOGLE_API_KEY in environment. See .env.example")

app = Flask(__name__)

# Simple rate limiter to avoid hitting Google quotas accidentally
limiter = Limiter(app=app, key_func=get_remote_address, default_limits=["30/minute"])

def call_openwebui(prompt: str, model: str = "gemma:2b") -> str:
    """Call Open WebUI Chat Completions endpoint and return assistant content text."""
    url = f"{OPENWEBUI_URL.rstrip('/')}/api/chat/completions"
    headers = {"Content-Type": "application/json"}
    if OPENWEBUI_API_KEY:
        headers["Authorization"] = f"Bearer {OPENWEBUI_API_KEY}"
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 256,
        "temperature": 0.0
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    # defensive parsing for OpenAI-like format
    try:
        return data["choices"][0]["message"]["content"].strip()
    except Exception:
        # fallback: if Open WebUI returned different shape, try text
        return str(data)

def search_places_text(query: str, google_key: str):
    """Call Google Places Text Search and return list of results."""
    endpoint = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {"query": query, "key": google_key}
    resp = requests.get(endpoint, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()

def build_embed_iframe(place_id: str, width=600, height=450):
    src = f"https://www.google.com/maps/embed/v1/place?key={GOOGLE_API_KEY}&q=place_id:{urllib.parse.quote(place_id)}"
    iframe = f'<iframe width="{width}" height="{height}" style="border:0" loading="lazy" allowfullscreen src="{src}"></iframe>'
    return iframe, src

def build_maps_link(name: str, place_id: str):
    q = urllib.parse.quote_plus(name or "")
    return f"https://www.google.com/maps/search/?api=1&query={q}&query_place_id={urllib.parse.quote(place_id)}"

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"ok": True}), 200

@app.route("/search", methods=["POST"])
@limiter.limit("20/minute")
def search():
    """
    POST /search
    JSON body: { "query": "Cari ramen enak di Jakarta", "use_llm": true }
    Returns JSON with place info, iframe HTML and a maps link.
    """
    body = request.get_json(force=True, silent=True) or {}
    query = (body.get("query") or "").strip()
    if not query:
        return jsonify({"error": "Missing 'query' in request body"}), 400

    use_llm = body.get("use_llm", True)

    # 1) Optionally call LLM to canonicalize / parse the query
    parsed_query = query
    try:
        if use_llm:
            # prompt to LLM: instruct to output a short search query only
            llm_prompt = (
                f"Ubah permintaan pengguna berikut menjadi kalimat pencarian singkat yang cocok "
                f"untuk Google Places (bahasa Indonesia). Hanya keluarkan satu baris teks.\n\n"
                f"User: {query}\n\nOutput:"
            )
            parsed = call_openwebui(llm_prompt)
            if parsed:
                # safety: if LLM returns long text, take first line
                parsed_query = parsed.splitlines()[0].strip()
    except Exception as e:
        # If LLM fails, fall back to original query (we don't want whole flow to die)
        parsed_query = query

    # 2) Call Google Places Text Search
    try:
        places_resp = search_places_text(parsed_query, GOOGLE_API_KEY)
    except Exception as e:
        return jsonify({"error": "Google Places API error", "detail": str(e)}), 502

    results = places_resp.get("results", [])
    if not results:
        return jsonify({"error": "No places found", "query_used": parsed_query}), 404

    # pick top result
    place = results[0]
    place_name = place.get("name")
    place_address = place.get("formatted_address")
    place_id = place.get("place_id")
    latlng = place.get("geometry", {}).get("location", {})

    iframe_html, embed_src = build_embed_iframe(place_id)
    maps_link = build_maps_link(place_name, place_id)

    response = {
        "original_query": query,
        "parsed_query": parsed_query,
        "place": {
            "name": place_name,
            "address": place_address,
            "place_id": place_id,
            "location": latlng
        },
        "map_iframe": iframe_html,
        "map_embed_src": embed_src,
        "maps_link": maps_link,
        "raw_places_api_response_count": len(results)
    }
    return jsonify(response), 200

@app.route("/")
def index():
    return render_template("demo_frontend.html")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)