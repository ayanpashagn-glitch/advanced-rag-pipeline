"""Deterministic integration tests. Scripted AI validates plumbing, not real model quality."""
import io
import re
import hashlib
from dataclasses import replace
import pytest
from fastapi.testclient import TestClient
from pypdf import PdfWriter
from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject
from app import create_app
from intel.config import Settings
from intel.documents import extract
from intel.providers import AI, ProviderError
from intel.store import Store

TEXT = 'Training UAVs support mapping and disaster assessment. Battery endurance is 45 minutes. This is a fictional training example, not an operational specification.'
OTHER = 'Training UAVs support crop inspection. Battery endurance is 60 minutes. This is a fictional training example, not an operational specification.'


def pdf_bytes(pages):
    writer = PdfWriter()
    for text in pages:
        page = writer.add_blank_page(width=612, height=792)
        font = DictionaryObject({NameObject('/Type'): NameObject('/Font'),NameObject('/Subtype'): NameObject('/Type1'),NameObject('/BaseFont'): NameObject('/Helvetica')})
        page[NameObject('/Resources')] = DictionaryObject({NameObject('/Font'): DictionaryObject({NameObject('/F1'): writer._add_object(font)})})
        content = DecodedStreamObject()
        import textwrap
        lines = textwrap.wrap(text, 80)
        ops = ['BT /F1 11 Tf 40 740 Td']
        for line in lines:
            escaped = line.replace('\\','\\\\').replace('(','\\(').replace(')','\\)')
            ops.append(f'({escaped}) Tj 0 -18 Td')
        ops.append('ET')
        content.set_data('\n'.join(ops).encode('ascii'))
        page[NameObject('/Contents')] = writer._add_object(content)
    out = io.BytesIO(); writer.write(out); return out.getvalue()


class ScriptedAI:
    """Never used in production. Returns exact evidence and deterministic vectors."""
    def __init__(self):
        self.calls=[]
        self.invent=False
        self.reject=False
    def embed(self,texts):
        self.calls.append(('embed',texts))
        words=['mapping','battery','crop','disaster']
        return [[float(w in t.lower())+.01 for w in words] for t in texts]
    def generate(self,system,payload):
        self.calls.append(('generate',payload))
        if 'claims' in payload:
            return {'supported': [] if self.reject else list(range(len(payload['claims'])))}
        if 'capital of' in payload.get('question','').lower():
            return {'claims':[]}
        cs=payload['evidence'][:3]
        return {'claims':[{'text':c['text'][:250], 'ref':c['id'],
            'quote':'Invented evidence that is not in the source.' if self.invent else c['text'][:250]} for c in cs]}


@pytest.fixture
def setup(tmp_path):
    settings=Settings(data_dir=tmp_path,provider='ollama')
    ai=ScriptedAI(); app=create_app(settings,ai)
    with TestClient(app) as client:
        yield client, ai, app, settings


def upload(client, text=TEXT, name='training.txt'):
    response=client.post('/api/documents',files={'file':(name,text.encode(),'text/plain')})
    assert response.status_code==200,response.text
    return response.json()['id']


def body(client, ids, q='What is the battery endurance?', **extra):
    cid=client.post('/api/conversations',json={}).json()['id']
    return dict(question=q,document_ids=ids,conversation_id=cid,**extra)


def test_pdf_upload_page_citation(setup):
    c,ai,app,s=setup
    r=c.post('/api/documents',files={'file':('test.pdf',pdf_bytes(['Overview of training aircraft.',TEXT]),'application/pdf')})
    assert r.status_code==200,r.text
    ident=r.json()['id']
    page=c.get(f'/api/documents/{ident}/pages/2').json()
    assert '45 minutes' in ' '.join(page['text'].split())
    result=c.post('/api/ask',json=body(c,[ident])).json()
    assert result['status']=='grounded'
    assert any(x['page']==2 for x in result['claims'])


def test_summary(setup):
    c,ai,app,s=setup; ident=upload(c)
    r=c.post('/api/summary',json={'document_ids':[ident]})
    assert r.status_code==200,r.text
    assert r.json()['claims'] and r.json()['chunks_considered']>0
    assert c.post('/api/summary',json={'document_ids':[ident]}).json()['cached']


def test_followup_uses_previous_question_and_survives_restart(setup):
    c,ai,app,s=setup; ident=upload(c)
    b=body(c,[ident],q='What applications do training UAVs support?')
    assert c.post('/api/ask',json=b).status_code==200
    b['question']='What about their battery endurance?'
    assert c.post('/api/ask',json=b).status_code==200
    assert any('applications' in t for kind,p in ai.calls if kind=='embed' for t in p if 'their' in t)
    reopened=Store(s.data_dir)
    assert len(reopened.messages(b['conversation_id']))==4


def test_repeat_question_is_cached(setup):
    c,ai,app,s=setup; ident=upload(c); b=body(c,[ident])
    first=c.post('/api/ask',json=b).json(); count=len(ai.calls)
    second=c.post('/api/ask',json=b).json()
    assert second['cached'] and first['claims']==second['claims'] and len(ai.calls)==count


def test_outside_question_refuses(setup):
    c,ai,app,s=setup; ident=upload(c)
    r=c.post('/api/ask',json=body(c,[ident],q='What is the capital of France?')).json()
    assert r['status']=='not_found' and not r['claims']


def test_invented_quote_is_withheld(setup):
    c,ai,app,s=setup; ai.invent=True; ident=upload(c)
    r=c.post('/api/ask',json=body(c,[ident])).json()
    assert not r['claims'] and r['rejected_claims']>0


def test_semantically_unsupported_claim_is_withheld(setup):
    c,ai,app,s=setup; ai.reject=True; ident=upload(c)
    r=c.post('/api/ask',json=body(c,[ident])).json()
    # ScriptedAI emits extractive claims; exact source text is accepted without a
    # redundant model verification call.
    assert r['claims'] and r['rejected_claims']==0


def test_paraphrased_claim_still_requires_entailment_check(setup):
    c,ai,app,s=setup; ident=upload(c)
    original=ai.generate
    def generate(system,payload):
        if 'claims' in payload:
            return {'supported': []}
        evidence=payload['evidence'][0]
        return {'claims':[{'text':'The UAV lasts three quarters of an hour.',
            'ref':evidence['id'],'quote':'Battery endurance is 45 minutes.'}]}
    ai.generate=generate
    r=c.post('/api/ask',json=body(c,[ident])).json()
    assert not r['claims'] and r['rejected_claims']==1


def test_multi_document_comparison_cites_both(setup):
    c,ai,app,s=setup; a=upload(c); b=upload(c,OTHER,'second.txt')
    r=c.post('/api/ask',json=body(c,[a,b],compare=True)).json()
    assert {x['document_id'] for x in r['claims']}=={a,b}


def test_comparison_requires_two(setup):
    c,ai,app,s=setup; ident=upload(c)
    assert c.post('/api/ask',json=body(c,[ident],compare=True)).status_code==400


def test_scoped_search_excludes_unselected_doc(setup):
    c,ai,app,s=setup; a=upload(c); b=upload(c,OTHER,'second.txt')
    r=c.post('/api/search',json=body(c,[a])).json()
    assert r['mode']=='semantic' and all(x['document_id']==a for x in r['results'])


@pytest.mark.parametrize('name,data',[('empty.pdf',b''),('bad.pdf',b'not a pdf'),('corrupt.pdf',b'%PDF-broken'),('empty.txt',b'  \n'),('wrong.exe',b'hello'),('bad.txt',b'\xff\xfe')])
def test_bad_uploads(setup,name,data):
    c,ai,app,s=setup
    assert c.post('/api/documents',files={'file':(name,data)}).status_code==400


def test_blank_pdf(setup):
    c,ai,app,s=setup
    assert c.post('/api/documents',files={'file':('blank.pdf',pdf_bytes(['']))}).status_code==400


def test_encrypted_pdf(setup):
    c,ai,app,s=setup; writer=PdfWriter();writer.add_blank_page(100,100);writer.encrypt('secret');out=io.BytesIO();writer.write(out)
    r=c.post('/api/documents',files={'file':('locked.pdf',out.getvalue())})
    assert r.status_code==400 and 'Password' in r.json()['detail']


def test_page_limit(setup):
    c,ai,app,s=setup
    with pytest.raises(ValueError,match='page limit'):
        extract(pdf_bytes(['test']*3),'big.pdf',False,replace(s,max_pages=2))


def test_size_limit(setup):
    c,ai,app,s=setup
    with pytest.raises(ValueError,match='20 MB'):
        extract(b'x'*101,'big.txt',False,replace(s,max_bytes=100))


def test_duplicate_upload_returns_existing(setup):
    c,ai,app,s=setup; a=upload(c); b=upload(c)
    assert a==b and len(c.get('/api/documents').json())==1


def test_no_selection_and_empty_question(setup):
    c,ai,app,s=setup
    assert c.post('/api/ask',json=body(c,[])).status_code==422
    ident=upload(c)
    assert c.post('/api/ask',json=body(c,[ident],q=' ')).status_code==400


def test_delete_invalidates_cached_answer(setup):
    c,ai,app,s=setup; ident=upload(c); b=body(c,[ident])
    c.post('/api/ask',json=b)
    assert c.delete('/api/documents/'+ident).status_code==200
    assert c.post('/api/ask',json=b).status_code==400
    assert len(c.get('/api/conversations/'+b['conversation_id']).json())==2


def test_provider_failure_keeps_upload_and_reindex_recovers(setup):
    c,ai,app,s=setup; embed=ai.embed
    def fail(texts):raise ProviderError('Ollama unavailable')
    ai.embed=fail
    ident=upload(c)
    assert not c.get('/api/documents').json()[0]['indexed']
    assert c.post('/api/ask',json=body(c,[ident])).status_code==503
    ai.embed=embed
    assert c.post('/api/documents/'+ident+'/reindex').status_code==200
    assert c.get('/api/documents').json()[0]['indexed']


def test_groq_missing_key(tmp_path):
    ai=AI(Settings(data_dir=tmp_path,provider='groq',groq_key=''))
    with pytest.raises(ProviderError,match='GROQ_API_KEY'):
        ai.generate('Return JSON',{})


def test_evidence_mode_is_explicit(tmp_path):
    with TestClient(create_app(Settings(data_dir=tmp_path,provider='evidence'))) as c:
        ident=upload(c); r=c.post('/api/ask',json=body(c,[ident])).json()
        assert r['status']=='evidence_only' and r['provider']=='evidence'
        assert c.post('/api/summary',json={'document_ids':[ident]}).status_code==503


def test_cross_origin_write_rejected(setup):
    c,ai,app,s=setup
    assert c.post('/api/conversations',headers={'Origin':'https://attacker.example'}).status_code==403


def test_status_never_exposes_key(tmp_path):
    with TestClient(create_app(Settings(data_dir=tmp_path,groq_key='not-a-real-secret',provider='groq'))) as c:
        r=c.get('/api/status')
        assert 'not-a-real-secret' not in r.text and r.json()['key_configured']


def test_ui_assets_and_csp(setup):
    c,ai,app,s=setup
    assert 'Ask. Trace. Understand.' in c.get('/').text
    assert c.get('/static/app.js').status_code==200
    assert "object-src 'none'" in c.get('/').headers['Content-Security-Policy']


def test_summary_processes_every_chunk(setup):
    c,ai,app,s=setup
    content=' '.join(f'Section {i}: Training systems have battery limits and mapping capabilities. '+('Research data. '*65) for i in range(24))
    ident=upload(c,content)
    r=c.post('/api/summary',json={'document_ids':[ident]})
    assert r.status_code==200,r.text
    total=len(app.state.store.documents()[0]['chunks'])
    assert total>12 and r.json()['chunks_considered']==total
    seen={e['id'] for kind,p in ai.calls if kind=='generate' for e in p.get('evidence',[])}
    assert len(seen)==total


def test_real_tesseract_scanned_pdf(setup):
    import shutil
    if not shutil.which('tesseract'):pytest.skip('Tesseract not installed')
    from PIL import Image, ImageDraw, ImageFont
    c,ai,app,s=setup
    image=Image.new('RGB',(1400,400),'white');draw=ImageDraw.Draw(image)
    try:
        font=ImageFont.truetype('DejaVuSans.ttf',34)
    except OSError:
        font=ImageFont.load_default(size=34)
    draw.text((50,80),'Training drones support disaster mapping.',font=font,fill='black')
    out=io.BytesIO();image.save(out,format='PDF')
    pages,chunks,warnings=extract(out.getvalue(),'scanned.pdf',True,s)
    assert pages[0]['ocr'] and 'disaster mapping' in pages[0]['text'].lower()


def test_ocr_missing_dependency(setup,monkeypatch):
    from intel.documents import ocr_page
    monkeypatch.setattr('intel.documents.shutil.which',lambda x:None)
    with pytest.raises(ValueError,match='Tesseract'):
        ocr_page(b'',0)
