"""Page-aware parsing and the original project's recursive chunking strategy."""
import io
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter


def clean(text):
    return re.sub(r'[ \t]+', ' ', text.replace('\x00', '')).strip()


def ocr_page(data, page_number):
    if not shutil.which('tesseract'):
        raise ValueError('OCR requires Tesseract on PATH. Install it or upload a text-based PDF.')
    import pypdfium2 as pdfium
    with tempfile.TemporaryDirectory() as temp:
        with pdfium.PdfDocument(data) as pdf:
            page = pdf[page_number]
            if page.get_width() * page.get_height() > 4_000_000:
                raise ValueError('Scanned page dimensions are too large for OCR.')
            bitmap = page.render(scale=2)
            image = bitmap.to_pil()
            path = Path(temp) / 'page.png'
            image.save(path)
            image.close()
            bitmap.close()
            page.close()
        try:
            result = subprocess.run(['tesseract', str(path), 'stdout', '-l', 'eng'],
                                    capture_output=True, text=True, timeout=45)
        except subprocess.TimeoutExpired as exc:
            raise ValueError('OCR timed out. Try a smaller or clearer PDF.') from exc
        if result.returncode:
            raise ValueError('OCR failed. Check the Tesseract English language pack.')
        return clean(result.stdout)


def extract(data, filename, use_ocr, settings):
    if not data:
        raise ValueError('The uploaded file is empty.')
    if len(data) > settings.max_bytes:
        raise ValueError('File exceeds the 20 MB limit.')
    suffix = Path(filename).suffix.lower()
    warnings = []
    if suffix in ('.txt', '.md'):
        try:
            text = data.decode('utf-8-sig')
        except UnicodeDecodeError as exc:
            raise ValueError('Text documents must use UTF-8 encoding.') from exc
        pages = [{'number': 1, 'text': clean(text), 'ocr': False}]
    elif suffix == '.pdf':
        if not data.lstrip().startswith(b'%PDF-'):
            raise ValueError('This file is not a valid PDF.')
        try:
            reader = PdfReader(io.BytesIO(data))
            if reader.is_encrypted:
                raise ValueError('Password-protected PDFs are not supported. Upload an unlocked copy.')
            if len(reader.pages) > settings.max_pages:
                raise ValueError(f'PDF exceeds the {settings.max_pages}-page limit.')
            pages = []
            chars = 0
            for n, page in enumerate(reader.pages):
                # pypdf expands content streams; reject unusually large streams before text extraction.
                contents = page.get_contents()
                if contents and len(contents.get_data()) > 8_000_000:
                    raise ValueError('A PDF page is too complex. Export a simpler PDF.')
                text = clean(page.extract_text() or '')
                was_ocr = False
                if len(text) < 30 and use_ocr:
                    text = ocr_page(data, n)
                    was_ocr = True
                if not text:
                    warnings.append(f'Page {n+1} has no readable text; enable OCR for scanned pages.')
                chars += len(text)
                if chars > settings.max_chars:
                    raise ValueError('Document contains too much text. Split it into smaller files.')
                pages.append({'number': n+1, 'text': text, 'ocr': was_ocr})
        except ValueError:
            raise
        except Exception as exc:
            raise ValueError('Could not read this PDF. It may be corrupt or unsupported.') from exc
    else:
        raise ValueError('Supported formats: PDF, UTF-8 TXT and Markdown.')
    if sum(len(p['text']) for p in pages) > settings.max_chars:
        raise ValueError('Document contains too much text. Split it into smaller files.')
    if not any(p['text'].strip() for p in pages):
        raise ValueError('No readable text found. For a scanned PDF, enable OCR and install Tesseract.')
    if any(p['ocr'] for p in pages):
        warnings.append('OCR was used. Recognition may be imperfect; verify important quotations against the original.')
    # Reused from advanced-rag-pipeline: 1000-character recursive chunks, 200-character overlap.
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = []
    for page in pages:
        for text in splitter.split_text(page['text']):
            chunks.append({'id': f'p{page["number"]}c{len(chunks)+1}', 'page': page['number'], 'text': text})
    return pages, chunks, warnings
