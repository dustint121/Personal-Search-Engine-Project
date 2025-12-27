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

    cache = load_cache()
    app = PublicClientApplication(client_id=CLIENT_ID, authority=AUTHORITY, token_cache=cache)
    access_token = get_token(app)

    headers = {"Authorization": f"Bearer {access_token}"}



    url = f"https://graph.microsoft.com/v1.0/me/drive/root/search(q='notes')?$filter=endswith(name,'.docx')&$select=name,id,webUrl"


    response = requests.get(url, headers=headers)

    list_of_notes = response.json()['value']

    #write list of notes to json file
    with open("notes_metadata.json", "w") as f:
        json.dump(list_of_notes, f)

    # print(f"Found {len(list_of_notes)} notes.")
    # count = 0
    # os.makedirs("note_files", exist_ok=True)
    # for note in list_of_notes:
    #     #check if file already exists
    #     if os.path.exists(f"note_files/{note['id']}"):
    #         print(f"File {note['name']} already exists. Skipping download.")
    #         count += 1
    #         continue
    #     print(f"Downloading note #{count + 1} of {len(list_of_notes)}: {note['name']}")
    #     note_id = note['id']
    #     download_url = f"https://graph.microsoft.com/v1.0/me/drive/items/{note_id}/content"
    #     download_response = requests.get(download_url, headers=headers)
    #     if download_response.status_code == 200:    
    #         # store as binary file
    #         with open(f"note_files/{note_id}", "wb") as f:
    #             f.write(download_response.content)
    #     else:
    #         print(f"Failed to download {note['name']}")
    #     count += 1


#total of 51 files for about 750 MB total

# 10-20 minutes to download all files; may need to run multiple times due to requests timeouts