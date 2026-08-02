# ResearchRAG

A Corpus-Scale Retrieval-Augmented Generation System for Quantization & Low-Bit LLM Inference Literature.

Unlike single-document "chat with your PDF" tools, ResearchRAG is built on a
fixed, curated corpus of research papers and answers cross-paper questions —
synthesis, contradiction detection, and timeline queries — with verified,
chunk-linked citations.

## Corpus

- **Subfield:** Quantization & low-bit inference for LLMs
- **Size:** 605 papers
- **Built:** August 2, 2026
- **Source:** arXiv (`cs.CL`, `cs.LG`)

`corpus/pdfs/` is gitignored and regenerable — see below. Only
`corpus/corpus_metadata.json` is tracked in git.

## Scripts

### `build_corpus.py`

Pulls the corpus from the arXiv API by topic search terms, dedupes by
arXiv ID, and downloads the PDFs.

    python build_corpus.py

Re-running is safe — it resumes from existing metadata/PDFs instead of
re-fetching everything.

### `check_missing.py`

Verifies that `corpus_metadata.json` and `corpus/pdfs/` are in sync (some
downloads can silently fail due to transient network errors). Compares the
two, lists any missing papers, and offers to either retry downloading them
or remove their entries from the metadata file.

Run after `build_corpus.py`, before writing gold evaluation questions:

    python check_missing.py