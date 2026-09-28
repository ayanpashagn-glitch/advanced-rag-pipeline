# Advanced RAG — LangChain Docs Q&A (Groq + FAISS)

A Streamlit RAG app answering questions over LangChain's own documentation,
using local Ollama embeddings for retrieval and Groq's hosted inference
(Llama 3.1 8B, fast/cheap) for generation — a hybrid local+cloud setup.

## Why this is the strongest RAG variant in this portfolio

Unlike the fully-local RAG project, this one separates concerns realistically:
embeddings stay local and free (Ollama), while generation uses a fast hosted
API (Groq) — a pattern closer to how RAG is actually deployed in practice,
where local embedding is cheap but local LLM inference is often too slow for
a responsive UI.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env   # add your real GROQ_API_KEY (free tier at console.groq.com)
ollama pull mxbai-embed-large
```

## Run

```bash
streamlit run app.py
```

## Notes on fixes made

- Removed a hardcoded Groq API key committed in plaintext — now loaded from
  `.env`.
- **Rebuilt the retrieval chain entirely.** The original used
  `langchain.chains.create_retrieval_chain` and `create_stuff_documents_chain`
  along with `hub.pull(...)` — the entire `langchain.chains` module was
  removed in current LangChain (1.x), and `hub.pull` moved out of the base
  package. The chain is now composed manually with LCEL, which is also the
  current recommended pattern for RAG, not a workaround.
- Fixed a variable-shadowing bug: the original reused the name `prompt` for
  both the pulled retrieval prompt template and the Streamlit text input,
  silently overwriting the prompt template with the user's question string
  on every run.

## Tech stack

Python, Streamlit, LangChain (LCEL), Groq API, Ollama (local embeddings),
FAISS
