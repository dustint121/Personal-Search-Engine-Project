import json


# Function to read JSON data from file "drive_root_children.json"

if __name__ == "__main__":
    print("Reading JSON data from drive_root_children.json")
    data = None
    with open("drive_root_children.json", "r") as f:
        data = json.load(f)
    
    # Get the list of item names from the JSON data
    items_list = []
    if "value" in data:
        items_list = [item["name"] for item in data["value"]]
    print("Items List:", items_list)