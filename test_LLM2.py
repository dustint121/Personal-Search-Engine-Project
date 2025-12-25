from perplexity import Perplexity
import os
import json
import base64
from dotenv import load_dotenv


if __name__ == "__main__":
    load_dotenv()
    print("Perplexity API File Test")

    perplexity_key = os.getenv("PERPLEXITY_API_KEY")

    client = Perplexity(
        api_key=perplexity_key,
        base_url="https://api.perplexity.ai",
    )

    # 1. Read local file or provide file URL
    # FILE_PATH = "example.txt"  # change to your file
    # with open(FILE_PATH, "r", encoding="utf-8") as f:
    #     file_text = f.read()

    encoded_file = None

    # FILE_PATH = "C:\\Users\\dusti\\Downloads\\Notes Search Engine Project\\test_files\\A for-loop is all you need. For solving the inverse problem.pdf" # change to your file
    FILE_PATH = "C:\\Users\\dusti\\Downloads\\Notes Search Engine Project\\test_files\\Dustin_Tran_Resume.docx"
    with open(FILE_PATH, "rb") as f:
        file_data = f.read()
        encoded_file = base64.b64encode(file_data).decode('utf-8')
    
    file_url = None
    # Examples of file URLs:
    # file_url = "https://drive.google.com/uc?export=download&id=1kHLl90qURduXY4ECZUWR3qHbx0IIYG-B"
    # file_url = "https://teach.starfall.com/materials/books/learn-to-read/1-Zac-by-Starfall.pdf"
    # file_url = "https://www.gutenberg.org/cache/epub/77539/pg77539-images.html"

    if encoded_file:
        file_url = encoded_file
    # 2. Ask a question about the file

    # prompt = "Can you see the images in the attached document?"
    # prompt = "Can you see Figure 2 in the attached document? If so, describe it."
    # prompt = "Summarize this document"
    prompt = "Please count the number of attached documents for this query. Then summarize the content of each document in a few sentences."

    content =  [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "file_url",
                        "file_url": {
                            "url": file_url 
                        },
                    }
                ]

    file_url = "https://www.gutenberg.org/cache/epub/77539/pg77539-images.html"

    content.append(
        {   "type": "file_url",
            "file_url": {
                "url": file_url
            }
        }
    )

    response = client.chat.completions.create(
        model="sonar",
        messages=[
            {"role": "user", "content": content},
        ],
    )

    # 3. Convert to JSON-serializable dict
    response_json = response.model_dump()

    # Pretty-print JSON (or return this from a function)
    # print(json.dumps(response_json, indent=2))

    # Store JSON response to a file; create output directory if it doesn't exist
    os.makedirs("output", exist_ok=True)
    with open("output/perplexity_file_response.json", "w") as f:
        json.dump(response_json, f, indent=4)

    # Store just the answer text to a file
    with open("output/perplexity_file_answer.txt", "w", encoding="utf-8") as f:
        f.write(response.choices[0].message.content)



