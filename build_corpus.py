"""
build_corpus.py

Pulls a corpus of papers on LLM quantization / low-bit inference from the
arXiv API, dedupes them, and saves:
  - corpus_metadata.json   (id, title, authors, abstract, categories, dates, pdf_url)
  - pdfs/<arxiv_id>.pdf    (the actual PDF files, downloaded)

Run:
    pip install requests
    python build_corpus.py

Notes:
- arXiv's API asks for max ~1 request per 3 seconds. This script respects that.
- Adjust MAX_RESULTS, QUERY_TERMS, and DATE_RANGE below to tune your corpus size/scope.
- Re-running is safe: already-downloaded PDFs and already-seen ids are skipped.
"""

import json
import os
import time
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime

import requests

# ----------------------------- CONFIG -----------------------------

# Search terms for quantization / low-bit inference. Feel free to add/remove.
QUERY_TERMS = [
    "LLM quantization",
    "post-training quantization language model",
    "quantization aware training transformer",
    "low-bit inference large language model",
    "weight-only quantization",
    "GPTQ",
    "AWQ quantization",
    "ternary quantization language model",
    "1-bit LLM",
    "extreme low bit quantization neural network",
]

# arXiv categories to restrict to (cs.CL = computation & language, cs.LG = machine learning)
CATEGORIES = ["cs.CL", "cs.LG"]

# Roughly bound the field's real evolution: early PTQ work through recent sub-4-bit methods
DATE_MIN = "2020-01-01"
DATE_MAX = "2026-12-31"

MAX_RESULTS_PER_QUERY = 100   # arXiv API page size cap per request is 100
TARGET_TOTAL_PAPERS = 600     # stop once we have roughly this many unique papers

OUTPUT_DIR = "corpus"
METADATA_FILE = os.path.join(OUTPUT_DIR, "corpus_metadata.json")
PDF_DIR = os.path.join(OUTPUT_DIR, "pdfs")

ARXIV_API_URL = "https://export.arxiv.org/api/query"
REQUEST_DELAY_SECONDS = 3.1  # arXiv asks for >=3s between requests

ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}

# --------------------------------------------------------------------


def build_query(term: str) -> str:
    """Build an arXiv API search_query string for one topic term, restricted
    to our categories and (as best arXiv's query syntax allows) date range.

    Short terms (<=2 words) or terms that look like acronyms/method names
    (e.g. "GPTQ") are searched as exact phrases, since they're specific
    enough to appear verbatim. Longer descriptive terms are searched as an
    AND of their individual words, since requiring the exact phrase verbatim
    is too strict and silently returns zero results.
    """
    words = term.split()
    if len(words) <= 2:
        term_clause = f'all:"{term}"'
    else:
        term_clause = " AND ".join(f'all:"{w}"' for w in words)

    cat_clause = " OR ".join(f"cat:{c}" for c in CATEGORIES)
    return f"({term_clause}) AND ({cat_clause})"


def fetch_batch(search_query: str, start: int, max_results: int) -> ET.Element:
    params = {
        "search_query": search_query,
        "start": start,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
    }
    url = ARXIV_API_URL + "?" + urllib.parse.urlencode(params)
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    return ET.fromstring(resp.text)


def parse_entries(root: ET.Element):
    entries = []
    for entry in root.findall("atom:entry", ATOM_NS):
        arxiv_id_full = entry.find("atom:id", ATOM_NS).text.strip()
        arxiv_id = arxiv_id_full.rstrip("/").split("/")[-1]  # e.g. 2306.00978v2
        arxiv_id_base = arxiv_id.split("v")[0]

        title = entry.find("atom:title", ATOM_NS).text.strip().replace("\n", " ")
        summary = entry.find("atom:summary", ATOM_NS).text.strip().replace("\n", " ")
        published = entry.find("atom:published", ATOM_NS).text.strip()
        updated = entry.find("atom:updated", ATOM_NS).text.strip()

        authors = [
            a.find("atom:name", ATOM_NS).text
            for a in entry.findall("atom:author", ATOM_NS)
        ]

        categories = [
            c.attrib.get("term")
            for c in entry.findall("atom:category", ATOM_NS)
        ]

        pdf_url = None
        for link in entry.findall("atom:link", ATOM_NS):
            if link.attrib.get("title") == "pdf" or link.attrib.get("type") == "application/pdf":
                pdf_url = link.attrib.get("href")
        if pdf_url is None:
            pdf_url = f"https://arxiv.org/pdf/{arxiv_id_base}.pdf"

        entries.append({
            "arxiv_id": arxiv_id_base,
            "version": arxiv_id,
            "title": title,
            "authors": authors,
            "abstract": summary,
            "categories": categories,
            "published": published,
            "updated": updated,
            "pdf_url": pdf_url,
        })
    return entries


def in_date_range(entry: dict) -> bool:
    pub_date = entry["published"][:10]  # "YYYY-MM-DD"
    return DATE_MIN <= pub_date <= DATE_MAX


def load_existing_metadata():
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            return {e["arxiv_id"]: e for e in json.load(f)}
    return {}


def save_metadata(papers_by_id: dict):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(list(papers_by_id.values()), f, indent=2, ensure_ascii=False)


def download_pdf(entry: dict):
    os.makedirs(PDF_DIR, exist_ok=True)
    dest = os.path.join(PDF_DIR, f"{entry['arxiv_id']}.pdf")
    if os.path.exists(dest):
        return  # already downloaded
    try:
        resp = requests.get(entry["pdf_url"], timeout=60)
        resp.raise_for_status()
        with open(dest, "wb") as f:
            f.write(resp.content)
        print(f"  downloaded {entry['arxiv_id']}.pdf")
    except Exception as e:
        print(f"  FAILED to download {entry['arxiv_id']}: {e}")
    time.sleep(REQUEST_DELAY_SECONDS)


def main():
    papers_by_id = load_existing_metadata()
    print(f"Starting with {len(papers_by_id)} papers already in metadata file.")

    for term in QUERY_TERMS:
        if len(papers_by_id) >= TARGET_TOTAL_PAPERS:
            break

        search_query = build_query(term)
        print(f"\nQuerying arXiv for: {term!r}")

        start = 0
        while True:
            if len(papers_by_id) >= TARGET_TOTAL_PAPERS:
                break

            root = fetch_batch(search_query, start, MAX_RESULTS_PER_QUERY)
            entries = parse_entries(root)
            if not entries:
                break  # no more results for this query

            new_count = 0
            for e in entries:
                if not in_date_range(e):
                    continue
                if e["arxiv_id"] not in papers_by_id:
                    papers_by_id[e["arxiv_id"]] = e
                    new_count += 1

            print(f"  got {len(entries)} results (start={start}), {new_count} new unique papers "
                  f"(total so far: {len(papers_by_id)})")

            if len(entries) < MAX_RESULTS_PER_QUERY:
                break  # reached the end of results for this query

            start += MAX_RESULTS_PER_QUERY
            time.sleep(REQUEST_DELAY_SECONDS)

        save_metadata(papers_by_id)  # save progress after each query term

    print(f"\nMetadata collection done. {len(papers_by_id)} unique papers saved to {METADATA_FILE}")

    proceed = input("\nDownload PDFs for all of these now? This can take a while. [y/N] ")
    if proceed.lower().startswith("y"):
        print("Downloading PDFs...")
        for i, entry in enumerate(papers_by_id.values(), 1):
            print(f"[{i}/{len(papers_by_id)}] {entry['arxiv_id']}")
            download_pdf(entry)
        print(f"\nDone. PDFs saved under {PDF_DIR}/")
    else:
        print("Skipped PDF download. You can re-run this script anytime to resume "
              "(it will skip already-downloaded files and already-seen metadata).")


if __name__ == "__main__":
    main()