from perplexity import Perplexity
import json
import os
from dotenv import load_dotenv
load_dotenv()

# 1. Set your API key (or export PERPLEXITY_API_KEY in your shell)
perplexity_key = os.getenv("PERPLEXITY_API_KEY")

# 2. Create client
client = Perplexity(
    api_key=perplexity_key,
    base_url="https://api.perplexity.ai",
)

# 3. Send one simple message
response = client.chat.completions.create(
    model="sonar",          # any supported model name
    messages=[{"role": "user", "content": "What is the latest news in AI research?"}],
)

# 4. Print the text answer
# print(response.choices[0].message.content)

# print everything
# print(response)

# Convert to a JSON-serializable object (Python dict)
response_json = response.model_dump()



# Option 1: pretty-print JSON to stdout
# print(json.dumps(response_json, indent=2))

#store json response to a file
os.makedirs("output", exist_ok=True)
with open("output/perplexity_response.json", "w") as f:
    json.dump(response_json, f, indent=4)