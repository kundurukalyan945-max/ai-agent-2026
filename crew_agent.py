from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def ask_agent(agent_name, system_prompt, user_prompt):
    print(f"\n{agent_name} is working...")
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    return response.choices[0].message.content

print("=" * 55)
print("  Phase 4 — Multi-Agent Job Application Crew")
print("=" * 55)
company = input("Enter company name: ")
role = input("Enter job role: ")
print(f"\nLaunching 3-agent crew for {role} at {company}...")

# ── AGENT 1: RESEARCHER ───────────────────────────────────
research = ask_agent(
    "Agent 1 — Company Researcher",
    "You are an expert job market researcher. Give detailed, actionable intelligence about companies for job seekers.",
    f"""Research {company} for someone applying for {role}.
    Cover:
    1. What {company} does and main products
    2. Their tech stack
    3. Company culture and values
    4. What they look for in {role} candidates
    5. Top 5 must-have keywords for the resume"""
)
print("\n✅ Agent 1 done!")

# ── AGENT 2: RESUME WRITER ────────────────────────────────
resume = ask_agent(
    "Agent 2 — Resume Specialist",
    "You are an ATS resume expert. Tailor resumes to get past ATS systems and impress hiring managers.",
    f"""Based on this company research:
{research}

Tailor Kalyan's resume for {role} at {company}.

Kalyan's background:
- B.Tech CSE AI/ML, SVCE Bengaluru 2026, CGPA 7.3
- Built AI Career Suite: 5 agents, live at ai-agent-2026.streamlit.app
- Deep Learning Object Detection (YOLOv8, 93-95% accuracy, published paper)
- Skills: Python, ML, LangChain, Groq API, Streamlit, Java
- Internships: SmartBridge AI/ML 6 months, JPMorgan, Deloitte

Give:
1. Tailored 3-line professional summary for {company}
2. 5 rewritten bullet points matching {company}'s needs
3. Top 8 ATS keywords to include"""
)
print("✅ Agent 2 done!")

# ── AGENT 3: INTERVIEW COACH ─────────────────────────────
interview = ask_agent(
    "Agent 3 — Interview Coach",
    "You are a senior technical interview coach. You know exactly what top companies ask and how to answer perfectly.",
    f"""Using this research about {company}:
{research}

And this tailored resume for Kalyan:
{resume}

Prepare Kalyan for his {role} interview at {company}:
1. Top 5 technical questions {company} asks with perfect answers
2. Top 3 behavioral questions with STAR answers using Kalyan's projects
3. 3 smart questions Kalyan should ask the interviewer
4. One key insider tip for {company}'s interview process"""
)
print("✅ Agent 3 done!")

# ── FINAL REPORT ─────────────────────────────────────────
report = f"""
{'='*55}
MULTI-AGENT REPORT: {role} at {company}
{'='*55}

AGENT 1 — COMPANY RESEARCH:
{research}

{'='*55}
AGENT 2 — TAILORED RESUME:
{resume}

{'='*55}
AGENT 3 — INTERVIEW PREP:
{interview}
"""

print(report)

filename = f"crew_{company.replace(' ','_')}_{role.replace(' ','_')}.txt"
with open(filename, "w") as f:
    f.write(report)
print(f"\n✅ Full report saved to {filename}")