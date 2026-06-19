from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# This is the memory — a list that grows with every message
conversation_history = []

# This is the personality — your personal AI career coach
system_prompt = """You are Kalyan's personal AI career coach. 
You know that Kalyan is learning Python, Machine Learning, and Generative AI.
His goal is to get an AI/ML job or internship in Bengaluru in 2026.
He is a beginner who learns best with simple explanations and examples.
Always be encouraging, specific, and practical.
When he asks about code, give simple working examples.
When he asks about jobs, give real actionable advice."""

print("=" * 50)
print("  Your Personal AI Career Coach is ready!")
print("=" * 50)
print("I remember everything you tell me in this session.")
print("Type 'quit' to exit, 'clear' to reset memory.")
print("=" * 50)

while True:
    question = input("\nYou: ")

    if question.lower() == "quit":
        print("Coach: Good work today Kalyan! Keep building!")
        break

    if question.lower() == "clear":
        conversation_history = []
        print("Coach: Memory cleared! Fresh start.")
        continue

    if question.strip() == "":
        continue

    # Add user message to memory
    conversation_history.append({
        "role": "user",
        "content": question
    })

    # Send full conversation history to AI
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt}
        ] + conversation_history
    )

    answer = response.choices[0].message.content

    # Add AI reply to memory too
    conversation_history.append({
        "role": "assistant",
        "content": answer
    })

    print(f"\nCoach: {answer}")
    print("-" * 50)
    print(f"(Memory: {len(conversation_history)//2} messages remembered)")