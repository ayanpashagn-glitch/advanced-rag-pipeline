# AI usage disclosure

AI Tools Used:
- ChatGPT (Codex / ChatGPT Work)

Used For:
- Reviewing the challenge brief and mapping requirements
- Inspecting the existing RAG project
- Implementation, debugging, test design and execution
- UI creation, architecture explanation and documentation

Major AI-Assisted Components:
- FastAPI application and browser interface
- Page-aware upload processing and OCR integration
- RAG service, provider adapters, citations and validation
- SQLite storage, acceptance tests and live preflight script
- README, requirements map, explanation guide and video script

Existing Work Reused:
- Ayan's `advanced-rag-pipeline` repository
- Recursive splitting settings, local embeddings and FAISS retrieval design
- Original source preserved under `legacy/`; the challenge implementation is on a separate branch
- Organizer approval to reuse an existing project, as reported by Ayan

Personally Implemented / Modified:
- Ayan: describe the earlier project's components you actually wrote or modified.
- Ayan: after reviewing this branch, list specific changes you personally make.
- Do not say you independently implemented the newly AI-generated components unless you actually reimplement them.

Validation:
- Automated integration and provider-contract checks: see TESTING.md for observed results.
- Browser and OCR checks: see TESTING.md.
- Ayan must add the real-model preflight result, manual checks on ASTRA starter PDFs and any personal debugging work after doing them.

Understanding:
- AI assistance is allowed by the brief. The candidate remains responsible for understanding the implementation, validating outputs and explaining limitations.
- The explanation guide is a study aid, not evidence that the candidate already understands or has performed the described steps.
