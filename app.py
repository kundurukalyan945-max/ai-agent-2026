import streamlit as st
from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

st.set_page_config(page_title="Kalyan's AI Career Suite", page_icon="🤖", layout="wide")
st.title("🤖 Kalyan's AI Career Suite")
st.caption("Built with Python + Groq API — Free & Local")

tab1, tab2, tab3 = st.tabs(["🧠 AI Career Coach", "📄 Resume Tailor", "🎯 Interview Prep"])

# ── TAB 1: AI COACH ──────────────────────────────────
with tab1:
    st.header("AI Career Coach")
    st.caption("Remembers your full conversation")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    if prompt := st.chat_input("Ask your career coach anything..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": "You are Kalyan's AI career coach. He is a B.Tech CSE AI/ML student in Bengaluru targeting AI/ML jobs in 2026. Be encouraging and practical."},
                    ] + st.session_state.messages
                )
                reply = response.choices[0].message.content
                st.write(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})

# ── TAB 2: RESUME TAILOR ─────────────────────────────
with tab2:
    st.header("Resume Tailor")
    st.caption("Paste a job description → get tailored resume bullets instantly")

    job_desc = st.text_area("Paste job description here:", height=200)

    if st.button("✨ Tailor My Resume", type="primary"):
        if job_desc:
            with st.spinner("Tailoring your resume..."):
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": "You are an expert ATS resume writer."},
                        {"role": "user", "content": f"""My resume: B.Tech CSE AI/ML, SVCE Bengaluru 2026, CGPA 7.3.
Project: Deep Learning Object Detection for Visually Impaired (YOLOv8, TTS, Streamlit, 93-95% accuracy).
Skills: Python, ML, Deep Learning, LangChain, Groq API, AI Agents.

Job description: {job_desc}

Give me:
1. Top 5 ATS keywords to include
2. 3 rewritten project bullet points matching this job
3. A 3-line professional summary for this role"""}
                    ]
                )
                result = response.choices[0].message.content
                st.success("Done!")
                st.markdown(result)
        else:
            st.warning("Please paste a job description first!")

# ── TAB 3: INTERVIEW PREP ────────────────────────────
with tab3:
    st.header("Interview Prep")
    st.caption("Answer questions and get scored by AI")

    questions = [
        "Tell me about yourself and why you want to work in AI/ML?",
        "What is machine learning in simple terms?",
        "What is the difference between supervised and unsupervised learning?",
        "Tell me about your Object Detection project and challenges you faced.",
        "What is overfitting and how do you fix it?"
    ]

    question = st.selectbox("Choose a question:", questions)
    answer = st.text_area("Your answer:", height=150)

    if st.button("📊 Score My Answer", type="primary"):
        if answer:
            with st.spinner("Scoring your answer..."):
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[
                        {"role": "system", "content": "You are a strict technical interviewer. Score out of 10. Be direct and fast."},
                        {"role": "user", "content": f"Question: {question}\nAnswer: {answer}\n\nRespond with:\nSCORE: X/10\nGOOD: (one line)\nIMPROVE: (one line)\nBETTER ANSWER: (2-3 lines)"}
                    ]
                )
                feedback = response.choices[0].message.content
                lines = feedback.split('\n')
                score_line = [l for l in lines if 'SCORE' in l]
                if score_line:
                    score = int(score_line[0].split('/')[0].replace('SCORE:', '').strip())
                    color = "green" if score >= 7 else "orange" if score >= 5 else "red"
                    st.markdown(f"### :{color}[{score_line[0]}]")
                st.markdown(feedback)
        else:
            st.warning("Type your answer first!")