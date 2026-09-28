"""Provider HTTP contract tests using mocked transport, never fake production AI."""
import httpx
import pytest
from intel.config import Settings
from intel.providers import AI, ProviderError


def test_ollama_http_contract(monkeypatch,tmp_path):
    calls=[]
    def post(url,**kwargs):
        calls.append((url,kwargs))
        payload={'embeddings':[[1,2],[3,4]]} if url.endswith('/embed') else {'message':{'content':'{"claims":[]}'}}
        return httpx.Response(200,json=payload,request=httpx.Request('POST',url))
    monkeypatch.setattr(httpx,'post',post)
    ai=AI(Settings(data_dir=tmp_path,provider='ollama'))
    assert ai.embed(['one','two'])==[[1,2],[3,4]]
    assert ai.generate('Return JSON',{})=={'claims':[]}
    assert calls[0][1]['json']['input']==['one','two']
    assert calls[1][1]['json']['options']['temperature']==0
    assert calls[1][1]['json']['format']=='json'


def test_groq_http_contract(monkeypatch,tmp_path):
    calls=[]
    def post(url,**kwargs):
        calls.append((url,kwargs))
        return httpx.Response(200,json={'choices':[{'message':{'content':'{"claims":[]}'}}]},request=httpx.Request('POST',url))
    monkeypatch.setattr(httpx,'post',post)
    ai=AI(Settings(data_dir=tmp_path,provider='groq',groq_key='test-placeholder'))
    assert ai.generate('Return JSON',{})=={'claims':[]}
    assert calls[0][0]=='https://api.groq.com/openai/v1/chat/completions'
    assert calls[0][1]['headers']['Authorization']=='Bearer test-placeholder'
    assert calls[0][1]['json']['response_format']=={'type':'json_object'}


@pytest.mark.parametrize('status,expected',[(401,'key rejected'),(429,'rate limit'),(404,'unavailable'),(500,'HTTP 500')])
def test_provider_status_errors(monkeypatch,tmp_path,status,expected):
    monkeypatch.setattr(httpx,'post',lambda url,**kwargs:httpx.Response(status,request=httpx.Request('POST',url)))
    with pytest.raises(ProviderError,match=expected):
        AI(Settings(data_dir=tmp_path)).generate('Return JSON',{})


def test_invalid_model_json(monkeypatch,tmp_path):
    monkeypatch.setattr(httpx,'post',lambda url,**kwargs:httpx.Response(200,json={'message':{'content':'not JSON'}},request=httpx.Request('POST',url)))
    with pytest.raises(ProviderError,match='invalid structured'):
        AI(Settings(data_dir=tmp_path)).generate('Return JSON',{})


def test_embedding_batch_incomplete(monkeypatch,tmp_path):
    monkeypatch.setattr(httpx,'post',lambda url,**kwargs:httpx.Response(200,json={'embeddings':[]},request=httpx.Request('POST',url)))
    with pytest.raises(ProviderError,match='incomplete batch'):
        AI(Settings(data_dir=tmp_path)).embed(['example'])
