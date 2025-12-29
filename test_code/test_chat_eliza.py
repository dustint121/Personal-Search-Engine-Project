import re
import random

# Simple reflection dictionary (user -> bot perspective)
REFLECTIONS = {
    "am": "are",
    "was": "were",
    "i": "you",
    "i'd": "you would",
    "i've": "you have",
    "i'll": "you will",
    "my": "your",
    "you": "me",
    "you're": "I'm",
    "you've": "I've",
    "you'll": "I'll",
    "your": "my",
    "yours": "mine",
    "me": "you",
}

def reflect(fragment: str) -> str:
    words = fragment.lower().split()
    reflected = []
    for w in words:
        reflected.append(REFLECTIONS.get(w, w))
    return " ".join(reflected)

# (pattern, [responses...]) like classic ELIZA
PAIRS = [
    (r".*\babout\b(.*)", [
        "What about %1?",
        "How do you feel about %1?",
        "Why are you thinking about %1 right now?",
    ]),
    (r"hi|hello|hey", [
        "Hello. How are you feeling today?",
        "Hi there. What would you like to talk about?"
    ]),
    (r"my name is (.*)", [
        "Nice to meet you, %1.",
        "Hello %1, how are you today?"
    ]),
    (r"i feel (.*)", [
        "Why do you feel %1?",
        "Do you often feel %1?",
        "What makes you feel %1?"
    ]),
    (r"i am (.*)", [
        "How long have you been %1?",
        "Why do you say you are %1?"
    ]),
    (r"(.*)mother(.*)", [
        "Tell me more about your mother.",
        "How is your relationship with your mother?"
    ]),
    (r"(.*)father(.*)", [
        "Tell me more about your father.",
        "Do you get along with your father?"
    ]),
    (r"(.*)because (.*)", [
        "Is that the real reason?",
        "What other reasons come to mind?"
    ]),
    (r"(.*)\?", [
        "Why do you ask that?",
        "What do you think?",
        "How would you answer that yourself?"
    ]),
    (r"(.*)", [
        "Please tell me more.",
        "Can you elaborate on that?",
        "How does that make you feel?",
        "Let's talk more about that."
    ]),
]

def eliza_respond(text: str) -> str:
    text = text.strip()
    for pattern, responses in PAIRS:
        m = re.match(pattern, text, re.IGNORECASE)
        if m:
            response = random.choice(responses)
            # Substitute captured groups (%1, %2, ...) with reflected text
            for i in range(1, len(m.groups()) + 1):
                group = m.group(i)
                response = response.replace(f"%{i}", reflect(group))
            return response
    return "Please go on."

def chat():
    print("ELIZA: How do you do. Please tell me your problem.")
    while True:
        user = input("YOU: ")
        if not user:
            continue
        if user.lower() in {"quit", "exit", "bye"}:
            print("ELIZA: Goodbye. Thank you for talking to me.")
            break
        reply = eliza_respond(user)
        print("ELIZA:", reply)

if __name__ == "__main__":
    chat()