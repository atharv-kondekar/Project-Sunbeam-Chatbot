import os
from langchain_community.document_loaders import TextLoader

ROOT = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(ROOT, "Scraping Sunbeam Data", "data")

def load_all_txt():
    if not os.path.exists(DATA_DIR):
        raise FileNotFoundError(f"❌ DATA DIRECTORY NOT FOUND: {DATA_DIR}")

    docs = []
    for root, _, files in os.walk(DATA_DIR):
        for file in files:
            if file.lower().endswith(".txt"):
                path = os.path.join(root, file)
                loader = TextLoader(path, encoding="utf-8")
                for d in loader.load():
                    d.metadata["source"] = path
                    docs.append(d)
    return docs


if __name__ == "__main__":
    data = load_all_txt()
    print(f"✔ Loaded {len(data)} documents.\n")

    print("📌 SAMPLE FROM MAIN DATA:")
    for d in data[:5]:
        print("•", d.metadata["source"])

    print("\n📌 SAMPLE FROM COURSES FOLDER:")
    for d in data:
        if "courses" in d.metadata["source"].lower():
            print("•", d.metadata["source"])
            break
    else:
        print("❌ NO course files detected. Check folder spelling.")
