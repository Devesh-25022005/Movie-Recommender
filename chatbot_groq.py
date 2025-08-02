import streamlit as st
import openai 
from dotenv import load_dotenv
import os

load_dotenv()

def run_chatbot():
    groq_key = os.getenv("GROQ_API_KEY")
    openai.api_base = "https://api.groq.com/openai/v1"
    openai.api_key = groq_key 
   

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    user_input = st.chat_input("Ask about any movie")

    if user_input:
        st.session_state.chat_history.append({"role":"user", "content": user_input})
        with st.spinner("Thinking..."):
         response= openai.ChatCompletion.create(
             model="llama3-8b-8192",
             messages = [
                {"role":"user", "content": user_input},
                {"role":"system", "content":"You are a helpful and knowledgeable movie expert."},
                *st.session_state.chat_history

             ],
             max_tokens= 500,
             temperature = 0.7
         )
         reply = response.choices[0].message.content
         st.session_state.chat_history.append({"role":"assistant", "content": reply})

    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
