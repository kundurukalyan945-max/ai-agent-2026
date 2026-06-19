from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

questions = [
    "Tell me about yourself and why you want to work in AI/ML?",
    "Explain what machine learning is in simple terms.",
    "What is the difference between supervised and unsupervised learning?",
    "Tell me about your Object Detection project. What challenges did you face?",
    "What is overfitting and how do you fix it?",
]

print("=" * 50)
print("  AI Interview Coach — Kalyan's Prep Session")
print("=" * 50)
print("I will ask you 5 real interview questions.")
print("Answer each one, then I will score and improve it.")
print("=" * 50)

scores = []

for i, question in enumerate(questions):
    print(f"\nQ{i+1}: {question}")
    print("-" * 40)
    answer = input("Your answer: ")

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": """You are a strict but helpful technical interviewer at a top AI company in Bengaluru.
Score answers out of 10. Be fast and direct.
Format your response exactly like this:
SCORE: X/10
WHAT YOU DID WELL: (one line)
IMPROVE THIS: (one line)
BETTER ANSWER: (2-3 lines max)"""
            },
            {
                "role": "user",
                "content": f"Question: {question}\nCandidate answer: {answer}"
            }
        ]
    )

    feedback = response.choices[0].message.content
    print("\n" + feedback)
    print("-" * 40)

    try:
        score_line = [l for l in feedback.split('\n') if 'SCORE' in l][0]
        score = int(score_line.split('/')[0].replace('SCORE:', '').strip())
        scores.append(score)
    except:
        scores.append(5)

print("\n" + "=" * 50)
print("SESSION COMPLETE!")
print(f"Your average score: {sum(scores)//len(scores)}/10")
print(f"Individual scores: {scores}")
if sum(scores)//len(scores) >= 7:
    print("Great job! You are interview ready!")
else:
    print("Keep practicing! Run this again tomorrow.")
print("=" * 50)