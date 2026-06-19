from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

print("Your AI is ready! Type your question below.")
print("(Type 'quit' to exit)")
print("-" * 40)

while True:
    question = input("You: ")
    
    if question.lower() == "quit":
        print("Bye!")
        break
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": question}]
    )
    
    answer = response.choices[0].message.content
    print(f"AI: {answer}")
    print("-" * 40)