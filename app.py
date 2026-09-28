"""ASTRA INTEL API and UI. Start with: python -m uvicorn app:app --host 127.0.0.1"""
import hashlib
import logging
import shutil
import threading
from pathlib import Path
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from intel.config import Settings
from intel.documents import extract
from intel.providers import AI, ProviderError
from intel.service import Intelligence
from intel.store import Store

ROOT = Path(__file__).resolve().parent

class Question(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    document_ids: list[str] = Field(min_length=1, max_length=12)
    conversation_id: str
    compare: bool = False

class Selection(BaseModel):
    document_ids: list[str] = Field(min_length=1, max_length=12)


def create_app(settings=None, ai=None):
    settings = settings or Settings()
    store = Store(settings.data_dir)
    ai = ai or AI(settings)
    service = Intelligence(store, ai, settings)
    app = FastAPI(title='ASTRA INTEL', version='1.0.0')
    app.state.store, app.state.service = store, service
    lock = threading.Lock()

    @app.middleware('http')
    async def security_headers(request: Request, call_next):
        # Local single-user app. Prevent cross-origin writes; no permissive CORS.
        origin = request.headers.get('origin')
        if request.method not in ('GET', 'HEAD', 'OPTIONS') and origin and origin != str(request.base_url).rstrip('/'):
            return JSONResponse({'detail': 'Cross-origin requests are not permitted.'}, status_code=403)
        response = await call_next(request)
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Referrer-Policy'] = 'no-referrer'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; object-src 'none'; frame-ancestors 'none'; base-uri 'self'"
        return response

    @app.exception_handler(ValueError)
    async def value_error(request, exc):
        return JSONResponse({'detail': str(exc)}, status_code=400)

    @app.exception_handler(ProviderError)
    async def provider_error(request, exc):
        return JSONResponse({'detail': str(exc)}, status_code=503)

    @app.exception_handler(Exception)
    async def unexpected_error(request, exc):
        logging.exception('Request failed')
        return JSONResponse({'detail': 'Unexpected processing error. Check the server console and retry.'}, status_code=500)

    @app.get('/api/status')
    def status():
        return {'provider': settings.provider, 'chat_model': settings.groq_model if settings.provider == 'groq' else settings.chat_model,
                'embedding_model': settings.embedding_model, 'ocr_available': bool(shutil.which('tesseract')),
                'key_configured': bool(settings.groq_key) if settings.provider == 'groq' else None,
                'mode_notice': 'Evidence-only: AI summaries and semantic search are disabled.' if settings.provider == 'evidence' else
                'Ollama must be running for embeddings. Uploads remain readable if indexing fails.',
                'limits': {'max_mb': 20, 'max_pages': settings.max_pages, 'max_documents': settings.max_docs},
                'privacy': 'Local single-user workspace. Groq sends selected text to its API; Ollama keeps inference local.'}

    @app.get('/api/documents')
    def documents():
        return [{'id': d['id'], 'name': d['name'], 'pages': len(d['pages']), 'chunks': len(d['chunks']),
                 'indexed': bool(d['vectors']) and d['embedding_model'] == settings.embedding_model,
                 'warnings': d['warnings'], 'created': d['created']} for d in store.documents()]

    @app.post('/api/documents')
    def upload(file: UploadFile = File(...), ocr: bool = Form(False)):
        data = file.file.read(settings.max_bytes + 1)
        name = (file.filename or 'document.pdf').replace('\\', '/').split('/')[-1][:150]
        digest = hashlib.sha256(data).hexdigest()
        with lock:
            for d in store.documents():
                if d['digest'] == digest:
                    return {'id': d['id'], 'created': False, 'warnings': ['This document is already uploaded.']}
            if len(store.documents()) >= settings.max_docs:
                raise ValueError('Workspace limit reached. Delete a document before uploading another.')
            pages, chunks, warnings = extract(data, name, ocr, settings)
            vectors = None
            if settings.provider != 'evidence':
                try:
                    vectors = ai.embed([c['text'] for c in chunks])
                except ProviderError as exc:
                    warnings.append(str(exc) + ' Document saved; use Reindex after fixing setup.')
            ident, created = store.add(name, digest, pages, chunks, vectors, settings.embedding_model, warnings)
        return {'id': ident, 'created': created, 'warnings': warnings}

    @app.post('/api/documents/{ident}/reindex')
    def reindex(ident: str):
        with lock:
            d = service.select([ident])[0]
            vectors = ai.embed([c['text'] for c in d['chunks']])
            store.set_vectors(ident, vectors, settings.embedding_model)
        return {'indexed': True}

    @app.delete('/api/documents/{ident}')
    def delete(ident: str):
        with lock:
            service.select([ident])
            store.delete(ident)
        return {'deleted': True}

    @app.get('/api/documents/{ident}/pages/{page}')
    def page(ident: str, page: int):
        d = service.select([ident])[0]
        match = next((p for p in d['pages'] if p['number'] == page), None)
        if not match:
            raise HTTPException(404, 'Page not found.')
        return match | {'name': d['name']}

    @app.get('/api/conversations')
    def conversations():
        return store.conversations()

    @app.post('/api/conversations')
    def new_conversation():
        return {'id': store.create_conversation()}

    @app.get('/api/conversations/{ident}')
    def history(ident: str):
        return store.messages(ident)

    @app.post('/api/ask')
    def ask(body: Question):
        if not body.question.strip():
            raise ValueError('Enter a question.')
        with lock:
            return service.answer(body.question.strip(), body.document_ids, body.conversation_id, body.compare)

    @app.post('/api/summary')
    def summary(body: Selection):
        with lock:
            return service.summary(body.document_ids)

    @app.post('/api/search')
    def search(body: Question):
        if not body.question.strip():
            raise ValueError('Enter a search query.')
        with lock:
            results, mode = service.retrieve(service.select(body.document_ids), body.question)
        return {'results': results, 'mode': mode}

    @app.get('/')
    def home():
        return FileResponse(ROOT / 'static' / 'index.html')

    app.mount('/static', StaticFiles(directory=ROOT / 'static'), name='static')
    return app

app = create_app()
