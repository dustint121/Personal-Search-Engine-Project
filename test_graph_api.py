
import requests
import json
from msal import PublicClientApplication
import os
from dotenv import load_dotenv
load_dotenv()




if __name__ == "__main__":
    print("Microsoft Graph API Test")
    # OAuth details
    CLIENT_ID = os.getenv("CLIENT_ID")
    AUTHORITY = "https://login.microsoftonline.com/common"
    SCOPES = ["Files.Read.All"]


    # Create a PublicClientApplication
    app = PublicClientApplication(CLIENT_ID, authority=AUTHORITY)



    flow = app.initiate_device_flow(scopes=SCOPES)
    print("Go to", flow["verification_uri"], "and enter code:", flow["user_code"])

    result = app.acquire_token_by_device_flow(flow)

    if "access_token" in result:
        headers = {"Authorization": f"Bearer {result['access_token']}"}
        # url = "https://graph.microsoft.com/v1.0/me/drive/root/children"
        #for Document folder: 9E566E567FCDC108
        # url = "https://graph.microsoft.com/v1.0/drives/9E566E567FCDC108" # document folder id
        # url = "https://graph.microsoft.com/v1.0/drives/9E566E567FCDC108/items?$filter=endswith(name,'.docx')"

        # url = "https://graph.microsoft.com/v1.0/me/drive/root/search(q='Spark')?$filter=endswith(name,'.docx')&$select=name,id,webUrl"


        # url = "https://graph.microsoft.com/v1.0/drives/9E566E567FCDC108/items/9E566E567FCDC108!6747"  # text file metadata with downloadable URL
        # url = "https://graph.microsoft.com/v1.0/drives/9E566E567FCDC108/items/9E566E567FCDC108!6747/content"  # text file content
        url = "https://graph.microsoft.com/v1.0/drives/9E566E567FCDC108/items/9E566E567FCDC108!6559" #docx file metadata
        
        response = requests.get(url, headers=headers)
        # print(response.json())
        print("Response Status Code:", response.status_code)

        #unique case to handle file content download; not helpful for non-text files(.txt) with formatting
        if response.status_code == 200 and "content" in url: 
            
            print("File Content:")
            print(response.text)
        # if response.status_code == 200: # should give json response
        else: 
            #save json response to a file formatted with indentation
            os.makedirs("output", exist_ok=True)
            with open("output/graph_api.json", "w") as f:
                json.dump(response.json(), f, indent=4)
    else:
        print("Error:", result.get("error_description"))





    #https://developer.microsoft.com/en-us/graph/graph-explorer