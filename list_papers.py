"""
list_papers.py

Helps you pick a starting batch of papers to read, by mapping arXiv IDs
(your PDF filenames) back to titles, dates, and abstracts.

Run:
    python list_papers.py
"""

import json
import os

OUTPUT_DIR = "corpus"
METADATA_FILE = os.path.join(OUTPUT_DIR, "corpus_metadata.json")

# Well-known / widely-cited quantization method names. If your corpus
# contains the paper that introduced these, they're excellent starting
# points -- most later papers in the field reference them.
LANDMARK_KEYWORDS = [
    "GPTQ",
    "AWQ",
    "LLM.int8",
    "SmoothQuant",
    "QLoRA",
    "GGUF",
    "BitNet",
    "SpQR",
    "SqueezeLLM",
    "OmniQuant",
    "ZeroQuant",
]


def load_papers():
    with open(METADATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def find_landmarks(papers):
    print("=" * 70)
    print("LANDMARK PAPERS FOUND IN YOUR CORPUS")
    print("=" * 70)
    found_ids = set()
    for keyword in LANDMARK_KEYWORDS:
        matches = [p for p in papers if keyword.lower() in p["title"].lower()]
        for m in matches:
            if m["arxiv_id"] not in found_ids:
                found_ids.add(m["arxiv_id"])
                print(f"\n[{keyword}]")
                print(f"  file:  corpus/pdfs/{m['arxiv_id']}.pdf")
                print(f"  title: {m['title']}")
                print(f"  date:  {m['published'][:10]}")
    if not found_ids:
        print("\nNone of the landmark keywords matched titles in your corpus.")
    return found_ids


def show_oldest_newest(papers, n=5):
    sorted_papers = sorted(papers, key=lambda p: p["published"])
    print("\n" + "=" * 70)
    print(f"OLDEST {n} PAPERS (good for understanding early/foundational work)")
    print("=" * 70)
    for p in sorted_papers[:n]:
        print(f"\n  file:  corpus/pdfs/{p['arxiv_id']}.pdf")
        print(f"  title: {p['title']}")
        print(f"  date:  {p['published'][:10]}")

    print("\n" + "=" * 70)
    print(f"NEWEST {n} PAPERS (good for seeing current state of the field)")
    print("=" * 70)
    for p in sorted_papers[-n:]:
        print(f"\n  file:  corpus/pdfs/{p['arxiv_id']}.pdf")
        print(f"  title: {p['title']}")
        print(f"  date:  {p['published'][:10]}")


def search(papers, keyword):
    matches = [p for p in papers if keyword.lower() in p["title"].lower()]
    print(f"\n{len(matches)} matches for {keyword!r}:")
    for m in matches:
        print(f"\n  file:  corpus/pdfs/{m['arxiv_id']}.pdf")
        print(f"  title: {m['title']}")
        print(f"  date:  {m['published'][:10]}")


def main():
    papers = load_papers()
    print(f"Loaded {len(papers)} papers.\n")

    find_landmarks(papers)
    show_oldest_newest(papers, n=5)

    print("\n" + "=" * 70)
    while True:
        query = input("\nSearch titles by keyword (or press Enter to quit): ").strip()
        if not query:
            break
        search(papers, query)


if __name__ == "__main__":
    main()