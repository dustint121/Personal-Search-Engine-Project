# app_backend.py
import os
import json
import base64
from datetime import datetime

import requests
from flask import Flask, jsonify, request, render_template
from msal import PublicClientApplication
from dotenv import load_dotenv
from perplexity import Perplexity
from pymongo import MongoClient
from bson import ObjectId

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

# === MongoDB configuration (threads) ===

MONGO_URL = os.getenv("MONGO_URL")
mongo_client = MongoClient(MONGO_URL) if MONGO_URL else None
db = mongo_client["chatbot_db"] if mongo_client else None
threads_collection = db["threads"] if db else None  # documents: {_id, title, conversations, created_at, updated_at}

# print("mongo_client:", mongo_client)
print("MONGO_URL:", MONGO_URL)
# Notes metadata (catalog only – no local note_files usage)

BASE_DIR = os.path.dirname(__file__)
NOTES_METADATA_PATH = os.path.join(BASE_DIR, "notes_metadata.json")


# === Helpers ===

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
    notes = load_notes_metadata()
    if any(n.get("id") == note_id for n in notes):
        return
    notes.append({"id": note_id, "name": name, "webUrl": web_url})
    save_notes_metadata(notes)


def retrieve_document_content(item_id: str) -> bytes:
    """Retrieve a document's bytes directly from Graph (no local note_files folder)."""
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


def serialize_thread(doc):
    """Convert a Mongo thread document to JSON-safe dict."""
    return {
        "id": str(doc["_id"]),
        "title": doc.get("title", "Untitled"),
        "conversations": doc.get("conversations", []),
        "created_at": doc.get("created_at"),
        "updated_at": doc.get("updated_at"),
    }


# === HTML pages (Flask + Jinja) ===

@app.route("/")
def page1():
    """Search / summarize page."""
    return render_template("page1.html")


@app.route("/chat")
def page2():
    """Chat page with threads sidebar."""
    return render_template("page2.html")


# === JSON API: search/summarize/chat/auth ===

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
    thread_id = data.get("thread_id")

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

    # Optionally store in thread
    if threads_collection and thread_id:
        try:
            threads_collection.update_one(
                {"_id": ObjectId(thread_id)},
                {
                    "$push": {
                        "conversations": {
                            "user": user_text,
                            "assistant": reply,
                            "citations": citations,
                        }
                    },
                    "$set": {"updated_at": datetime.utcnow()},
                },
            )
        except Exception:
            # Do not fail chat if persistence fails
            pass

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


# === JSON API: threads (MongoDB) ===

@app.route("/api/threads", methods=["GET"])
def api_threads_list():
    """List all threads (id, title, updated_at)."""
    if not threads_collection:
        return jsonify([])

    docs = list(
        threads_collection.find({}, {"conversations": 0}).sort("updated_at", -1)
    )
    threads = [
        {
            "id": str(doc["_id"]),
            "title": doc.get("title", "Untitled"),
            "updated_at": doc.get("updated_at"),
        }
        for doc in docs
    ]
    return jsonify(threads)


@app.route("/api/threads", methods=["POST"])
def api_threads_create():
    """Create a new thread with optional title."""
    if not threads_collection:
        return jsonify({"error": "Threads storage not configured"}), 500

    payload = request.get_json(silent=True) or {}
    title = (payload.get("title") or "").strip() or "New thread"
    now = datetime.utcnow()
    doc = {
        "title": title,
        "conversations": [],
        "created_at": now,
        "updated_at": now,
    }
    result = threads_collection.insert_one(doc)
    doc["_id"] = result.inserted_id
    return jsonify(serialize_thread(doc)), 201


@app.route("/api/threads/<thread_id>", methods=["GET"])
def api_threads_get(thread_id):
    """Get a full thread with conversations."""
    if not threads_collection:
        return jsonify({"error": "Threads storage not configured"}), 500

    try:
        doc = threads_collection.find_one({"_id": ObjectId(thread_id)})
    except Exception:
        return jsonify({"error": "Invalid thread id"}), 400

    if not doc:
        return jsonify({"error": "Thread not found"}), 404

    return jsonify(serialize_thread(doc))


@app.route("/api/threads/<thread_id>", methods=["PUT"])
def api_threads_rename(thread_id):
    """Rename a thread."""
    if not threads_collection:
        return jsonify({"error": "Threads storage not configured"}), 500

    payload = request.get_json(silent=True) or {}
    new_title = (payload.get("title") or "").strip()
    if not new_title:
        return jsonify({"error": "Title cannot be empty"}), 400

    try:
        result = threads_collection.update_one(
            {"_id": ObjectId(thread_id)},
            {"$set": {"title": new_title, "updated_at": datetime.utcnow()}},
        )
    except Exception:
        return jsonify({"error": "Invalid thread id"}), 400

    if result.matched_count == 0:
        return jsonify({"error": "Thread not found"}), 404

    return jsonify({"status": "ok"})


@app.route("/api/threads/<thread_id>", methods=["DELETE"])
def api_threads_delete(thread_id):
    """Delete a thread."""
    if not threads_collection:
        return jsonify({"error": "Threads storage not configured"}), 500

    try:
        result = threads_collection.delete_one({"_id": ObjectId(thread_id)})
    except Exception:
        return jsonify({"error": "Invalid thread id"}), 400

    if result.deleted_count == 0:
        return jsonify({"error": "Thread not found"}), 404

    return jsonify({"status": "deleted"})


if __name__ == "__main__":
    app.run(debug=True)
