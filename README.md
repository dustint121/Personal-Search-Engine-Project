# Intro

## About

My project repo for creating a personal search engine based on my academic and study notes stored on OneDrive (.docx files). Perplexity API will also be integrated for AI-based document summarization.

## Instructions to Access Word Documents from OneDrive
Have an account on https://portal.azure.com/

On Azure, go to Microsoft Entra ID.
1. Go under **Manage** --> **App Registration** --> Create **New Registration**
2. For New Registration, type a name for the app, select **"Personal Microsoft accounts only"**, skip "Redirect URL", and then register 
3. Go to new App under **App Registration**
4. Go under new app --> API Permissions, add **Microsoft Graph Delegated permissions for "Files.Read.All"** and grant Admin consent
5. Go under new app --> Authentication --> Settings, enable **"Allow public client flows"**
6. Go under new app --> Overview : Record the **"Application (client) ID"** for future reference in code



## Instructions to Access Perplexity Chatbot API
1. Have account on https://www.perplexity.ai/  
2. Generate API Key for usage and record for future reference


Official Documentation for API: https://docs.perplexity.ai/getting-started/overview



## In Project File after git cloning
Add **.env** file with
> CLIENT_ID= **[Microsoft Azure Client ID]**

> PERPLEXITY_API_KEY=**[Perplexity API key]**

Run
>pip install -r requirements.txt


## Useful Documentation
Official Documentation for Microsoft Graph API: 
https://learn.microsoft.com/en-us/graph/overview 
https://developer.microsoft.com/en-us/graph/graph-explorer

Official Documentation for Perplexity API: https://docs.perplexity.ai/getting-started/overview