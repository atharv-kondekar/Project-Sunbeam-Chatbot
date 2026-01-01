import os, re
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain.chat_models import init_chat_model


# Connecting to vectorDb and embedding model 
DB_DIR = os.path.join(os.path.dirname(__file__), "chroma_db")

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
db = Chroma(persist_directory=DB_DIR, embedding_function=embeddings)

retriever = db.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 8}
)

#Initializing LLM
llm = init_chat_model(
    model="meta-llama-3.1-8b-instruct",
    model_provider="openai",
    openai_api_base="http://localhost:1234/v1",
    api_key="dummy"
)


# ---------------- NORMALIZATION the query ----------------
def normalize_query(q: str) -> str:
    q = q.lower().strip()

    for p in ["??", "?", "!", ".", ","]:
        q = q.replace(p, "")

    filler = ["hey", "bro", "hello", "hi", "give me", "please", "tell me"]
    for f in filler:
        q = q.replace(f, "")

    replacements = {
        "cost": "fees",
        "price": "fees",
        "how long": "duration",
        "time required": "duration",
        "course length": "duration",
        "gen ai": "generative ai",
        "gen-ai": "generative ai",
        "llm": "generative ai",
        "ml": "machine learning",
        "data science": "machine learning",
        "adv java": "advanced java",
        "mern": "mern full stack development",
        "fsd": "full stack development",
        "python": "python development",
    }
    for k, v in replacements.items():
        q = q.replace(k, v)

    return q.strip()


# ---------------- EXTRACT FROM UNSTRUCTURED TEXT ----------------
def extract_section(query, context):
    q = query.lower()

    patterns = {
        "duration": r"(duration|how long|hours|months).{0,80}",
        "fees": r"(fees|cost|price).{0,80}",
        "eligibility": r"(eligibility|prerequisites|requirements).{0,200}",
        "syllabus": r"(syllabus|modules|curriculum|topics).{0,300}",
        "schedule": r"(schedule|batch|dates).{0,150}",
        "timings": r"(timings|time|hours|class time).{0,120}",
        "about": r"(sunbeam|institute|training|established|focus|mission).{0,300}"
    }

    # Targeted match
    for key, pattern in patterns.items():
        if key in q:
            match = re.search(pattern, context, flags=re.IGNORECASE)
            if match:
                return match.group(0)

    # Fallback match
    for pattern in patterns.values():
        match = re.search(pattern, context, flags=re.IGNORECASE)
        if match:
            return match.group(0)

    return None


# ---------------- ASK FUNCTION (MAIN LOGIC) ----------------
def ask(raw_query: str):
    query = normalize_query(raw_query)
    docs = retriever.invoke(query)

    docs = [d for d in docs if d.metadata.get("score", 0) >= 0.10] or docs
    if not docs:
        return "Not in my current Sunbeam data.", []

    context = "\n\n---\n\n".join([d.page_content for d in docs])
    extracted = extract_section(query, context)

    base_prompt = f"""
You are a Sunbeam Institute information assistant.
Answer ONLY using the text below.
Do NOT guess or hallucinate.
If you don't find the answer, respond EXACTLY:
Not in my current Sunbeam data.

TEXT:
{context}

QUESTION: {query}
"""

    if extracted:
        prompt = base_prompt + f"\nRelevant Extract:\n{extracted}\nANSWER:"
        response = llm.invoke(prompt).content.strip()
        if response and "not in" not in response.lower():
            return response, []

    prompt = base_prompt + "\nANSWER:"
    # invoking the LLM 
    response = llm.invoke(prompt).content.strip()
    

    if not response or "not in" in response.lower():
        return "Not in my current Sunbeam data.", []

    return response, []


# ---------------- TEST BLOCK ----------------
if __name__ == "__main__":
    print("\n🚀 TESTING UNSTRUCTURED RAG (rag_local.py)\n")

    test_queries = [
        "fees for core java",
        "duration for the java course",
        "eligibility for python development",
        "syllabus for machine learning",
        "duration for mastering generative ai course",
        "about sunbeam",
        "internship domains",
        "placements statistics",
        "marine engineering course fees",  # should fail
    ]

    for q in test_queries:
        ans, _ = ask(q)
        print(f"❓ {q}\n➡️ {ans}\n")

    print("🎯 DONE — if majority fail, your .txt files STILL suck.\n")
