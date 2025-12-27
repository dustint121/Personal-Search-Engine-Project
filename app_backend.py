# app_backend.py

import os
import json
import atexit
import base64

import requests
from flask import Flask, jsonify, request
from msal import PublicClientApplication, SerializableTokenCache
from dotenv import load_dotenv
from perplexity import Perplexity

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

# Simple in-memory chat history (single-user dev)
CHAT_HISTORY = [
    {
        "role": "system",
        "content": (
            "You are a friendly chatbot in a web app. "
            "Keep replies brief and to-the-point unless the user asks for detail. "
            "You can reference attached note files as needed."
        ),
    }
]


def load_cache():
    cache = SerializableTokenCache()
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            cache.deserialize(f.read())
    atexit.register(
        lambda: open(CACHE_FILE, "w").write(cache.serialize())
        if cache.has_state_changed
        else None
    )
    return cache


def get_token(msal_app: PublicClientApplication) -> str:
    accounts = msal_app.get_accounts()
    if accounts:
        result = msal_app.acquire_token_silent(SCOPES, account=accounts[0])
        if result and "access_token" in result:
            return result["access_token"]

    flow = msal_app.initiate_device_flow(scopes=SCOPES)
    if "user_code" not in flow:
        raise RuntimeError("Failed to create device flow. Check app registration.")
    print("Go to", flow["verification_uri"], "and enter code:", flow["user_code"])
    result = msal_app.acquire_token_by_device_flow(flow)
    if "access_token" in result:
        return result["access_token"]

    raise RuntimeError("Authentication failed: {}".format(result.get("error_description")))


def get_graph_headers():
    cache = load_cache()
    msal_app = PublicClientApplication(
        client_id=CLIENT_ID,
        authority=AUTHORITY,
        token_cache=cache,
    )
    access_token = get_token(msal_app)
    return {"Authorization": f"Bearer {access_token}"}


def search_onedrive_docx(query: str):
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
    Retrieve a document's bytes directly from Graph.
    No local note_files folder is used.
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


# === API routes ===


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
    # source value from frontend is now ignored; always use Graph
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
