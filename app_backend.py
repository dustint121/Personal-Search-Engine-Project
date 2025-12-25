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

# === OneDrive / Microsoft Graph configuration ===[file:194][file:193]
CLIENT_ID = os.getenv("CLIENT_ID")
AUTHORITY = "https://login.microsoftonline.com/common"
SCOPES = ["Files.Read.All"]
CACHE_FILE = os.path.join(os.path.dirname(__file__), "token_cache.bin")
ONEDRIVE_DOCUMENTS_FOLDER_ID = os.getenv("ONEDRIVE_DOCUMENTS_FOLDER_ID")

# === Perplexity API configuration ===[file:193]
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
PPLX_CLIENT = Perplexity(
    api_key=PERPLEXITY_API_KEY,
    base_url="https://api.perplexity.ai",
)


def load_cache():
    cache = SerializableTokenCache()
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            cache.deserialize(f.read())
    # persist cache on exit only if changed
    atexit.register(
        lambda: open(CACHE_FILE, "w").write(cache.serialize())
        if cache.has_state_changed
        else None
    )
    return cache


def get_token(msal_app: PublicClientApplication) -> str:
    """
    Get an access token using MSAL, preferring silent auth and
    falling back to device code flow on first run.[file:194][file:193]
    """
    # 1. Try silent first
    accounts = msal_app.get_accounts()
    if accounts:
        result = msal_app.acquire_token_silent(SCOPES, account=accounts[0])
        if result and "access_token" in result:
            return result["access_token"]

    # 2. Device code flow if no valid token/refresh token
    flow = msal_app.initiate_device_flow(scopes=SCOPES)
    if "user_code" not in flow:
        raise RuntimeError("Failed to create device flow. Check app registration.")
    print("Go to", flow["verification_uri"], "and enter code:", flow["user_code"])
    result = msal_app.acquire_token_by_device_flow(flow)
    if "access_token" in result:
        return result["access_token"]

    raise RuntimeError(
        "Authentication failed: {}".format(result.get("error_description"))
    )


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
    """
    Call Microsoft Graph /me/drive/root/search for .docx files
    that match the query string and return a simple list of
    {id, title, url} objects for the frontend.[file:194]
    """
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

    # Optional: still save raw output for debugging
    os.makedirs("output", exist_ok=True)
    with open("output/query_result.json", "w") as f:
        json.dump(data, f, indent=4)

    items = data.get("value", [])
    results = [
        {
            "id": item.get("id"),
            "title": item.get("name", "(no name)"),
            "url": item.get("webUrl", "#"),
        }
        for item in items
    ]
    return results


def retrieve_document_content(item_id: str) -> bytes:
    """
    Download the raw file bytes for a OneDrive item using its id.[file:193]
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


# === Flask API routes ===

@app.route("/api/search")
def api_search():
    q = request.args.get("q", "")
    try:
        results = search_onedrive_docx(q)
        return jsonify(results)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/summarize", methods=["POST"])
def api_summarize():
    """
    Body: { "ids": ["id1", "id2", ...] }
    Returns: { "summary": "text from Perplexity" }
    """
    payload = request.get_json(silent=True) or {}
    ids = payload.get("ids", [])
    if not ids:
        return jsonify({"error": "No ids provided"}), 400

    try:
        # 1. Fetch document bytes for each id
        file_contents = []
        for item_id in ids:
            content_bytes = retrieve_document_content(item_id)
            encoded = base64.b64encode(content_bytes).decode("utf-8")
            file_contents.append(encoded)

        # 2. Build Perplexity content array with static prompt[file:193]
        prompt = (
            "You are summarizing a set of Microsoft Word documents from my OneDrive. "
            "For each attached document, provide a short (2–3 sentence) summary. "
            "Then provide a brief (3–5 bullet) overall summary that synthesizes key themes "
            "across all documents."
        )

        content = [
            {
                "type": "text",
                "text": prompt,
            }
        ]

        # For now, send each file as a base64 'file_url.url' block (mirroring test_both_api).[file:193]
        for encoded_data in file_contents:
            content.append(
                {
                    "type": "file_url",
                    "file_url": {
                        "url": encoded_data
                    },
                }
            )

        # 3. Call Perplexity
        response = PPLX_CLIENT.chat.completions.create(
            model="sonar",
            messages=[
                {"role": "user", "content": content},
            ],
        )

        summary_text = response.choices[0].message.content
        return jsonify({"summary": summary_text})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# NOTE: do not put app.run(...) here; app_front.py calls it.
