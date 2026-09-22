"""Bounded, resumeless named runs; no scoring labels enter inference."""
import concurrent.futures as cf, fcntl, json, os, signal, threading, time, urllib.request, urllib.error, uuid, sys
from common import ROOT,dump,readlines,sha
from method import payload
RATE=.042/1e6
RESERVE=65536*RATE
stop=threading.Event()
for sig in (signal.SIGINT,signal.SIGTERM):signal.signal(sig,lambda *_:stop.set())
class NoRedirect(urllib.request.HTTPRedirectHandler):
 def redirect_request(self,*args,**kwargs):return None
class API:
 def __init__(self):
  self.key=os.environ.get('TYPESAFE_API_KEY','').strip()
  if not self.key:raise RuntimeError('TYPESAFE_API_KEY missing')
  self.lock=threading.Lock();self.ledger=ROOT/'runs/api_ledger.jsonl';self.next=0
  latest={r['call_id']:r for r in readlines(self.ledger)} if self.ledger.exists() else {}
  self.spent=sum(r['charge'] for r in latest.values())
 def log(self,r):
  with self.ledger.open('a') as f:f.write(json.dumps(r)+'\n');f.flush();os.fsync(f.fileno())
 def call(self,joke,folder):
  p=payload(joke);dump(folder/'request.json',p)
  for attempt in range(3):
   if stop.is_set() or (ROOT/'STOP').exists():raise RuntimeError('Stopped')
   cid=uuid.uuid4().hex
   with self.lock:
    if self.spent+RESERVE>5:stop.set();raise RuntimeError('Budget exhausted')
    self.spent+=RESERVE;self.log({'call_id':cid,'charge':RESERVE,'event':'reserved','run':folder.parent.name})
    delay=max(0,self.next-time.monotonic());self.next=max(self.next,time.monotonic())+.12
   if stop.wait(delay):raise RuntimeError('Stopped with conservative reservation')
   t=time.perf_counter();r={'call_id':cid,'event':'finished','charge':RESERVE,'run':folder.parent.name};retry=False;out=None
   try:
    req=urllib.request.Request('https://api.typesafe.ai/v1/systemone',data=json.dumps(p).encode(),headers={'Authorization':'Bearer '+self.key,'Content-Type':'application/json'})
    with urllib.request.build_opener(NoRedirect()).open(req,timeout=60) as resp:out=json.loads(resp.read())
    dump(folder/f'response-{attempt}.json',out)
    r['usage']=out.get('usage',{});r['model']=out.get('model');n=r['usage'].get('input_tokens')
    if isinstance(n,int):r['charge']=n*RATE;r['estimated_cost_usd']=n*RATE
    assert out['model']==p['model']
    assert set(out['answers'])==set(p['questions'])
    for key,a in out['answers'].items():
     q=p['questions'][key]
     assert a['type']==q['type']
     if a['type']=='noul':assert isinstance(a['noul'],(int,float)) and 0<=a['noul']<=1
     else:
      probs=a['probabilities'];assert set(probs)==set(q['criteria'])
      assert all(isinstance(v,(int,float)) and 0<=v<=1 for v in probs.values())
      assert abs(sum(probs.values())-1)<=len(probs)*.005+1e-6
      assert a['choice'] in probs
   except Exception as e:
    r['error']=str(e).replace(self.key,'[REDACTED]')[:300];retry=isinstance(e,(urllib.error.URLError,TimeoutError));out=None
   finally:
    r['seconds']=time.perf_counter()-t
    with self.lock:self.spent+=r['charge']-RESERVE;self.log(r)
   if out is not None:return out['answers']
   if not retry:break
   if stop.wait(2**attempt):break
  raise RuntimeError('API failure; inspect trace')

if __name__=='__main__':
 from common import read
 lock=(ROOT/'runs/.runner.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 from method import MODEL
 freeze=read(ROOT/'sources/frozen.json')
 for name,digest in freeze['files'].items():assert sha(ROOT/name)==digest,name
 name=sys.argv[1] if len(sys.argv)>1 else 'primary-v1'
 assert name in ['primary-v1','repeat-1','repeat-2']
 rows=read(ROOT/'data/cases.json')
 if name!='primary-v1':rows=rows[:10]
 folder=ROOT/'runs'/name;folder.mkdir(exist_ok=False)
 api=API();t=time.perf_counter();pred={};errors=[]
 def call(row):
  try:return row['id'],api.call(row,folder/row['id']),None
  except Exception as e:return row['id'],None,str(e)
 with cf.ThreadPoolExecutor(max_workers=4) as pool:
  for key,answers,error in pool.map(call,rows):
   if answers is not None:pred[key]=answers
   else:errors.append({'id':key,'error':error})
   dump(folder/'predictions.json',pred)
   if (len(pred)+len(errors))%20==0:print(json.dumps({'complete':len(pred),'failed':len(errors),'budget_charge':api.spent}),flush=True)
 dump(folder/'summary.json',{'requested':len(rows),'answered':len(pred),'errors':errors,'wall_seconds':time.perf_counter()-t,'budget_charge_cumulative':api.spent})
