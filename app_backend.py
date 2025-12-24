# backend.py
from flask import Flask, jsonify, request

app = Flask(__name__)

# Replace with your real .docx search index
DATA = [
    {"title": "Meeting Notes - Project X", "url": "#"},
    {"title": "Research Notes - ML", "url": "#"},
    {"title": "OneDrive Setup Guide", "url": "#"},
]

def search_entries(query: str):
    q = (query or "").lower()
    return [item for item in DATA if q in item["title"].lower()]

@app.route("/api/search")
def api_search():
    q = request.args.get("q", "")
    return jsonify(search_entries(q) if q else [])

# Do NOT run app here; ui.py will import and configure it
