import os
import json
import atexit
import requests

from msal import PublicClientApplication, SerializableTokenCache
from dotenv import load_dotenv

load_dotenv()

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



def get_token(app): #NOTE: token will last for 1 hour
    # 1. Try silent first (no user interaction if cache has valid tokens)
    accounts = app.get_accounts()
    if accounts:
        result = app.acquire_token_silent(SCOPES, account=accounts[0])
        if result and "access_token" in result:
            return result["access_token"]

    # 2. Fallback to device flow (first run or no valid refresh token)
    flow = app.initiate_device_flow(scopes=SCOPES)
    if "user_code" not in flow:
        raise RuntimeError("Failed to create device flow. Check app registration.")
    print("Go to", flow["verification_uri"], "and enter code:", flow["user_code"])
    result = app.acquire_token_by_device_flow(flow)
    if "access_token" in result:
        return result["access_token"]

    raise RuntimeError("Authentication failed: {}".format(result.get("error_description")))



if __name__ == "__main__":
    print("Microsoft Graph API Test")

    cache = load_cache()
    app = PublicClientApplication(client_id=CLIENT_ID, authority=AUTHORITY, token_cache=cache)
    access_token = get_token(app)

    headers = {"Authorization": f"Bearer {access_token}"}


    if access_token:
        print("Access token acquired successfully.")