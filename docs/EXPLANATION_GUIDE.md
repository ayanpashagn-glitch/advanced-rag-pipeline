# ASTRA INTEL - explanation guide for Ayan

Read this while opening the corresponding code. Practise explaining it in your own words. Do not claim checks or personal changes you have not performed.

## A natural introduction

“I chose ASTRA INTEL, the document intelligence challenge. The problem is that reading a long technical report to find one answer takes time. My application lets a user upload a document, get a summary, and ask questions. Each accepted answer includes its supporting quotation and page, so the user can verify it.

“I started from my existing Advanced RAG project, with the organizers' approval. That project already used chunking, Ollama embeddings and FAISS retrieval. For this challenge, I adapted the pipeline to uploaded documents, added page tracking and persistent conversations, and removed the web fallback. I used ChatGPT to help implement and test this version, and I disclose that in the README.”

Adapt the verbs about implementation to your actual contribution. It is fine to say “I used ChatGPT to implement X, then I reviewed and tested Y” if that is accurate.

## The pipeline, step by step

1. **The browser sends a file.** `static/app.js` uses `FormData` and calls `POST /api/documents`. No model/API key lives in the browser.
2. **FastAPI validates it.** `app.py` enforces supported file types, size and workspace limits. `intel/documents.py` checks PDF readability and rejects encrypted or empty inputs.
3. **Text is extracted page by page.** pypdf provides the text. Page 1 means the first page in the PDF file, not a printed label in the footer. OCR can turn image-only pages into text with Tesseract.
4. **Text becomes chunks.** The recursive splitter makes roughly 1000-character pieces with 200-character overlap. Chunks are cut within each page, so page identity is preserved. Overlap reduces loss of context near chunk boundaries.
5. **Chunks become vectors.** Ollama's embedding model converts text into numeric vectors that represent meaning. The model is not being trained by an upload.
6. **SQLite stores the data.** It stores extracted pages, chunks, vectors, model identity, conversations and cached answers. FAISS performs vector retrieval; SQLite handles durable storage.
7. **A question becomes a vector.** The selected documents define the search scope. FAISS compares normalized vectors using inner product, which equals cosine similarity. A small lexical component helps with exact terms.
8. **The model receives evidence.** The selected passages, question and relevant previous questions are sent to the configured local Ollama model or optional Groq model. The prompt forbids external knowledge and treats document instructions as untrusted text.
9. **The answer is checked.** The model must return structured claims with source IDs and quotations. Python rejects unknown IDs and quotes that are not present in the source. A second AI call checks whether each quote supports the whole statement. Unsupported claims are withheld.
10. **The browser displays citations.** Each citation loads the source page and highlights the quotation using safe DOM text nodes. Conversation exchanges are saved for reopening later.

## Explain it with an analogy

“The documents are books. Chunking creates index cards with page numbers. Embeddings place cards with similar meanings near each other. FAISS finds the relevant cards. The language model drafts an answer from those cards. The validator checks that the quoted lines exist and support the answer. The citation lets the user inspect the book page.”

## Why these choices?

| Choice | Reason and tradeoff |
|---|---|
| Python + FastAPI | Fits my Python/backend learning and gives typed HTTP endpoints; a separate browser UI makes the data flow clear |
| Existing splitter + embeddings + FAISS | Builds on my earlier RAG experience, avoids retraining and supports semantic retrieval |
| Vanilla frontend | Small interface without a separate frontend build step; backend remains easy to run and explain |
| SQLite | Simple durable local storage without a database server; appropriate for a single-user three-day challenge |
| Local Ollama default | No paid API required, can keep text local after model download; speed and quality depend on hardware/model |
| Optional Groq | Can provide faster hosted generation; requires credentials, connectivity and accepting hosted text processing |
| Exact quote plus semantic verifier | Checks both provenance and support; adds latency and still is not a mathematical guarantee |
| Caching | Repeated questions can return identical checked results; consistency does not itself prove correctness |

## Where to look in the code

| File | What to explain |
|---|---|
| `app.py` | Routes, request models, upload flow, source selection and error responses |
| `intel/documents.py` | Extraction, page boundaries, OCR and recursive chunks |
| `intel/providers.py` | Ollama embedding/chat endpoints and optional Groq adapter |
| `intel/retrieval.py` | Normalization, cosine FAISS ranking and lexical contribution |
| `intel/service.py` | Follow-up handling, retrieval, grounding, summary reduction and caching |
| `intel/store.py` | SQLite persistence and transactional chat exchanges |
| `static/app.js` | Uploads, question requests, chat rendering and citation highlighting |
| `tests/test_acceptance.py` | Deterministic integration tests with a scripted AI, separate from live quality evaluation |

## Summary vs question answering

“A question usually needs a few relevant passages, so I retrieve top-ranked chunks. A whole-document summary must not silently cover only the first pages. I process all chunks in batches, retain representative quoted evidence, reduce it, and generate a concise checked summary. This is slower, and a concise summary can still omit detail.”

## Follow-up questions

“The application saves messages. For follow-ups such as ‘What about its battery?’, it includes recent questions in the retrieval query. Conversation text is used for interpreting the question, never as document evidence. This is a simple heuristic and can fail for ambiguous references. A future version could use a dedicated query-rewriting step.”

## Important limitations to admit

- A valid quote does not prove the model's interpretation is correct. The verifier can also make mistakes.
- Top-k retrieval can miss relevant passages; a refusal can mean retrieval failed rather than that the document truly contains no answer.
- Tables, formulas and OCR can extract incorrectly.
- Small local models can be slow or over-refuse. Real-model quality must be evaluated on actual starter documents.
- This is a local single-user challenge app. It does not have production authentication or tenant isolation.
- Source pages are extracted text views, not overlays on the original PDF image.

## Likely discussion questions

**What is RAG?**
Retrieval-augmented generation: retrieve relevant source material and supply it to a language model before generating an answer.

**Is RAG fine-tuning?**
No. Uploading a document changes the retrieval corpus, not the model's weights.

**Why not send the whole PDF with every question?**
Extraction is still needed. Long text costs context and time; retrieval selects relevant parts. Full-document summary uses a separate all-chunk process.

**What is an embedding?**
A numeric representation of text used for similarity search. It is not a factual confidence score.

**Why FAISS and SQLite?**
FAISS finds similar vectors. SQLite stores persistent structured records. They solve different problems.

**Why remove web search?**
The challenge explicitly requires answers based only on the provided document. Web fallback would violate that requirement.

**How do you prevent hallucinations?**
I reduce them with scoped evidence, constrained JSON output, exact quote/source validation and a second support check. I do not claim zero hallucinations.

**What if the PDF tells the AI to ignore instructions?**
It is treated as untrusted document content, not a command. The system has no browsing or arbitrary execution tools. Grounding checks provide another layer, but adversarial model behavior still requires testing.

**Can someone access another user's documents?**
This version is single-user and bound to localhost. It should not be exposed as a public multi-user app without authentication and isolation.

**Why use AI to build it?**
The challenge permits it. I used AI to accelerate implementation and debugging, and I must understand and validate the result. I disclose the generated parts and my own work.

## Real debugging examples from this build

Use these only after understanding them; attribute them to the AI-assisted build session rather than pretending you personally diagnosed them.

1. An early test double identified verifier requests by the word “supported” in the prompt. That word also appeared in the normal generation prompt, causing test failures. The fix made request classification depend on the payload structure. This was a test-fixture bug, not an LLM success/failure.
2. A synthetic PDF fixture originally wrapped text by raw character count, splitting “minutes” across lines. The assertion exposed this. The fixture now wraps by words, while real extraction limitations remain documented.

Add at least one problem you personally encounter and debug when running the real models. Explain the observed symptom, the evidence you inspected and the actual fix.
