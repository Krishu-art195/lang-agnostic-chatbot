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
from langdetect import detect
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
    
def translate(data,target_lang):
    """Detects language and translates 'data' to 'target_lang'. Returns the translated string(or original id detection unsupported)
    """
    try:
        u_lang=detect(data)
    except Exception:
        return data 

    if u_lang in lang_shortcut.values():
        try:
            result = GoogleTranslator(source=u_lang,target=target_lang).translate(data)
        
  
            history = f'You asked: {data}\nDetected: {u_lang}\nResult: {result}\n{'-'*40}\n'        
          
            with open('data.txt', 'a', encoding="utf-8") as f:
                f.write(history)
            return result
        except Exception:
            return data
    else:
        return data


   
# -------------------------------
# Step 1: Extract text from PDF
# -------------------------------
def pdf_to_text(pdf_path):
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        page_text=page.extract_text()
        if page_text:
            text += page_text + "\n"
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
    lang=detect(query)
    en_query=translate(query,'en')
    pdf_text = pdf_to_text(pdf_path)
    chunks = chunk_text(pdf_text, chunk_size=200, overlap=50)
    retrieved = retrieve_chunks(en_query, chunks, top_k=3)
    

    if not retrieved:
        return None

    context = "\n\n".join(retrieved)

    prompt = f"""
    You are a helpful assistant.
    Answer the question based only on the following context from a college notice PDF.

    Context:
    {context}

    Question: {en_query}

    Give a clear and concise answer."""
    response = client.chat.completions.create(
        model="gpt-4o-mini",   
        messages=[{"role": "user", "content": prompt}],
        temperature=0)
    new_response=translate(response.choices[0].message.content,lang)
    return new_response
#step -5:read multiple pdf
def answer_from_pdfs(query, pdf_paths):
    answers = []
    for pdf_path in pdf_paths:
        answer = answer_question(query, pdf_path)
        if answer and "does not contain any information" not in answer.lower():
            answers.append(f"📄 From **{pdf_path}**:\n{answer}")
    if answers:
        return "\n\n".join(answers)
    else:
        return "❌ Sorry, no relevant information found in the given PDFs."
    
# -------------------------------
# Step 6: Save history
# -------------------------------
def save_history(query, answer):
    wrapped_answer = textwrap.fill(answer, width=75)
    history = (
        f"Your query:\n{query}\n"
        f"Response:\n{wrapped_answer}\n"
        f"{'-'*40}\n"
    )
    with open("result.txt", "a", encoding="utf-8") as f:
        f.write(history)

#import streamlit as st
#import random
# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Namaste! How can I assist you Today?"}]

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
pdf_paths = ["FAQs-30-11-23.pdf", "Various_Scholarship_Scheme_for_B.Tech_students.pdf","Fees Information B Tech B Arch Admission thr JoSAA 2023.pdf","AC First Year UG Winter-2025 (July-2025 to Jan-2026) Raut Mam ver2 (1).pdf"]  # Add more PDFs here
# Accept user input
if prompt := st.chat_input("What is up?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    
    with st.chat_message("user"):
        st.markdown(prompt)
        
    
        
        #print("Q:", query)
        #print("A:", answer)
    
        #client = genai.Client()
        #response = client.models.generate_content(
        #    model="gemini-2.5-flash", contents=prompt
        #    )
        #print(response.text)
        
    
    # Display assistant response in chat message container
    answer = answer_from_pdfs(prompt, pdf_paths)
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = answer
        #new_answer=translate(answer) 

    sleep(0.05)
                    # Add a blinking cursor to simulate typing
    message_placeholder.markdown(full_response + "▌")
    message_placeholder.markdown(full_response)
        # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content":(answer)})
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
    save_history(prompt, answer)

    
        


        
