import os
from langchain_community.document_loaders import TextLoader

# Path setup 
ROOT = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(ROOT, "Scraping sunbeam data", "scraped data")


# laods .txt 
def load_all_txt():
    #validates the path
    if not os.path.exists(DATA_DIR):
        raise FileNotFoundError(f"❌ DATA DIRECTORY NOT FOUND: {DATA_DIR}")

    # docs loading 
    docs = []
    for root, _, files in os.walk(DATA_DIR):
        for file in files:
            if file.lower().endswith(".txt"):
                path = os.path.join(root, file)
                #text loader 
                loader = TextLoader(path, encoding="utf-8")
                for d in loader.load():
                    d.metadata["source"] = path
                    docs.append(d)
    print(f"✔ Loaded {len(docs)} documents from: {DATA_DIR}")
    return docs

if __name__ == "__main__":
    data = load_all_txt()
    print("\n📌 SAMPLE FILES:")
    for d in data[:5]:
        print("•", d.metadata["source"])
