# 5-8 minute project explanation video

Target duration: about 7 minutes. Record the working application and your own voice. Use this as a guide, not a claim that every step has already been completed. Rehearse once after the live-model preflight passes. Never display `.env` secrets.

## 0:00-0:40 - problem understanding

“Hi, I am Ayan Pasha G.N from BMSIT&M. I selected ASTRA INTEL. Technical documents can be long, and finding a specific answer manually is slow. My solution lets users upload a document, summarize it and ask questions, with quotations and page citations to verify the answers.

“I built on my existing Advanced RAG project with permission to reuse previous work. The main change is making the system document-only and traceable.”

Show the app title and selected challenge in README.

## 0:40-2:10 - live demonstration

Upload one of ASTRA's public starter PDFs. If using the included synthetic samples, state clearly that they are fictional test documents.

“This upload extracts text page by page, makes chunks and indexes them. Here is the concise summary. Now I will ask about the document's major applications. This answer includes a source. Clicking it opens the corresponding page with the supporting quotation highlighted.”

Ask a follow-up and demonstrate visible chat history.

“Now I will ask something the document does not specify, such as operational range in this sample. The system should refuse unsupported claims rather than use web knowledge.”

Upload/select the second sample, compare battery endurance and show citations from both sources. Do not edit out a meaningful failure and then claim it never occurs. If generation is slow, explain that local inference has a latency tradeoff; keep at least one real end-to-end interaction visible.

## 2:10-3:30 - complete architecture

Open `docs/architecture.svg` or the README Mermaid diagram. It must also be in the repository.

“The browser sends requests to FastAPI. The upload pipeline extracts PDF text or uses OCR for scanned pages. The recursive splitter keeps page metadata. Ollama converts chunks into vectors. SQLite stores the document, chunks, vectors and conversations.

“For a question, the backend searches only the selected documents. FAISS retrieves relevant chunks by semantic similarity. The language model receives those chunks and returns structured claims with quotations. Python checks the source IDs and exact quotation text, and a second AI call checks support. The result is displayed with clickable citations and saved in the conversation.”

Mention the summary branch processes every chunk in batches. Explain local run architecture and why no public deployment is necessary for this demo.

## 3:30-4:40 - technical decisions

“My original project already used recursive splitting, Ollama embeddings and FAISS. I retained that approach and the 1000-character chunks with 200-character overlap. I chose FastAPI because I am focusing on Python backend development. SQLite keeps setup simple for a local challenge application. The frontend uses ordinary HTML, CSS and JavaScript, so there is no separate frontend build.

“The default model runs through Ollama locally. Groq is an optional hosted provider. I removed the original web fallback because the challenge requires answers from the document only. I use zero-temperature generation and cache checked answers for consistency.”

Open `intel/service.py` and explain retrieval and the quotation check. You do not need to read every line.

## 4:40-5:15 - AI assistance

“I used ChatGPT to help implement the interface, API, storage, citation validation, tests and documentation. The foundation was my earlier RAG project. I am transparent about that in the AI usage file.”

Then state exactly what you personally reviewed, changed and tested. Example ONLY after doing it: “I ran the models locally, checked the answers against the starter PDF, tested unsupported questions, and changed [specific component].” Do not invent contributions.

## 5:15-6:15 - testing and debugging

Show the actual pytest output and `artifacts/live-preflight.json` from your real-model run.

“The automated tests check file errors, source scope, page citations, persistence, caching, comparison, OCR and rejection of invalid evidence. Most automated generation tests use scripted responses, so they test the application logic, not the intelligence of a real model. I separately ran the real model and manually checked its quotations.”

Describe one or two bugs you understand. Prefer at least one you personally reproduced. State symptom, diagnosis and fix. The guide contains early fixture bugs, but do not misattribute them to yourself.

## 6:15-7:00 - limitations and improvements

“Grounding checks reduce unsupported answers but do not guarantee perfection. Small models can make mistakes or refuse too often. OCR and complex tables may extract poorly, and retrieval can miss a relevant passage. This is a local single-user application, not a production multi-user deployment.

“With more time, I would evaluate retrieval on more documents, add reranking, improve table extraction, use background jobs and build authenticated deployment support.”

Finish by showing the repository, README, architecture and setup instructions.

## Recording checklist

- Real AI provider running, not evidence-only mode.
- Video shows input, processing and actual output.
- Architecture diagram shown and explained.
- AI assistance and personal contribution honestly described.
- Debugging and limitations included.
- No keys, tokens or personal/private documents on screen.
- Audio understandable; aim for 5-8 minutes with no filler.
- Upload the video yourself and include its link in ASTRA's submission form.
