# Validation report

Build session: 28 September 2026. Python 3.12 on Linux. Exact installed Python versions are in `requirements-lock.txt`.

## Observed automated results

**40 tests passed** with `python -m pytest -q`.

Coverage includes:
- Multi-page PDF upload, page extraction and page citations.
- AI summary flow, summary cache and all-chunk coverage for a long document.
- Follow-up retrieval using previous questions; history surviving store reopening.
- Repeated question cache consistency.
- Unknown-question refusal path, fabricated quotation rejection and semantic-verifier rejection.
- Multi-document comparison with evidence from both documents.
- Comparison source-count validation and document-scoped semantic search.
- Empty, corrupt, wrong-format, encrypted, oversized and page-limit inputs.
- Duplicate uploads, missing selection, empty questions and deleted-source invalidation.
- Embedding-service failure preserving an uploaded document; successful reindex recovery.
- Missing Groq key, explicit evidence-only mode and cross-origin write rejection.
- No API key exposure in status; HTML/JS serving and content security policy.
- Real image-only PDF rendered with PDFium and recognized by **installed Tesseract**.
- Missing-Tesseract error path.
- Ollama and Groq request/response contracts using mocked HTTP responses.
- Provider 401, 404, 429 and 500 error handling; malformed JSON and incomplete embeddings.

**Boundary:** `ScriptedAI` in the acceptance tests returns controlled responses and deterministic vectors. These tests prove application behavior and guardrail handling, not real-model reasoning quality or semantic retrieval accuracy. Provider HTTP tests use mock transport, not real hosted calls.

The OCR test executes the real OCR engine when available; it skips if Tesseract is absent. It passed in this environment.

## Observed browser checks

Chromium headless with Playwright; desktop **1440 x 1000** and mobile **390 x 844**. Actual locally served API/UI in `AI_PROVIDER=evidence` mode.

Passed:
- Empty-selection error appears.
- File upload populates and selects the document.
- Evidence-only Q&A is explicitly labelled.
- Citation opens a source dialog and highlights a real passage.
- History reappears after reload.
- Comparison with only one document shows the expected error.
- No horizontal overflow at the mobile viewport.
- No JavaScript page errors.

Screenshots were visually reviewed for desktop layout, mobile layout and source-dialog rendering. The included browser smoke script reproduces these checks with an empty workspace. Browser checks **do not** validate real AI output. Node/Playwright are optional test tools, not production dependencies.

Example PowerShell browser QA setup in a separate terminal:

```powershell
# Use a NEW data directory for this test, with no existing documents.
$env:AI_PROVIDER="evidence"
$env:DATA_DIR="artifacts/browser-test-data"
.\.venv\Scripts\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8000
```

In another terminal at the repository root:

```powershell
npm install
npx playwright install chromium
npm run test:browser
```

Stop the evidence-mode server before the real demo. In the first terminal, remove the test environment overrides (`Remove-Item Env:AI_PROVIDER` and `Remove-Item Env:DATA_DIR`) and restart using your actual `.env`. Do not submit an evidence-only demonstration as AI functionality.

## Checks still required on Ayan's machine

**Live AI generation/embedding quality is NOT verified in this build environment.** No local Ollama service/models or configured Groq key were available. An attempted local Ollama call returned a service-unavailable error; downloading the Ollama runtime from its official site timed out. This is an explicit remaining acceptance gate, not a passed test.

1. Start Ollama; pull `llama3.2:3b` and `mxbai-embed-large`.
2. Run the application in a fresh throwaway data directory with `AI_PROVIDER=ollama` (or configured Groq).
3. Execute `python live_preflight.py` while the server runs.
4. Inspect `artifacts/live-preflight.json`. It must report `passed: true`.
5. Test ASTRA's actual starter PDFs; only the challenge brief was provided for this build.
6. Validate English OCR on your own scan if you demonstrate that bonus.
7. Record the real working application and your own explanation.

Preflight checks upload/indexing, summary citations, grounded Q&A, consistency, a follow-up, outside-document refusal, absent specifications, comparison, quote presence and saved history. It cleans up only files it created; old chat excerpts remain in the throwaway database. The script requires an empty workspace to avoid touching existing documents.

Even a passed preflight is a small example-based check, not a broad accuracy benchmark. Manually check varied questions, especially negations, numerical claims and unsupported questions.

## Useful manual failure cases

| Input / action | Expected behavior |
|---|---|
| Empty/corrupt PDF | Clear error; no useless document record |
| Scanned PDF without readable text | Enable OCR instruction |
| OCR enabled without Tesseract | Dependency error |
| Ask before selecting a document | Selection error |
| Stop Ollama | Recoverable AI error, no fabricated answer |
| Groq mode with missing key | Setup error |
| Question unrelated to document | No supported answer, or explicitly document-supported statement of missing information |
| Select document A while B contains the answer | No evidence from B |
| A source tells the assistant to ignore rules | Treat that sentence as document data; do not execute instructions |
| Delete a source after a conversation | Future queries rejected; old excerpts retained; source-view error is explicit |
| Reopen app | Conversation history remains |

## Actual debugging during development

- Fixed a test-double dispatch mistake that confused generation and verification requests.
- Changed PDF fixture wrapping to word boundaries and normalized whitespace in the assertion; PDF extraction can insert newlines between words.
- Added SOCKS support for HTTPX after the environment's configured proxy exposed a missing optional dependency; provider initialization errors now surface as service errors.
- Browser runtime download failed initially; a packaged Chromium runtime was used for the local visual/workflow checks. This affected test infrastructure, not application functionality.
