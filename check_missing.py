"""
check_missing.py

Compares corpus_metadata.json against what's actually in corpus/pdfs/,
lists any missing papers, and offers to retry downloading just those.

Run from the same folder as build_corpus.py:
    python check_missing.py
"""

import json
import os
import time
import requests

OUTPUT_DIR = "corpus"
METADATA_FILE = os.path.join(OUTPUT_DIR, "corpus_metadata.json")
PDF_DIR = os.path.join(OUTPUT_DIR, "pdfs")
REQUEST_DELAY_SECONDS = 3.1


def main():
    with open(METADATA_FILE, "r", encoding="utf-8") as f:
        papers = json.load(f)

    existing_files = {
        fname[:-4]  # strip ".pdf"
        for fname in os.listdir(PDF_DIR)
        if fname.lower().endswith(".pdf")
    }

    missing = [p for p in papers if p["arxiv_id"] not in existing_files]

    print(f"Metadata entries: {len(papers)}")
    print(f"PDFs on disk:      {len(existing_files)}")
    print(f"Missing:           {len(missing)}\n")

    if not missing:
        print("Nothing missing -- metadata and PDF folder are in sync.")
        return

    print("Missing papers:")
    for p in missing:
        print(f"  {p['arxiv_id']}  -  {p['title']}")

    choice = input("\n[r]etry downloading these, [d]elete them from metadata, or [n]othing? [r/d/n] ").lower()

    if choice == "r":
        for p in missing:
            print(f"Retrying {p['arxiv_id']}...")
            try:
                resp = requests.get(p["pdf_url"], timeout=60)
                resp.raise_for_status()
                dest = os.path.join(PDF_DIR, f"{p['arxiv_id']}.pdf")
                with open(dest, "wb") as f:
                    f.write(resp.content)
                print(f"  success: {p['arxiv_id']}.pdf")
            except Exception as e:
                print(f"  still failing: {p['arxiv_id']} -- {e}")
            time.sleep(REQUEST_DELAY_SECONDS)
        print("\nDone. Re-run this script to confirm everything now matches.")

    elif choice == "d":
        remaining = [p for p in papers if p["arxiv_id"] not in {m["arxiv_id"] for m in missing}]
        with open(METADATA_FILE, "w", encoding="utf-8") as f:
            json.dump(remaining, f, indent=2, ensure_ascii=False)
        print(f"\nRemoved {len(missing)} entries from metadata. "
              f"{len(remaining)} entries remain, matching your {len(existing_files)} PDFs.")

    else:
        print("No changes made.")


if __name__ == "__main__":
    main()