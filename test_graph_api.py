import os
import json
import atexit
import requests

from msal import PublicClientApplication, SerializableTokenCache
from dotenv import load_dotenv

load_dotenv()

ONEDRIVE_DOCUMENTS_FOLDER_ID = os.getenv("ONEDRIVE_DOCUMENTS_FOLDER_ID")

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
 

    # Uncomment one of the following URLs to test different API endpoints
    # url = "https://graph.microsoft.com/v1.0/me/drive/root/children"
    #for Document folder: 9E566E567FCDC108
    # url = "https://graph.microsoft.com/v1.0/drives/9E566E567FCDC108" # document folder id
    # url = "https://graph.microsoft.com/v1.0/drives/9E566E567FCDC108/items?$filter=endswith(name,'.docx')"

    # url = "https://graph.microsoft.com/v1.0/me/drive/root/search(q='Spark')?$filter=endswith(name,'.docx')&$select=name,id,webUrl"


    # url = "https://graph.microsoft.com/v1.0/drives/9E566E567FCDC108/items/9E566E567FCDC108!6747"  # text file metadata with downloadable URL
    # url = "https://graph.microsoft.com/v1.0/drives/9E566E567FCDC108/items/9E566E567FCDC108!6747/content"  # text file content
    url = "https://graph.microsoft.com/v1.0/drives/9E566E567FCDC108/items/9E566E567FCDC108!6559" #docx file metadata
    

    url = f"https://graph.microsoft.com/v1.0/drives/{ONEDRIVE_DOCUMENTS_FOLDER_ID}/items/9E566E567FCDC108!6559"
    response = requests.get(url, headers=headers)
    # print("Response Status Code:", response.status_code)

    os.makedirs("output", exist_ok=True)
    if response.status_code == 200 and "content" in url: #will return raw file content
        # print("File Content:")
        # print(response.text)
        with open("output/graph_api_file_content.txt", "w", encoding="utf-8") as f:
            f.write(response.text)
    else:
        with open("output/graph_api.json", "w") as f:
            json.dump(response.json(), f, indent=4)

