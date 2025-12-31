import os
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain.chat_models import init_chat_model


# ---------------- CONFIG ----------------
DB_DIR = os.path.join(os.path.dirname(__file__), "chroma_db")

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
db = Chroma(persist_directory=DB_DIR, embedding_function=embeddings)

retriever = db.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 8}
)

llm = init_chat_model(
    model="meta-llama-3.1-8b-instruct",
    model_provider="openai",
    openai_api_base="http://localhost:1234/v1",  # change if needed
    api_key="dummy"
)


# ---------------- NORMALIZATION ----------------
def normalize_query(q: str) -> str:
    q = q.lower().strip()

    # Remove punctuation/noise
    for p in ["??", "?", "!", ".", ","]:
        q = q.replace(p, "")

    # Remove filler words
    filler_phrases = [
        "hey bro", "bro", "hey", "hello", "hi", "can you tell me",
        "what's the", "whats the", "i want to know", "give me", "please", "tell me"
    ]
    for f in filler_phrases:
        q = q.replace(f, "")

    # Intent mapping
    replace_map = {
        "cost": "fees",
        "price": "fees",
        "how long": "duration",
        "time required": "duration",
        "course length": "duration"
    }
    for k, v in replace_map.items():
        q = q.replace(k, v)

    # Course/term mapping
    course_map = {
        "gen ai": "generative ai",
        "gen-ai": "generative ai",
        "llm": "generative ai",
        "ml": "machine learning",
        "data science": "machine learning",
        "data-science": "machine learning",
        "adv java": "advanced java",
        "mern": "mern full stack development",
        "fsd": "full stack development"
    }
    for k, v in course_map.items():
        q = q.replace(k, v)

    return q.strip()


# ---------------- DOC FILTERING ----------------
def filter_docs_by_course(query, docs):
    tokens = set(query.lower().split())
    filtered = [d for d in docs if any(t in d.metadata.get("course", "") for t in tokens)]
    return filtered if filtered else docs


def prioritize_by_section(query, docs):
    q = query.lower()

    if any(x in q for x in ["fee", "fees"]):
        target = "fees"
    elif "duration" in q or "hours" in q or "months" in q:
        target = "duration"
    elif "eligibility" in q or "prerequisite" in q:
        target = "eligibility"
    elif "syllabus" in q or "module" in q:
        target = "syllabus"
    elif "schedule" in q or "timings" in q:
        target = "schedule"
    else:
        return docs

    prioritized = [d for d in docs if d.metadata.get("section") == target]
    return prioritized if prioritized else docs


# ---------------- ASK FUNCTION ----------------
def ask(raw_query: str):
    query = normalize_query(raw_query)

    docs = retriever.invoke(query)

    # manual score cleanup
    docs = [d for d in docs if d.metadata.get("score", 1) >= 0.18] or docs

    docs = filter_docs_by_course(query, docs)
    docs = prioritize_by_section(query, docs)

    context = "\n\n---\n\n".join(d.page_content for d in docs)

    prompt = f"""
You are a Sunbeam information assistant.
Answer ONLY using the context below.
If answer is not present → respond EXACTLY with:
Not in my current Sunbeam data.

CONTEXT:
{context}

QUESTION: {query}
ANSWER:
""".strip()

    response = llm.invoke(prompt)
    answer = response.content.strip()
    sources = [d.metadata.get("file") for d in docs]
    return answer, sources


# ---------------- TEST CASES ----------------
TEST_CASES = [
    ("fees for java", "direct"),
    ("duration of generative ai", "direct"),
    ("eligibility for data science", "direct"),     # mapped to ML now
    ("fees for marine engineering", "not_found"),
    ("java duration", "direct"),
    ("cost of gen ai", "direct"),
    ("yo python cost??", "direct"),
    ("hey bro what’s the fees for java course?", "direct"),
    ("where is sunbeam located?", "not_found"),
    ("placement percentage", "not_found"),
]


# ---------------- MAIN ----------------
if __name__ == "__main__":
    print("\n🚀 TESTING SUNBEAM RAG SYSTEM\n")

    for query, expected in TEST_CASES:
        answer, src = ask(query)

        if expected == "not_found":
            passed = (answer == "Not in my current Sunbeam data.")
        else:
            passed = (answer != "Not in my current Sunbeam data.")

        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} → {query!r}")
        print(f"   ↳ {answer}")
        print(f"   ↳ Sources: {src}\n")

    print("\n🎯 DONE — Only fail if data is missing, not inconsistency.\n")
