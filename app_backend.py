import os
import json
import atexit

import requests
from flask import Flask, jsonify, request
from msal import PublicClientApplication, SerializableTokenCache
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# === OneDrive / Microsoft Graph configuration ===[file:111]
CLIENT_ID = os.getenv("CLIENT_ID")
AUTHORITY = "https://login.microsoftonline.com/common"
SCOPES = ["Files.Read.All"]
CACHE_FILE = os.path.join(os.path.dirname(__file__), "token_cache.bin")


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
    falling back to device code flow on first run.[file:111]
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


def search_onedrive_docx(query: str):
    """
    Call Microsoft Graph /me/drive/root/search for .docx files
    that match the query string and return a simple list of
    {title, url} objects for the frontend.[file:111]
    """
    if not query:
        return []

    cache = load_cache()
    msal_app = PublicClientApplication(
        client_id=CLIENT_ID,
        authority=AUTHORITY,
        token_cache=cache,
    )
    access_token = get_token(msal_app)
    headers = {"Authorization": f"Bearer {access_token}"}

    # Graph search endpoint, filtered to .docx and minimal fields[file:111]
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

    # Graph returns items under "value"; map to simple list
    items = data.get("value", [])
    results = [
        {
            "title": item.get("name", "(no name)"),
            "url": item.get("webUrl", "#"),
        }
        for item in items
    ]
    return results


# === Flask API route used by ReactPy frontend ===
@app.route("/api/search")
def api_search():
    q = request.args.get("q", "")
    try:
        results = search_onedrive_docx(q)
        return jsonify(results)
    except Exception as e:
        # Simple error handling for now
        return jsonify({"error": str(e)}), 500

# NOTE: do not put app.run(...) here; app_frontend.py calls it.