import os
import base64
import json
import atexit
import requests
from perplexity import Perplexity
from msal import PublicClientApplication, SerializableTokenCache
from dotenv import load_dotenv

load_dotenv()

CLIENT_ID = os.getenv("CLIENT_ID")
AUTHORITY = "https://login.microsoftonline.com/common"
SCOPES = ["Files.Read.All"]
CACHE_FILE = os.path.join(os.path.dirname(__file__), "token_cache.bin")
ONEDRIVE_DOCUMENTS_FOLDER_ID = os.getenv("ONEDRIVE_DOCUMENTS_FOLDER_ID")



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


def retrieve_document_content(query_id, access_token):
    cache = load_cache()
    app = PublicClientApplication(client_id=CLIENT_ID, authority=AUTHORITY, token_cache=cache)
    access_token = get_token(app)

    headers = {"Authorization": f"Bearer {access_token}"}


    query_id = input("Enter id: ")

    url = f"https://graph.microsoft.com/v1.0/drives/{ONEDRIVE_DOCUMENTS_FOLDER_ID}/items/{query_id}/content"

    response = requests.get(url, headers=headers)

    response_text = response.text
    print("Document content:")
    print(response_text)


def retrieve_document_content(query_id, access_token):
    headers = {"Authorization": f"Bearer {access_token}"}
    url = f"https://graph.microsoft.com/v1.0/drives/{ONEDRIVE_DOCUMENTS_FOLDER_ID}/items/{query_id}/content"
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise RuntimeError(f"Failed to retrieve document content from {url}: {response.status_code} {response.text}")
    
    file_bytes = response.content
    return file_bytes
    # return response.text
    


if __name__ == "__main__":
    print("Microsoft Graph API Test")

    cache = load_cache()
    app = PublicClientApplication(client_id=CLIENT_ID, authority=AUTHORITY, token_cache=cache)
    access_token = get_token(app)
    # query_id = input("Enter id: ")
    query_id = "9E566E567FCDC108!6559"

    file_data = retrieve_document_content(query_id, access_token)

    # convert to bytes
    # response_text = response_text.encode('utf-8')

    print("Document content retrieved successfully.")

    # Encode the file content to base64
    encoded_file_data = base64.b64encode(file_data).decode('utf-8')
    



    
    file_data = {
        "type": "file_url",
        "file_url": {
            "url": encoded_file_data
        }
    }


    prompt = "Please count the number of attached documents for this query. Then summarize the content of each document in a few sentences."
    content =  [
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]

    content.append(file_data)



    perplexity_key = os.getenv("PERPLEXITY_API_KEY")

    client = Perplexity(
        api_key=perplexity_key,
        base_url="https://api.perplexity.ai",
    )

    response = client.chat.completions.create(
        model="sonar",
        messages=[
            {"role": "user", "content": content},
        ],
    )

    # 3. Convert to JSON-serializable dict
    response_json = response.model_dump()


    os.makedirs("output", exist_ok=True)
    with open("output/two_api_response.txt", "w") as f:
        f.write(response.choices[0].message.content)