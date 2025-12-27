# app_backend.py
import os
import json
import base64

import requests
from flask import Flask, jsonify, request, render_template

from msal import PublicClientApplication
from dotenv import load_dotenv
from perplexity import Perplexity
from get_authentication import load_cache, get_token

load_dotenv()

app = Flask(__name__)

# === OneDrive / Microsoft Graph configuration ===

CLIENT_ID = os.getenv("CLIENT_ID")
AUTHORITY = "https://login.microsoftonline.com/common"
SCOPES = ["Files.Read.All"]
CACHE_FILE = os.path.join(os.path.dirname(__file__), "token_cache.bin")
ONEDRIVE_DOCUMENTS_FOLDER_ID = os.getenv("ONEDRIVE_DOCUMENTS_FOLDER_ID")

# === Perplexity API configuration ===

PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
PPLX_CLIENT = Perplexity(api_key=PERPLEXITY_API_KEY, base_url="https://api.perplexity.ai")

# Notes metadata (catalog only – no local note_files usage)

BASE_DIR = os.path.dirname(__file__)
NOTES_METADATA_PATH = os.path.join(BASE_DIR, "notes_metadata.json")


def get_graph_headers():
    """Acquire a Graph access token and return Authorization headers."""
    cache = load_cache()
    msal_app = PublicClientApplication(
        client_id=CLIENT_ID,
        authority=AUTHORITY,
        token_cache=cache,
    )
    access_token = get_token(msal_app)
    return {"Authorization": f"Bearer {access_token}"}


def search_onedrive_docx(query: str):
    """Search OneDrive for .docx files whose name matches the query."""
    if not query:
        return []
    headers = get_graph_headers()
    url = (
        "https://graph.microsoft.com/v1.0/me/drive/root/"
        f"search(q='{query}')"
        "?$filter=endswith(name,'.docx')"
        "&$select=name,id,webUrl"
    )
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()

    os.makedirs("output", exist_ok=True)
    with open("output/query_result.json", "w") as f:
        json.dump(data, f, indent=4)

    items = data.get("value", [])
    return [
        {
            "id": item.get("id"),
            "title": item.get("name", "(no name)"),
            "url": item.get("webUrl", "#"),
        }
        for item in items
    ]


def load_notes_metadata():
    if not os.path.exists(NOTES_METADATA_PATH):
        return []
    with open(NOTES_METADATA_PATH, "r") as f:
        return json.load(f)


def save_notes_metadata(notes):
    with open(NOTES_METADATA_PATH, "w") as f:
        json.dump(notes, f, indent=2)


def append_note_metadata_if_missing(note_id: str, name: str = "", web_url: str = ""):
    """
    Kept in case you still want to extend metadata, but no longer writes any local files.
    """
    notes = load_notes_metadata()
    if any(n.get("id") == note_id for n in notes):
        return
    notes.append({"id": note_id, "name": name, "webUrl": web_url})
    save_notes_metadata(notes)


def retrieve_document_content(item_id: str) -> bytes:
    """
    Retrieve a document's bytes directly from Graph (no local note_files folder).
    """
    headers = get_graph_headers()
    url = (
        f"https://graph.microsoft.com/v1.0/drives/"
        f"{ONEDRIVE_DOCUMENTS_FOLDER_ID}/items/{item_id}/content"
    )
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise RuntimeError(
            f"Failed to retrieve document content from {url}: "
            f"{response.status_code} {response.text}"
        )
    return response.content


# === HTML pages (Flask + Jinja) ===

@app.route("/")
def page1():
    """Search / summarize page."""
    return render_template("page1.html")


@app.route("/chat")
def page2():
    """Chat page."""
    return render_template("page2.html")


# === JSON API routes (used by JS) ===

@app.route("/api/search")
def api_search():
    q = request.args.get("q", "")
    try:
        return jsonify(search_onedrive_docx(q))
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/notes-metadata")
def api_notes_metadata():
    return jsonify(load_notes_metadata())


@app.route("/api/summarize", methods=["POST"])
def api_summarize():
    payload = request.get_json(silent=True) or {}
    ids = payload.get("ids", [])
    # "source" from frontend is ignored; always use Graph

    if not ids:
        return jsonify({"error": "No ids provided"}), 400

    try:
        file_contents = []
        for item_id in ids:
            content_bytes = retrieve_document_content(item_id)
            encoded = base64.b64encode(content_bytes).decode("utf-8")
            file_contents.append(encoded)

        prompt = (
            "You are summarizing a set of Microsoft Word documents from my notes. "
            "For each attached document, provide a short summary, then a brief overall summary."
        )

        content = [{"type": "text", "text": prompt}]
        for encoded_data in file_contents:
            content.append(
                {
                    "type": "file_url",
                    "file_url": {"url": encoded_data},
                }
            )

        response = PPLX_CLIENT.chat.completions.create(
            model="sonar",
            messages=[{"role": "user", "content": content}],
        )

        summary_text = response.choices[0].message.content
        return jsonify({"summary": summary_text, "source": "cloud"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json(silent=True) or {}
    user_text = (data.get("message") or "").strip()
    note_ids = data.get("note_ids") or []  # list of OneDrive IDs to attach

    if not user_text:
        return jsonify({"error": "Empty message"}), 400

    # Build content with text + attached files (directly from Graph)
    content = [{"type": "text", "text": user_text}]
    file_contents = []

    try:
        for note_id in note_ids:
            content_bytes = retrieve_document_content(note_id)
            encoded = base64.b64encode(content_bytes).decode("utf-8")
            file_contents.append(encoded)

        for encoded_data in file_contents:
            content.append(
                {
                    "type": "file_url",
                    "file_url": {"url": encoded_data},
                }
            )
    except Exception as e:
        return jsonify({"error": f"Failed to load attachments: {e}"}), 500

    try:
        response = PPLX_CLIENT.chat.completions.create(
            model="sonar",
            messages=[{"role": "user", "content": content}],
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    reply = response.choices[0].message.content
    citations = getattr(response, "citations", []) or []
    return jsonify({"reply": reply, "citations": citations})


@app.route("/api/auth-status")
def api_auth_status():
    """
    Check if a valid Graph token is available.
    If not, start device flow and return the 'Go to ... enter code ...' message.
    """
    try:
        cache = load_cache()
        msal_app = PublicClientApplication(
            client_id=CLIENT_ID,
            authority=AUTHORITY,
            token_cache=cache,
        )

        # Try silent first
        accounts = msal_app.get_accounts()
        if accounts:
            result = msal_app.acquire_token_silent(SCOPES, account=accounts[0])
            if result and "access_token" in result:
                return jsonify(
                    {
                        "status": "ok",
                        "message": "Microsoft Graph permissions are properly set.",
                    }
                )

        # No valid token: initiate device flow but DO NOT block waiting for user.
        flow = msal_app.initiate_device_flow(scopes=SCOPES)
        if "user_code" not in flow:
            return jsonify(
                {
                    "status": "error",
                    "message": "Failed to create device flow. Check app registration.",
                }
            ), 500

        verify_msg = (
            f"Go to {flow['verification_uri']} and enter code: {flow['user_code']}\n"
            "Then refresh this page."
        )

        return jsonify({"status": "needs_auth", "message": verify_msg})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
