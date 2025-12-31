import os
from loader import load_all_txt
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter

DB_DIR = os.path.join(os.path.dirname(__file__), "chroma_db")


def detect_section(text):
    t = text.lower()

    # Fees
    if any(x in t for x in ["fee", "fees", "cost", "price", "charges", "₹", "rs ", "inr"]):
        return "fees"

    # Duration (uppercase, lowercase, synonyms)
    if any(x in t for x in ["duration", "duration:", "60 hours", "hours", "weeks", "months"]):
        return "duration"

    # Eligibility / Requirements (map PREREQUISITES)
    if any(x in t for x in ["eligibility", "prerequisite", "prerequisites", "requirements"]):
        return "eligibility"

    # Syllabus (map SYLLABUS MODULES)
    if any(x in t for x in ["syllabus", "syllabus modules", "modules", "curriculum", "topics"]):
        return "syllabus"

    # Schedule
    if any(x in t for x in ["batch", "schedule", "timings", "dates", "mode"]):
        return "schedule"

    return "general"

# ---------------------------------------------------------------------


# ------------------- COURSE TAGGING / NORMALIZATION -------------------
def clean_and_tag(docs):
    cleaned = []
    for d in docs:
        filename = os.path.basename(d.metadata["source"])
        course = (
            filename.replace(".txt", "")
            .replace("Course_Name__", "")
            .replace("_", " ")
            .replace("-", " ")
            .strip()
        )

        d.page_content = f"COURSE: {course}\n\n{d.page_content}"
        d.metadata["course"] = course.lower()
        cleaned.append(d)

    return cleaned
# ----------------------------------------------------------------------


# -------------------------- CHUNKING ENGINE ---------------------------
def chunk_documents(docs):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=350,
        chunk_overlap=50,
        separators=[
        "COURSE:", "CATEGORY:", "PREREQUISITES:", "SYLLABUS MODULES:",
        "DURATION:", "FEES:", "SCHEDULE:", "TIMINGS:", "MODE:",
        "OUTCOMES:", "SOFTWARE REQUIREMENTS:",
        "\n\n", "\n"
        ],
    )

    chunks = splitter.split_documents(docs)

    for c in chunks:
        section = detect_section(c.page_content)
        c.metadata["section"] = section

        # ORDER MATTERS: COURSE FIRST, THEN SECTION
        c.page_content = (
            f"COURSE: {c.metadata['course']}\n"
            f"SECTION: {section.upper()}\n\n"
            f"{c.page_content}"
        )

    return chunks
# ----------------------------------------------------------------------


# --------------------------- INGEST PIPELINE --------------------------
def ingest():
    print("📥 Loading .txt files...")
    docs = load_all_txt()
    if not docs:
        raise ValueError("❌ NO DOCUMENTS FOUND. Fix your DATA path in loader.py")

    print("🔧 Cleaning & Course Tagging...")
    docs = clean_and_tag(docs)

    print("✂️ Splitting into chunks...")
    chunks = chunk_documents(docs)
    print(f"📌 Total Chunks: {len(chunks)}")

    for c in chunks:
        c.metadata["file"] = os.path.basename(c.metadata.get("source", "unknown"))

    print("⚙️ Creating Embeddings...")
    emb = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    print("💾 Saving to ChromaDB...")
    Chroma.from_documents(chunks, emb, persist_directory=DB_DIR)

    print("🎉 DONE: Vector DB ready for use")
    return len(chunks)
# ----------------------------------------------------------------------


# ------------------------- EXECUTION CONTROL --------------------------
if __name__ == "__main__":
    if os.path.exists(DB_DIR):
        import shutil
        print("🗑️ Clearing old DB...")
        shutil.rmtree(DB_DIR)

    total = ingest()
    print(f"🚀 FINISHED → {total} vectors stored.")
# ----------------------------------------------------------------------
