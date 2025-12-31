import os
from loader import load_all_txt
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter

DB_DIR = os.path.join(os.path.dirname(__file__), "chroma_db")


def clean_and_tag(docs):
    """Add COURSE metadata/anchor to help retrieval accuracy."""
    cleaned = []
    for d in docs:
        filename = os.path.basename(d.metadata["source"])
        course = (
            filename.replace(".txt", "")
            .replace("Course_Name__", "")
            .replace("_", " ")
            .strip()
        )

        # Strong anchor tag for the retriever
        tagged = f"COURSE: {course}\n\n{d.page_content}"
        d.page_content = tagged
        d.metadata["course"] = course.lower()
        cleaned.append(d)

    return cleaned


def chunk_documents(docs):
    """Smart chunking to avoid cross-contamination between courses."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=350,
        chunk_overlap=50,
        separators=[
            "COURSE:", "Eligibility:", "Pre-requisites", "Prerequisites",
            "Duration:", "Fees:", "Syllabus:", "Modules:", "\n\n", "\n", " "
        ],
    )
    return splitter.split_documents(docs)


def ingest():
    print("📥 Loading text...")
    docs = load_all_txt()

    if not docs:
        raise ValueError("❌ NO DOCUMENTS FOUND. FIX YOUR loader path.")

    print("🔧 Cleaning + Tagging")
    docs = clean_and_tag(docs)

    print("✂️ Chunking data...")
    chunks = chunk_documents(docs)
    print(f"📌 Total Chunks Created: {len(chunks)}")

    for c in chunks:
        c.metadata["file"] = os.path.basename(c.metadata.get("source", "unknown"))

    print("⚙️ Embeddings...")
    emb = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    print("💾 Storing to ChromaDB...")
    Chroma.from_documents(
        chunks,
        emb,
        persist_directory=DB_DIR
    )

    print("🎉 DONE → ChromaDB Updated & Saved Automatically")

    return len(chunks)


if __name__ == "__main__":
    total = ingest()
    print(f"🚀 FINISHED → {total} vectors stored.")
