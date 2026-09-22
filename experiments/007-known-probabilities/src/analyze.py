import csv,math,statistics as st
from collections import defaultdict
from common import ROOT,read,dump,readlines,sha
from method import payload
OUT=ROOT.parents[1]/'outputs/known-probabilities';OUT.mkdir(exist_ok=True)
cases=read(ROOT/'data/cases.json');truth=read(ROOT/'data/answers.json')
freeze=read(ROOT/'sources/frozen.json')
for name,digest in freeze['files'].items():assert sha(ROOT/name)==digest,name
pred=read(ROOT/'runs/primary-v1/predictions.json')
variants=['plain','explicit','reversed','noul','complement_inverted']
rows=[];multi=[];sum_errors=[]
def tv(a,b):return sum(abs(a[k]-b[k]) for k in a)/2
def normalized(p):return {k:v/sum(p.values()) for k,v in p.items()}
for case in cases:
 i=case['id'];a=pred.get(i);gold=truth[i]
 if a:
  assert read(ROOT/'runs/primary-v1'/i/'request.json')==payload(case)
  for key,answer in a.items():
   if answer['type']=='choice':sum_errors.append({'id':i,'question':key,'sum':sum(answer['probabilities'].values())})
 if 'outcomes' in case:
  item={'id':i,'scenario':case['state'],'truth':gold['distribution'],'derivation':gold['derivation'],'valid':a is not None}
  if a:
   item['predictions']={v:a[v]['probabilities'] for v in ['plain','explicit','reversed']}
   item['tv']={v:tv(normalized(p),gold['distribution']) for v,p in item['predictions'].items()}
   item['max_component_error']={v:max(abs(normalized(p)[k]-gold['distribution'][k]) for k in p) for v,p in item['predictions'].items()}
   item['order_tv']=tv(normalized(a['plain']['probabilities']),normalized(a['reversed']['probabilities']))
  multi.append(item);continue
 item={'id':i,'family':case['group'],'scenario':case['state'],'event':case['event'],'true_probability':gold['p'],'exact_fraction':gold['fraction'],'derivation':gold['derivation'],'valid':a is not None}
 if a:
  item.update({v:a[v]['probabilities']['event_occurs'] for v in ['plain','explicit','reversed']})
  item.update(noul=a['noul']['noul'],complement_inverted=1-a['complement']['noul'])
  item['numeric_correct']=a['numeric']['choice']==gold['numeric_correct']
  item['numeric_selected']=case['numeric_options'][a['numeric']['choice']]
  item['complement_sum']=a['noul']['noul']+a['complement']['noul']
  item['order_difference']=abs(item['plain']-item['reversed'])
  for v in variants:item[v+'_error_pp']=100*(item[v]-gold['p'])
 rows.append(item)
def metrics(rs,v):
 errors=[r[v]-r['true_probability'] for r in rs if r['valid']]
 return {'valid':len(errors),'total':len(rs),'mae_pp':100*st.mean(map(abs,errors)),'rmse_pp':100*math.sqrt(st.mean(e*e for e in errors)),'signed_error_pp':100*st.mean(errors),'max_error_pp':100*max(map(abs,errors)),**{f'within_{t}pp':sum(abs(e)<=t/100+1e-9 for e in errors) for t in [1,5,10]}}
aggregate={v:metrics(rows,v) for v in variants}
families={g:{v:metrics([r for r in rows if r['family']==g],v) for v in variants} for g in sorted({r['family'] for r in rows})}
subsets={label:{v:metrics([r for r in rows if (r['true_probability'] in [0,1])==certain],v) for v in variants} for label,certain in [('certain',True),('uncertain',False)]}
valid=[r for r in rows if r['valid']]
coherence={'mean_order_difference_pp':100*st.mean(r['order_difference'] for r in valid),'max_order_difference_pp':100*max(r['order_difference'] for r in valid),'mean_complement_sum_error_pp':100*st.mean(abs(r['complement_sum']-1) for r in valid),'max_complement_sum_error_pp':100*max(abs(r['complement_sum']-1) for r in valid),'mean_choice_noul_gap_pp':100*st.mean(abs(r['plain']-r['noul']) for r in valid),'max_raw_choice_sum_error':max(abs(r['sum']-1) for r in sum_errors)}
repeats=[]
for name in ['repeat-1','repeat-2']:
 rp=read(ROOT/'runs'/name/'predictions.json');diffs=[];identical=0;answered=0
 for case in cases[:10]:
  i=case['id']
  if i not in rp or i not in pred:continue
  assert read(ROOT/'runs'/name/i/'request.json')==payload(case)
  answered+=1
  def vector(a):return [v for key in sorted(a) for v in ([a[key]['noul']] if a[key]['type']=='noul' else [a[key]['probabilities'][k] for k in sorted(a[key]['probabilities'])])]
  a=vector(pred[i]);b=vector(rp[i]);identical+=a==b;diffs.extend(abs(x-y) for x,y in zip(a,b))
 repeats.append({'run':name,'answered':answered,'total':10,'identical_case_vectors':identical,'max_component_change_pp':100*max(diffs),'mean_component_change_pp':100*st.mean(diffs)})
latest={x['call_id']:x for x in readlines(ROOT/'runs/api_ledger.jsonl')};calls=list(latest.values())
accounting={}
for name in ['primary-v1','repeat-1','repeat-2']:
 cs=[c for c in calls if c['run']==name]
 accounting[name]={**read(ROOT/'runs'/name/'summary.json'),'api_attempts':len(cs),'input_tokens':sum(c.get('usage',{}).get('input_tokens',0) for c in cs),'output_tokens':sum(c.get('usage',{}).get('output_tokens',0) for c in cs),'estimated_cost_usd':sum(c['charge'] for c in cs),'median_request_seconds':st.median(c['seconds'] for c in cs)}
summary={'model':'jev-1.13.0','binary':aggregate,'by_family':families,'by_certainty':subsets,'numeric_correct':sum(r.get('numeric_correct',False) for r in rows),'numeric_total':len(rows),'baseline_half_mae_pp':100*st.mean(abs(.5-r['true_probability']) for r in rows),'coherence':coherence,'repeats':repeats,'accounting':accounting,'total_estimated_cost_usd':sum(c['charge'] for c in calls),'multiclass_mean_tv':{v:st.mean(r['tv'][v] for r in multi if r['valid']) for v in ['plain','explicit','reversed']}}
result={'summary':summary,'binary_cases':rows,'multiclass_cases':multi,'raw_probability_sums':sum_errors}
dump(ROOT/'runs/primary-v1/analysis.json',result);dump(OUT/'results.json',result)
with (OUT/'binary-results.csv').open('w') as f:
 fields=list(rows[0]);w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
with (OUT/'multiclass-results.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['case','scenario','variant','outcome','exact_probability','raw_jev_probability','raw_sum','normalized_jev_probability'])
 for r in multi:
  if not r['valid']:w.writerow([r['id'],r['scenario'],'FAILED']);continue
  for v,p in r['predictions'].items():
   for k in p:w.writerow([r['id'],r['scenario'],v,k,r['truth'][k],p[k],sum(p.values()),normalized(p)[k]])
print(__import__('json').dumps(summary,indent=2))
