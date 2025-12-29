
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv
import os

load_dotenv()

mongo_url = os.getenv("MONGO_URL")
print("mongo_url:", mongo_url)
# Create a new client and connect to the server
client = MongoClient(mongo_url, server_api=ServerApi('1'))

# Send a ping to confirm a successful connection
# try:
#     client.admin.command('ping')
#     print("Pinged your deployment. You successfully connected to MongoDB!")
# except Exception as e:
#     print(e)

if __name__ == "__main__":
    db = client["test_db"]
    collection = db["conversations"]

    #what if database does not exist? it will be created when we insert a document
    #what if collection does not exist? it will be created when we insert a document
    # Example document to insert
    # conversation = {
    #     "user": "I feel sad today.",
    #     "eliza": "Why do you feel sad today?"
    # }

    conversation_list = [
        {
            "user": "I feel sad today.",
            "eliza": "Why do you feel sad today?"
        },
        {
            "user": "My name is John.",
            "eliza": "Nice to meet you, John!"
        }
    ]

    #insert conversation list as one document
    result = collection.insert_one({"conversations": conversation_list})
    print(f"Inserted document with id: {result.inserted_id}")

    id = result.inserted_id

    #update conversation list with more conversations
    conversation_list.append({
        "user": "I am feeling better now.",
        "eliza": "That's great to hear!"
    })

    #update the document with the new conversation list
    collection.update_one({"_id": id}, {"$set": {"conversations": conversation_list}})




    #delete the document
    # collection.delete_one({"_id": id})
    # print(f"Deleted document with id: {id}")