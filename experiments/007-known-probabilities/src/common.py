import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(p): return json.loads(Path(p).read_text())
def dump(p,x):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n')
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def readlines(p): return [json.loads(s) for s in Path(p).read_text().splitlines()]
