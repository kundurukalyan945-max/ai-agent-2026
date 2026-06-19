from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MY_RESUME = """
Name: Kalyan
Degree: B.Tech CSE (AI/ML) - Sri Venkateswara College of Engineering, Bengaluru (2026)
CGPA: 7.3

PROJECTS:
- Deep Learning Object Detection Framework for Visually Impaired Users
  Built YOLOv8 model with offline TTS pipeline and Streamlit deployment
  Achieved 93-95% detection accuracy

SKILLS:
- Python, Machine Learning, Deep Learning
- YOLOv8, TTS, Streamlit
- Java, SQL

CURRENTLY LEARNING:
- LangChain, AI Agents, Generative AI
- Built AI chatbot with memory using Groq API
- Built job scraper agent using Python
"""

print("=" * 50)
print("  Resume Tailor Agent")
print("=" * 50)
print("Paste the job description below.")
print("When done, type DONE on a new line and press Enter.")
print("=" * 50)

lines = []
while True:
    line = input()
    if line.strip() == "DONE":
        break
    lines.append(line)

job_description = "\n".join(lines)

print("\nTailoring your resume... please wait...")

response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[
        {
            "role": "system",
            "content": """You are an expert resume writer and ATS optimization specialist.
Your job is to tailor resumes to match job descriptions exactly.
Always use strong action verbs. Match keywords from the job description exactly.
Format output cleanly and professionally."""
        },
        {
            "role": "user",
            "content": f"""Here is my resume:
{MY_RESUME}

Here is the job description I am applying for:
{job_description}

Please do these 3 things:
1. List the TOP 5 keywords from the job description I must include
2. Rewrite my project bullet points to match this job description
3. Write a 3-line professional summary for this specific role

Keep it concise and ATS-friendly."""
        }
    ]
)

result = response.choices[0].message.content
print("\n" + "=" * 50)
print("TAILORED RESUME OUTPUT")
print("=" * 50)
print(result)

# Save to file
with open("tailored_resume.txt", "w") as f:
    f.write(f"JOB DESCRIPTION:\n{job_description}\n\n")
    f.write(f"TAILORED OUTPUT:\n{result}")

print("\n" + "=" * 50)
print("Saved to tailored_resume.txt")
