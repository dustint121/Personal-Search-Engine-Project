  

# About
My project repo for creating a personal search engine/chatbot application based on my academic and study notes stored on OneDrive (.docx files). Perplexity API will also be integrated for AI-based document summarization.
 
This project relies on the Microsoft Graph API for accessing documents and metadata from Microsoft and the Perplexity API for LLM-generated assisstance.

The application will have three pages.

The first page is a search engine that will search for relevant documents in the OneDrive folder based on a search query. It has URL links to the documents and AI summarization capability.
  
The second page is a chatbot using the Perplexity API to be able to converse with the user and allow referencing of existing note-related documents.

The third page has a basic keyword-based chatbot based on the original Eliza chatbot from 1966 along with a tab presenting a brief history of chatbots.
  

# Instructions for Running Code Repo on Local Machine
## Access Perplexity Chatbot API

Have account on https://www.perplexity.ai/

1. Generate API Key for usage and record for future reference


## Access Personal Files from OneDrive (Part 1)

Have an account on https://portal.azure.com/

On Azure, go to Microsoft Entra ID.

1. Go under **Manage** --> **App Registration** --> Create **New Registration**

2. For New Registration, type a name for the app, select **"Personal Microsoft accounts only"**, skip "Redirect URL", and then register

3. Go to new App under **App Registration**

4. Go under new app --> API Permissions, add **Microsoft Graph Delegated permissions for "Files.Read.All" and "offline_access"** and grant Admin consent to both

5. Go under new app --> Authentication --> Settings, enable **"Allow public client flows"**

6. Go under new app --> Overview : Record the **"Application (client) ID"** for future reference in code

  
## Access Personal Files from OneDrive (Part 2)

Go to https://developer.microsoft.com/en-us/graph/graph-explorer and log in with Microsoft account.

1. Type in and run query for: "https://graph.microsoft.com/v1.0/me/drive/root/children"

2. Record **'driveID'** for "Documents folder (should be the only driveID value available.

## Access Perplexity Chatbot API

1. Have account on https://www.perplexity.ai/

2. Generate API Key for usage and record for future reference

## Setup MongoDB 

Go to https://cloud.mongodb.com/ and log in with account.

1. Create a cluster and record the "connection string"/"uri" (looks like a URL) from the "Connect New" button.
  
  

## In Project File after git cloning

1. Add **.env** file with

> PERPLEXITY_API_KEY=**[Perplexity API key]**

> CLIENT_ID= **[Microsoft Azure Client ID]**

>ONEDRIVE_DOCUMENTS_FOLDER_ID=**[driveID]**

>MONGO_URL=**[MONGODB Connection String]**

>USAGE_PASSWORD=**[any string works]**

2. Run
>pip install -r requirements.txt

3. Run
>python get_authentication.py

Will generate token_cache.bin for authencation after logging into Microsoft account with external link. Should be a one-time request before automatically giving recredentials for every future request/reset.

4. Run
>python download_all_notes.py

Will download majority of metadata for note-related .docx documents into notes_metadata.json

5. Run
>python app_backend.py

Will start up application.

  

## Useful Documentation

Official Documentation for Microsoft Graph API:

https://learn.microsoft.com/en-us/graph/overview

https://developer.microsoft.com/en-us/graph/graph-explorer

  

Official Documentation for Perplexity API: https://docs.perplexity.ai/getting-started/overview