import streamlit as st
import os
import random
import json
from docx import Document

st.set_page_config(page_title="Flashcard Review", layout="centered")

# --- Settings ---
FLASHCARD_FOLDER = "flashcard_app/flashcards"
DATA_FOLDER = "progress"
TAGS = ["Important", "Very Important", "Review Later"]

# --- Utils ---
def get_module_files():
    files = [f for f in os.listdir(FLASHCARD_FOLDER) if f.endswith(".docx")]
    return {f[:-5]: os.path.join(FLASHCARD_FOLDER, f) for f in files}

def load_questions_from_docx(filepath):
    doc = Document(filepath)
    qa_pairs = []
    q, a = None, None
    for para in doc.paragraphs:
        text = para.text.strip()
        if text.startswith("Q:"):
            q = text[2:].strip()
        elif text.startswith("A:") and q:
            a = text[2:].strip()
            qa_pairs.append({"question": q, "answer": a})
            q, a = None, None
    return qa_pairs

def load_progress(module_name):
    path = os.path.join(DATA_FOLDER, f"{module_name}.json")
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {}

def save_progress(module_name, data):
    path = os.path.join(DATA_FOLDER, f"{module_name}.json")
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

# --- Main App ---
st.title("🧠 Flashcard Trainer")

modules = get_module_files()
if not modules:
    st.warning("No modules found. Please add .docx files to the 'flashcards/' folder.")
    st.stop()

module_name = st.selectbox("Choose a Module", list(modules.keys()))
progress = load_progress(module_name)
qa_pairs = load_questions_from_docx(modules[module_name])

# Merge progress with flashcards
for i, qa in enumerate(qa_pairs):
    qid = str(i)
    qa["id"] = qid
    if qid not in progress:
        progress[qid] = {
            "correct": 0,
            "incorrect": 0,
            "tags": []
        }

# Tag Filter
selected_tag = st.selectbox("Filter by tag (optional)", ["All"] + TAGS)
if selected_tag != "All":
    qa_pairs = [qa for qa in qa_pairs if selected_tag in progress[qa["id"]]["tags"]]

# Question Count
num_q = st.slider("How many questions?", 1, min(50, len(qa_pairs)), 10)
qa_pairs = random.sample(qa_pairs, min(num_q, len(qa_pairs)))

# Add the "Go" button here
if 'flashcards' not in st.session_state:
    st.session_state.flashcards = []

if st.button('Go'):
    # Store flashcards in session state once 'Go' is pressed
    st.session_state.flashcards = qa_pairs

# --- Flashcard Loop ---
if st.session_state.flashcards:
    for qa in st.session_state.flashcards:
        qid = qa["id"]
        st.markdown("----")
        with st.container():
            # Show the question and answer only after pressing 'Go'
            if st.button(f"🔹 **Q:** {qa['question']}", key=f"flip_{qid}"):
                st.markdown(f"🟩 **A:** {qa['answer']}")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Got it", key=f"right_{qid}"):
                    progress[qid]["correct"] += 1
            with col2:
                if st.button("❌ Missed it", key=f"wrong_{qid}"):
                    progress[qid]["incorrect"] += 1

            # Tagging
            current_tags = progress[qid]["tags"]
            new_tags = st.multiselect("Tag this question", TAGS, default=current_tags, key=f"tag_{qid}")
            progress[qid]["tags"] = new_tags

    # Save progress after the flashcard loop
    save_progress(module_name, progress)
