"""Fetch public ChargeAlong site details and preserve per-record source attribution.

USYD CODE CITATION ACKNOWLEDGEMENT
Generated with OpenAI Codex assistance; review required.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import json
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from urllib.parse import urlencode
import csv
from acquire import ROOT

def get_json(url):
    for attempt in range(3):
        try:
            with urlopen(Request(url,headers={'User-Agent':'COMP5339-student-data-integration/1.0'}),timeout=35) as response:
                return json.load(response)
        except (HTTPError,URLError,TimeoutError):
            if attempt==2: raise
            time.sleep(2**attempt)

def refresh_nearby():
    folder=ROOT/'data/external/chargealong_nearby';folder.mkdir(parents=True,exist_ok=True)
    with (ROOT/'data/b_handoff/data/dc_chargers.csv').open(encoding='utf-8') as stream:
        rows=list(csv.DictReader(stream))
    def retrieve(row):
        path=folder/(row['charger_id']+'.json')
        if path.exists(): return
        params={'lat':round(float(row['latitude']),4),'lng':round(float(row['longitude']),4),'radius_km':2,'limit':10}
        url='https://api.chargealong.io/v1/nearby?'+urlencode(params)
        response=get_json(url)
        path.write_text(json.dumps({'request_url':url,'retrieved_at_utc':datetime.now(timezone.utc).isoformat(),'response':response},ensure_ascii=False,indent=2),encoding='utf-8')
    failures=[]
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures={pool.submit(retrieve,row):row['charger_id'] for row in rows}
        for i,future in enumerate(as_completed(futures),1):
            try: future.result()
            except Exception as exc: failures.append({'charger_id':futures[future],'error':str(exc)})
            if i%100==0: print(f'Nearby queries {i}/{len(rows)}',flush=True)
    (folder.parent/'nearby_errors.json').write_text(json.dumps(failures,indent=2))

def refresh_details(limit=None):
    cache=json.loads((ROOT/'data/handoff/chargealong_cache.json').read_text())
    # Cache candidates within 500 m; later matching still requires operator/address evidence.
    ids={r['public_id'] for records in cache.values() for r in records if r.get('distance_km',999)<=0.5}
    for path in (ROOT/'data/external/chargealong_nearby').glob('*.json'):
        records=json.loads(path.read_text(encoding='utf-8'))['response']['data']['sites']
        ids.update(r['public_id'] for r in records if r.get('distance_km',999)<=0.5)
    ids=sorted(ids)
    folder=ROOT/'data/external/chargealong_sites';folder.mkdir(parents=True,exist_ok=True)
    missing=[eid for eid in ids if not (folder/(eid+'.json')).exists()]
    if limit: missing=missing[:limit]
    def retrieve(eid):
        url='https://api.chargealong.io/v1/sites/'+eid
        result=get_json(url)
        envelope={'request_url':url,'retrieved_at_utc':datetime.now(timezone.utc).isoformat(),'response':result}
        (folder/(eid+'.json')).write_text(json.dumps(envelope,ensure_ascii=False,indent=2),encoding='utf-8')
        return eid
    failures=[]
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures={pool.submit(retrieve,eid):eid for eid in missing}
        for i,future in enumerate(as_completed(futures),1):
            try: future.result()
            except Exception as exc: failures.append({'external_id':futures[future],'error':str(exc)})
            if i%50==0: print(f'Fetched {i}/{len(missing)} detail responses',flush=True)
    (folder.parent/'refresh_errors.json').write_text(json.dumps(failures,indent=2))
    print(f'{len(list(folder.glob("*.json")))} cached detail files; {len(failures)} failures')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--limit',type=int);p.add_argument('--nearby',action='store_true')
    args=p.parse_args()
    if args.nearby: refresh_nearby()
    refresh_details(args.limit)
