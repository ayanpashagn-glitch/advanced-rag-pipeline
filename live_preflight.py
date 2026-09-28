"""Exercise a running REAL-provider server. Run in an empty throwaway workspace."""
import json
from datetime import datetime, timezone
from pathlib import Path
import httpx

ROOT=Path(__file__).resolve().parent

def main():
    report={'run_at':datetime.now(timezone.utc).isoformat(),'checks':[],'passed':False}
    uploaded=[]
    with httpx.Client(base_url='http://127.0.0.1:8000',timeout=600) as client:
        def request(method,path,**kwargs):
            r=client.request(method,'/api'+path,**kwargs)
            if r.status_code>=400:
                raise RuntimeError(f'{path}: HTTP {r.status_code}: {r.text[:500]}')
            return r.json()
        def check(name, condition, result=None):
            report['checks'].append({'name':name,'passed':bool(condition),'result':result})
            print(('PASS ' if condition else 'FAIL ')+name)
            if not condition:raise AssertionError(name)
        try:
            status=request('GET','/status');report['configuration']=status
            check('Real AI provider selected',status['provider'] in ('ollama','groq'))
            check('Empty throwaway workspace',not request('GET','/documents'))
            for name in ['uav_training_brief.txt','uav_training_update.txt']:
                r=request('POST','/documents',files={'file':(name,(ROOT/'samples'/name).read_bytes(),'text/plain')})
                if r['created']:uploaded.append(r['id'])
                check('Upload '+name,r['created'],r)
            check('Semantic indexes ready',all(d['indexed'] for d in request('GET','/documents')))
            summary=request('POST','/summary',json={'document_ids':[uploaded[0]]})
            check('AI summary has citations',bool(summary.get('claims')),summary)
            conversation=request('POST','/conversations',json={})['id']
            def ask(q,ids=None,compare=False):
                return request('POST','/ask',json={'question':q,'document_ids':ids or [uploaded[0]],'conversation_id':conversation,'compare':compare})
            first=ask('What are the major applications discussed in this document?')
            check('Document Q&A returns grounded claims',first['status']=='grounded' and bool(first['claims']),first)
            repeat=ask('What are the major applications discussed in this document?')
            check('Repeated question consistent',repeat['cached'] and repeat['claims']==first['claims'])
            follow=ask('What about its battery endurance?')
            check('Follow-up returns 45-minute evidence',any('45' in c['quote'] for c in follow['claims']),follow)
            unknown=ask('What is the capital of France?')
            check('Outside-document question refused',unknown['status']=='not_found' and not unknown['claims'],unknown)
            missing=ask('What is the operational range in kilometers?')
            combined=' '.join(c['text'] for c in missing['claims']).lower()
            check('Missing specification not invented',not missing['claims'] or any(w in combined for w in ['not specif','no claim','not provide','unspecified']),missing)
            comparison=ask('Compare the battery endurance.',uploaded,True)
            check('Comparison cites both documents',{c['document_id'] for c in comparison['claims']}==set(uploaded),comparison)
            for c in first['claims']:
                page=request('GET',f'/documents/{c["document_id"]}/pages/{c["page"]}')
                check('Citation quote exists in page',' '.join(c['quote'].split()) in ' '.join(page['text'].split()))
            check('Conversation saved',len(request('GET','/conversations/'+conversation))>=12)
            report['passed']=True
        except Exception as exc:
            report['error']=str(exc);print('PREFLIGHT INCOMPLETE:',exc)
        finally:
            for ident in uploaded:
                try:request('DELETE','/documents/'+ident)
                except Exception:pass
            (ROOT/'artifacts').mkdir(exist_ok=True)
            (ROOT/'artifacts'/'live-preflight.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    return 0 if report['passed'] else 1

if __name__=='__main__':raise SystemExit(main())
