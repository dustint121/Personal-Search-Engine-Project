"""
test_chatbot.py

Simple terminal chatbot using Perplexity's Chat Completions API.
- Multi-turn conversation with in-memory history
- No file attachments, text only
"""

import os
from perplexity import Perplexity

from dotenv import load_dotenv

load_dotenv()

def main():
    # 1. Create client (expects PERPLEXITY_API_KEY in env)
    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key:
        raise RuntimeError("Please set PERPLEXITY_API_KEY in your environment.")

    client = Perplexity(api_key=api_key)

    # 2. Conversation state: system + running history
    messages = [
        {
            "role": "system",
            "content": (
                "You are a friendly chatbot in a terminal. "
                "Keep replies brief and to-the-point unless the user asks for detail."
                "You should not be referencing or citing any external sources (i.e. websites) but using your internal knowledge base without searching."
            ),
        }
    ]

    print("Perplexity terminal chat. Type 'exit' or 'quit' to stop.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting chat.")
            break

        if user_input.lower() in {"exit", "quit"}:
            print("Goodbye!")
            break

        if not user_input:
            continue

        # 3. Append user message to history
        messages.append({"role": "user", "content": user_input})

        # 4. Call Perplexity chat completions
        try:
            response = client.chat.completions.create(
                model="sonar",  # or "sonar-pro", etc. [web:58][web:67]
                messages=messages,
            )
        except Exception as e:
            print(f"[Error from API] {e}")
            # Optionally remove last user message on failure
            messages.pop()
            continue

        # 5. Extract assistant reply
        reply = response.choices[0].message.content
        print(f"Assistant: {reply}\n")

        # 6. Add assistant reply to history so context is preserved
        messages.append({"role": "assistant", "content": reply})


if __name__ == "__main__":
    main()
