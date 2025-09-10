
# from google import genai
from dotenv import load_dotenv
from time import sleep
import sys
import streamlit as st
import random
import os
from PyPDF2 import PdfReader
import re
import textwrap
from deep_translator import GoogleTranslator
from openai import OpenAI
load_dotenv()
client = OpenAI(api_key=os.getenv("openAIapikey"))
# Glossy Gradient Text with CSS
st.markdown(
    """
    <style>
    .glossy-text {
        font-size: 40px;
        font-weight: bold;
        background: linear-gradient(90deg, #ff7eb3, #ff758c, #ff7eb3);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-shadow: 2px 2px 5px rgba(255, 118, 136, 0.6);
    }
    </style>
    <div class="glossy-text">
        ✨ Welcome to AI Sakha ✨
    </div>
    """,
    unsafe_allow_html=True
)
#translation
lang_shortcut = {'english' : 'en',
                 'hindi' : 'hi',
                 'marathi' : 'mr',
                 'bengali' : 'bn',
                 'tamil' : 'ta',
                 'telugu' : 'te',
                 'japanese' : 'ja'}
def translate(data, user_language):
      
      user_language = user_language.lower()
      
      if user_language in lang_shortcut:
        target = lang_shortcut[user_language]
        result = GoogleTranslator(source='auto', target=target).translate(data)
        print(result)
  
        history = f'You asked: {data}\nTranslate to: {user_language}\nResult: {result}\n{'-'*40}\n'        
          
        with open('data.txt', 'a', encoding="utf-8") as f:
            f.write(f'{history}\n')
  
      else:
          print("Language not supported")


   
# -------------------------------
# Step 1: Extract text from PDF
# -------------------------------
def pdf_to_text(pdf_path):
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        if page.extract_text():
            text += page.extract_text() + "\n"
    return text

# -------------------------------
# Step 2: Split text into chunks (with overlap)
# -------------------------------
def chunk_text(text, chunk_size=200, overlap=50):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i+chunk_size])
        chunks.append(chunk)
    return chunks

# -------------------------------
# Step 3: Retrieve Top-K relevant chunks
# -------------------------------
def retrieve_chunks(query, chunks, top_k=3):
    results = []
    query_words = query.split()
    for chunk in chunks:
        score = sum(bool(re.search(qw, chunk, re.IGNORECASE)) for qw in query_words)
        if score > 0:
            results.append((score, chunk))
    results.sort(reverse=True, key=lambda x: x[0])
    return [c for _, c in results[:top_k]]

# -------------------------------
# Step 4: Generate answer using LLM
# -------------------------------
def answer_question(query, pdf_path):
    pdf_text = pdf_to_text(pdf_path)
    chunks = chunk_text(pdf_text, chunk_size=200, overlap=50)
    retrieved = retrieve_chunks(query, chunks, top_k=3)

    if not retrieved:
        return "❌ Sorry, no relevant information found in the PDF."

    context = "\n\n".join(retrieved)

    prompt = f"""
    You are a helpful assistant.
    Answer the question based only on the following context from a college notice PDF.

    Context:
    {context}

    Question: {query}

    Give a clear and concise answer."""
    response = client.chat.completions.create(
        model="gpt-4o-mini",   
        messages=[{"role": "user", "content": prompt}],
        temperature=0)
    return response.choices[0].message.content
#import streamlit as st
#import random
# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Namaste! How can I assist you Today?"}]

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("What is up?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)
        pdf_path = "FAQs-30-11-23.pdf"
        answer = answer_question(prompt, pdf_path)
        #print("Q:", query)
        #print("A:", answer)
    
        #client = genai.Client()
        #response = client.models.generate_content(
        #    model="gemini-2.5-flash", contents=prompt
        #    )
        #print(response.text)
        
    
    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = answer
        new_answer=translate(answer, 'hindi') 

    sleep(0.05)
                    # Add a blinking cursor to simulate typing
    message_placeholder.markdown(full_response + "▌")
    message_placeholder.markdown(full_response)
        # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content":(new_answer)})
def save_history(prompt, answer):
    # wrap answer text so each line has max 15 characters
    wrapped_answer = textwrap.fill(answer, width=15)

    history = (
        f"Your query:\n{prompt}\n"
        f"Response:\n{wrapped_answer}\n"
        f"{'-'*40}\n"
    )

    with open("result.txt", "a", encoding="utf-8") as f:
        f.write(history)

    
        