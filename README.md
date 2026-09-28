# ASTRA INTEL

**Challenge 01 · Document Intelligence · ASTRA Software Team 2026-27**

Upload a public document, generate a concise summary, ask questions, and trace each accepted claim to its document and page. Built by Ayan Pasha G.N with disclosed ChatGPT assistance, evolving his existing **Advanced RAG** project.

## Features

- PDF, TXT and Markdown upload; page-aware extraction and recursive chunking.
- Document summaries covering all chunks through hierarchical reduction.
- Question answering strictly scoped to selected documents, with no web search fallback.
- Source quotations, page citations and highlighted extracted-page evidence.
- Conversation history persisted in SQLite and follow-up question handling.
- Multiple documents, semantic search and two-document comparison.
- Exact quotation validation and a second AI entailment check; unsupported claims withheld.
- Optional English OCR for scanned PDF pages using Tesseract.
- Fully local Ollama inference or optional Groq generation with local embeddings.
- File validation, provider/key errors, recovery by reindexing and duplicate detection.

## Stack and reuse

Python 3.12, FastAPI, vanilla HTML/CSS/JavaScript, SQLite, pypdf, LangChain recursive text splitter, NumPy, FAISS, Ollama, optional Groq, PDFium and Tesseract.

This challenge branch reuses the original project's recursive splitting configuration, Ollama embedding/FAISS retrieval approach and retrieve-then-generate design. It replaces website ingestion with page-aware uploads, removes external web answering, and separates UI, API, storage and AI processing.

## Quick start - Windows PowerShell

Install Python 3.12 and Ollama first. From the downloaded/cloned repository root:

```powershell
git clone --branch astra-intel-challenge https://github.com/ayanpashagn-glitch/advanced-rag-pipeline.git astra-intel
cd astra-intel
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
ollama pull llama3.2:3b
ollama pull mxbai-embed-large
.\.venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8000
```

Open **http://127.0.0.1:8000**. API docs: **http://127.0.0.1:8000/docs**.

If Ollama is not running, open the Ollama desktop application or run `ollama serve` in another terminal. Do not run a second server if one is already listening. First model downloads require internet and several GB of disk. A local model can be slow on a laptop; a stronger model can improve grounding at the cost of memory and latency.

After initial Ollama/model setup, `START_WINDOWS.bat` creates the Python environment if necessary, installs requirements and starts the app. Keep its console open.

## macOS / Linux

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
ollama pull llama3.2:3b
ollama pull mxbai-embed-large
.venv/bin/python -m uvicorn app:app --host 127.0.0.1 --port 8000
```

## Environment variables

| Variable | Default / purpose |
|---|---|
| `AI_PROVIDER` | `ollama`; alternatives `groq`, `evidence` |
| `OLLAMA_URL` | `http://127.0.0.1:11434`; server-controlled, never accepted from a document |
| `CHAT_MODEL` | `llama3.2:3b`, local generation |
| `EMBEDDING_MODEL` | `mxbai-embed-large`, local semantic embeddings |
| `GROQ_API_KEY` | Required only for `groq`; server-side only |
| `GROQ_MODEL` | `llama-3.1-8b-instant`; change if unavailable in your account |
| `DATA_DIR` | `data`; private SQLite storage, excluded from Git |

Restart after editing `.env`. If using Groq, selected evidence is sent to Groq for answering and checking. Summarization sends all chunks in batches. Ollama is still needed for embeddings. Model availability, provider quotas and terms can change; no unlimited free service is promised.

`AI_PROVIDER=evidence` provides an explicitly labelled keyword/excerpt inspection mode without AI. **It does not satisfy the AI summary/semantic-search requirements and is not the final submission configuration.** The app never silently falls back to this mode.

## OCR

Install Tesseract with English language data and ensure `tesseract --version` works in the same terminal. On Windows add its installation directory to PATH and reopen the terminal. On Ubuntu/Debian, `sudo apt install tesseract-ocr tesseract-ocr-eng`. PDF rendering dependencies are installed by pip. Enable **OCR scanned pages** before uploading a scanned PDF. If an already-uploaded scan needs OCR, delete it and upload again with OCR enabled.

OCR runs on pages with fewer than 30 extracted characters. Mixed pages with both substantial digital text and important image-only text are a known limitation. Highlighting uses extracted text, not original PDF coordinates.

## Using the app

1. Upload `samples/uav_training_brief.txt` and `samples/uav_training_update.txt` or ASTRA's actual starter PDFs.
2. Select the first document. Click **Summarize selected**.
3. Ask “What are the major applications discussed in the document?”
4. Ask “What about its battery endurance?” Open a citation and inspect the highlighted passage.
5. Ask “What is its operational range?” The examples do not specify a range; an unsupported answer should be withheld.
6. Select both documents, choose **Compare two**, and ask “Compare battery endurance.” Expect source-backed 45-minute and 60-minute statements from the synthetic examples.
7. Use **Search evidence** for semantic passage retrieval. Search scores are rankings, not factual confidence.
8. Reload the page or restart the app and reopen the conversation.

The included examples are fictional, self-created test data, not authoritative defence information or official ASTRA starter material.

## Tests and live verification

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
# With the real server and models running in another terminal:
.\.venv\Scripts\python.exe live_preflight.py
```

For Linux/macOS substitute `.venv/bin/python`. The exact Linux environment used for verification is recorded in `requirements-lock.txt`; install it instead of the flexible requirements files when reproducing that environment. `live_preflight.py` uploads self-created examples, tests the running AI pipeline, writes a local JSON report under `artifacts/`, and deletes its uploaded examples afterwards. Run it in an otherwise empty temporary demo workspace.

## Limits and future improvements

- Local single-user workspace; no login, tenant isolation, quota management or production deployment hardening. Bind to localhost. A public multi-user deployment needs authentication and isolation first.
- 12 documents, 20 MB/file, 100 pages/file and 350,000 extracted characters/file; processing is serialized to simplify consistency.
- Small models may over-refuse or misjudge entailment. Verification reduces risk but is not proof of truth. Read original sources.
- Top-k retrieval may miss relevant passages. Numerical table layout, formulas and complex PDFs may extract imperfectly.
- Long summaries use hierarchical reduction; all chunks are considered but details can be lost. Processing can take minutes.
- OCR is English-only and imperfect; mixed scanned/digital pages may need manual OCR.
- Page numbers mean PDF page order, not printed page labels. TXT/MD use page 1.
- Follow-ups use a heuristic and previous questions; ambiguous references may need restating.
- Cached answers support repeatability, not model correctness. Delete/reindex invalidates caches. Changing model identifiers changes cache keys; replacing a model under the same name requires reindexing.
- Deleted source documents invalidate future queries but old conversation excerpts remain in SQLite. Delete the local data directory to reset the whole workspace after stopping the server.
- Next improvements: retrieval evaluation on official starter PDFs, reranking, better table parsing, multilingual OCR, background jobs, robust query rewriting, export and authenticated deployment.

## Sources / attribution

- Original project: https://github.com/ayanpashagn-glitch/advanced-rag-pipeline
- Ollama API: https://docs.ollama.com/api and https://github.com/ollama/ollama/blob/main/docs/api.md
- Groq API: https://console.groq.com/docs/api-reference
- LangChain text splitters: https://docs.langchain.com/oss/python/integrations/splitters
- FAISS: https://github.com/facebookresearch/faiss
- pypdf: https://pypdf.readthedocs.io/
- Tesseract: https://github.com/tesseract-ocr/tesseract
- PDFium Python bindings: https://github.com/pypdfium2-team/pypdfium2

Dependencies retain their respective licenses; model weights have separate license terms. No blanket license is asserted for the original author's code. No ASTRA logo asset was bundled in this branch; the interface uses a text wordmark.
