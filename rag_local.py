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

    for p in ["??", "?", "!", ".", ","]:
        q = q.replace(p, "")

    filler = ["hey", "bro", "hello", "hi", "give me", "please", "tell me"]
    for f in filler:
        q = q.replace(f, "")

    # Intent mapping
    intent_map = {
        "cost": "fees",
        "price": "fees",
        "how long": "duration",
        "time required": "duration",
        "course length": "duration",
    }
    for k, v in intent_map.items():
        q = q.replace(k, v)

    # Course mapping
    course_map = {
        "gen ai": "generative ai",
        "gen-ai": "generative ai",
        "llm": "generative ai",
        "ml": "machine learning",
        "data science": "machine learning",
        "adv java": "advanced java",
        "mern": "mern full stack development",
        "fsd": "full stack development",
        "python": "python programming",
    }
    for k, v in course_map.items():
        q = q.replace(k, v)

    return q.strip()

# ---------------- FILTER DOCS ----------------
def filter_docs_by_course(query, docs):
    tokens = set(query.lower().split())
    filtered = [d for d in docs if any(t in d.metadata.get("course","") for t in tokens)]
    return filtered if filtered else docs

def prioritize_by_section(query, docs):
    q = query.lower()

    if "fees" in q: target = "fees"
    elif any(x in q for x in ["duration", "hours", "months"]): target = "duration"
    elif any(x in q for x in ["eligibility", "prerequisite"]): target = "eligibility"
    elif any(x in q for x in ["syllabus", "module"]): target = "syllabus"
    elif any(x in q for x in ["schedule", "timings"]): target = "schedule"
    else: return docs

    best = [d for d in docs if d.metadata.get("section") == target]
    return best if best else docs

# ---------------- ASK FUNCTION ----------------
def ask(raw_query: str):
    query = normalize_query(raw_query)

    # Step 1: initial retrieval
    docs = retriever.invoke(query)

    # Step 2: SOFT score filter (don’t nuke everything)
    soft = [d for d in docs if d.metadata.get("score", 0) >= 0.25]
    docs = soft if soft else docs  # fallback to original if empty

    if not docs:
        return "Not in my current Sunbeam data.", []

    # Step 3: refine
    docs = filter_docs_by_course(query, docs)
    docs = prioritize_by_section(query, docs)

    # Step 4: build context for model
    context = "\n\n---\n\n".join(d.page_content for d in docs)

    # Step 5: instruction
    prompt = f"""
You are a Sunbeam Institute information assistant.

RULES:
- Respond ONLY using the context.
- If answer is missing → reply EXACTLY: Not in my current Sunbeam data.
- Do NOT guess or hallucinate.
- Answer in one or two lines maximum.

CONTEXT:
{context}

QUESTION: {query}
ANSWER:
""".strip()

    response = llm.invoke(prompt)
    answer = response.content.strip()

    if answer.lower() == "not in my current sunbeam data.":
        return "Not in my current Sunbeam data.", []

    return answer, []

# ---------------- TEST ----------------
if __name__ == "__main__":
    print("\n🚀 TESTING\n")
    tests = [
        "fees for java",
        "duration for generative ai",
        "eligibility for machine learning",
        "about sunbeam",
    ]
    for t in tests:
        ans, _ = ask(t)
        print(f"Q: {t} → {ans}")
