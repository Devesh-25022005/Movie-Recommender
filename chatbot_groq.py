import streamlit as st
import openai
from dotenv import load_dotenv
import os

load_dotenv()
openai.api_base = "https://openrouter.ai/api/v1"
openai.api_key = st.secrets["OPEN_ROUTER_API_KEY"]

FREE_MODELS = {
    "DeepSeek R1": "deepseek/deepseek-r1:free",
    "DeepSeek R1‑0528": "deepseek/deepseek-r1-0528:free",
    "DeepSeek V3‑0324": "deepseek/deepseek-v3-0324:free",
    "GLM 4.5 Air": "z-ai/glm-4.5-air:free",
}

def run_chatbot():
    model_name = st.selectbox("Choose a free model", list(FREE_MODELS.keys()))
    model_id = FREE_MODELS[model_name]

    if "history" not in st.session_state:
        st.session_state.history = []

    user_input = st.chat_input("Ask anything about movies")
    if user_input:
        st.session_state.history.append({"role": "user", "content": user_input})
        with st.spinner("Generating response..."):
            resp = openai.ChatCompletion.create(
                model=model_id,
                messages=[{"role": "system", "content": "You are a friendly and knowledgeable movie expert."},
                          *st.session_state.history],
                max_tokens=1000,
                temperature=0.7,
            )
        reply = resp.choices[0].message.content
        st.session_state.history.append({"role": "assistant", "content": reply})

    for msg in st.session_state.history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
