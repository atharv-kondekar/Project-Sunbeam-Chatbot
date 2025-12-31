import os
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain.chat_models import init_chat_model

DB_DIR = os.path.join(os.path.dirname(__file__), "chroma_db")

embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
db = Chroma(persist_directory=DB_DIR, embedding_function=embeddings)
retriever = db.as_retriever(search_kwargs={"k": 5})

llm = init_chat_model(
    model="meta-llama-3.1-8b-instruct",
    model_provider="openai",
    openai_api_base="http://localhost:1234/v1",
    api_key="dummy"
)

SYSTEM_PROMPT = """
You are a Sunbeam information assistant.

STRICT RULES:
1. Answer ONLY using the provided CONTEXT.
2. If information is not in context → reply: "Not in my current Sunbeam data."
3. No guessing, no assumptions, no external knowledge.
4. Keep responses short, clear, factual. No fluff.
5. If multiple relevant matches exist, summarize concisely.
6. If the user's question asks for:
   - "internship batches"
   - "batch schedule"
   - "internship schedule"
   - "list of internship batches"
   - "internship batch codes"
   - "all internship batches"
   OR contains ANY of these words:
   ["batch", "schedule", "batches", "batch code"]
   
   → Then IGNORE normal shortening and RETURN the FULL batch schedule table EXACTLY as found in the context. Do not rewrite or reformat beyond a clean table.

7. NEVER answer from memory. Only from CONTEXT.

QUESTION:
{question}

CONTEXT:
{context}

FINAL ANSWER:
"""

def filter_docs_by_course(query, docs):
    key = query.lower()

    return [
        d for d in docs
        if "course" in key or any(k in d.metadata.get("course", "") for k in key.split())
    ] or docs


def ask(query: str):
    docs = retriever.invoke(query)
    docs = filter_docs_by_course(query, docs)

    context = "\n".join(d.page_content for d in docs)
    prompt = f"{SYSTEM_PROMPT}\n\nCONTEXT:\n{context}\n\nQUESTION: {query}\nANSWER:"

    response = llm.invoke(prompt)
    answer = response.content.strip()

    sources = [d.metadata.get("file") for d in docs]
    return answer, sources


if __name__ == "__main__":
    while True:
        q = input("\n❓ Ask: ")
        if q.lower() in ["exit", "quit"]: break
        ans, src = ask(q)
        print("\n🧠", ans)
        print("📌", src, "\n")
