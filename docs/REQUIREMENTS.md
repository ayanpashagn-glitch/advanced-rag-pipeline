# ASTRA PDF requirement map

Source: `Astra_Software_interview.pdf`, 16 pages, provided by the candidate. Selected challenge: **01 - ASTRA INTEL**. Challenges 02 and 03 are alternative choices, not additional requirements. The PDF explicitly says choose ONE.

The organizer has confirmed to Ayan that starting from an existing project is allowed. This branch evolves `advanced-rag-pipeline` and retains the original version under `legacy/`. Do not describe the legacy project as newly written during the challenge.

“Implemented” means code exists; see TESTING.md for what was actually exercised. Real-model quality must pass the local preflight before submission.

## Mandatory product requirements (page 6)

| Requirement | Implementation | Verification |
|---|---|---|
| Upload a PDF/document | PDF, UTF-8 TXT and MD upload, multiple files | PDF upload, bad upload and browser tests |
| Extract/process content | pypdf; original recursive splitter configuration; optional OCR; page metadata | Multi-page PDF test; real Tesseract test |
| Concise summary | Hierarchical AI summary across all chunks; quotes/citations | Scripted-provider summary and long-document coverage tests; real model preflight pending |
| Questions about uploaded document | Selected-document FAISS retrieval and grounded generation | API tests and live-model preflight script |
| Only document-based answers | No web tools; scoped retrieval; exact quotation validation; separate entailment check; refusal | Invented quote and unsupported claim rejection tests; no guarantee that a model never errs |
| Relevant section/page | Each accepted claim has document name, PDF page and quote | Page citation API test; browser opens highlighted source |

## Recommended features (page 6)

| Requirement | Implementation |
|---|---|
| Usable interface and errors | Responsive upload/chat/source interface; empty, corrupt, encrypted, too large, no selection, missing key and provider-down errors |
| Multi-turn visible history | SQLite messages and conversations; previous questions included for referential follow-ups; reopening history |
| Page-level citations | Clickable citations open extracted page text and highlight matching quote |
| Consistency | Deterministic retrieval order, zero-temperature generation, cached repeated answers scoped by document/model/question/history |

Follow-up detection is heuristic and works best for short references (“its”, “their”, “what about”). Users should restate ambiguous subjects. History is never used as factual evidence.

## Every INTEL bonus item (page 7)

| Bonus | Implementation / dependency |
|---|---|
| Multiple documents | Up to 12 per local workspace; explicit source selection |
| Semantic search | Ollama embeddings + FAISS cosine search across selected documents |
| Document comparison | Exactly two selected documents, separate retrieval for each, citations from both; partial-result disclosure |
| Unsupported-answer detection | Exact source/ref validation plus LLM entailment verifier; fail closed for malformed verifier output |
| OCR | Opt-in English Tesseract OCR with PDFium rendering for pages with little text; requires Tesseract installation |
| Relevant-text highlighting | Highlighted quotation in extracted page view; not an overlay on the original PDF image |
| Local/open-source models | Default Ollama local generation and embeddings; review each chosen model's license. Groq optional |
| Conversation persistence | SQLite; survives app restart. Search previews/summaries are not chat messages; summaries are separately cached |

## Common rules and deliverables (pages 1-5, 10-16)

| Item | Status / candidate action |
|---|---|
| Own work, attributed resources | Legacy provenance and AI disclosure provided. Candidate must review and accurately fill personal contribution |
| Public or self-created data | Two clearly labelled synthetic sample documents included. Upload official starter PDFs when received |
| No harmful personal surveillance | Document intelligence only; no person tracking or surveillance functions |
| Source + dependencies + configuration | Repository, pinned tested requirements, `.env.example`, run scripts |
| README and installation | README with Windows, macOS/Linux commands |
| Deployment or exact local setup | Local demo path supplied; public deployment is not required by the PDF when impractical |
| Architecture diagram | Mermaid in README; standalone SVG for screen sharing |
| Tests, example inputs, known failure cases | TESTING.md and live_preflight.py |
| Detailed explanation text | EXPLANATION_GUIDE.md and VIDEO_SCRIPT.md |
| 5-8 minute video, working demo and architecture | Script prepared; Ayan must rehearse, record and upload his own explanation |
| AI-use disclosure | AI_USAGE.md; candidate must amend personal implementation/validation accurately |
| Limitations and future improvements | README and guide |
| No committed secrets | `.env` ignored; scan before publishing; no credentials added by this work |
| Submission form | Ayan must submit repo/branch, local instructions and recorded-video link |
| Deadline | PDF says 1 October 2026, no extensions. Exact time/form URL not provided; verify with organizers |

The PDF mentions a rubric in section 9 and technical discussion in section 10, but those sections in the supplied file are actually Timeline and Final Message. No numeric rubric, submission form URL, or starter resource files were attached. Do not invent them.

## Final candidate checklist

- [ ] Install Ollama and required models; confirm generation and embeddings work.
- [ ] Run the automated tests and live preflight with your chosen real model.
- [ ] Upload ASTRA's provided PDFs and check answers against them manually.
- [ ] Demonstrate summary, Q&A, citation opening, follow-up, unsupported question and comparison.
- [ ] Test OCR if you claim it in your demonstration.
- [ ] Read the explanation guide; explain functions without reading generated text blindly.
- [ ] Complete the personal contribution and validation disclosure truthfully.
- [ ] Record and upload the 5-8 minute video with the architecture diagram.
- [ ] Provide this branch URL and exact run instructions; submit form before the verified cutoff.
