import streamlit as st
from rag_local import ask   # your backend - don't edit it here

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Sunbeam Course Assistant",
    page_icon="📚",
    layout="centered"
)

st.title("📚 Sunbeam Course Assistant (Chat Mode)")


# ---------------- CHAT MEMORY ----------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []   # stores: (role, message)


# ---------------- USER INPUT ----------------
query = st.chat_input("Ask about course fees, duration, syllabus, etc...")

if query:
    try:
        answer, _ = ask(query)  # ignore sources
        st.session_state.chat_history.append(("user", query))
        st.session_state.chat_history.append(("assistant", answer))
    except Exception as e:
        st.error(f"❌ Backend Error: {e}")
        st.stop()


# ---------------- RENDER CHAT ----------------
for role, message in st.session_state.chat_history:

    if role == "user":
        with st.chat_message("user", avatar="🧑"):
            st.write(message)

    elif role == "assistant":
        with st.chat_message("assistant", avatar="🤖"):
            st.write(message)


