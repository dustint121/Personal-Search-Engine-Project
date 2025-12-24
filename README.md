# Intro

Hi! I'm your first Markdown file in **StackEdit**. If you want to learn about StackEdit, you can read me. If you want to play with Markdown, you can edit me. Once you have finished with me, you can create new files by opening the **file explorer** on the left corner of the navigation bar.


## Data Requirements to Access Word Documents from OneDrive
Have an account on https://portal.azure.com/

On Azure, go to Microsoft Entra ID.
1. Go under **Manage** --> **App Registration** --> Create **New Registration**
2. For New Registration, type a name for the app, select **"Personal Microsoft accounts only"**, skip "Redirect URL", and then register 
3. Go to new App under **App Registration**
4. Go under new app --> API Permissions, add **Microsoft Graph Delegated permissions for "Files.Read.All"** and grant Admin consent
5. Go under new app --> Authentication --> Settings, enable **"Allow public client flows"**
6. Go under new app --> Overview : Record the **"Application (client) ID"** for future reference in code


## In Project File after git cloning
Add **.env** file with
> CLIENT_ID= **[Client ID recorded in previous section]**

Run
>pip install -r requirements.txt

