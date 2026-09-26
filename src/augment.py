"""Reconstruct supported attributes from cached responses and explicit matching evidence.

USYD CODE CITATION ACKNOWLEDGEMENT
Generated with OpenAI Codex assistance. B/C inputs and original selections are retained.
"""
import json
import re
from acquire import ROOT
import pandas as pd

ALIASES = {
    'evie':'evie','evienetworks':'evie','tesla':'tesla','teslamotors':'tesla',
    'teslateslaonlycharging':'tesla','tesladestination':'tesla','teslaincludingnontesla':'tesla',
    'bp':'bp','bpaustralia':'bp','bppulse':'bp','bppulseau':'bp',
    'ampol':'ampol','ampcharge':'ampol','ampolampcharge':'ampol','nrma':'nrma','nrmaelectric':'nrma',
    'chargehub':'chargehub','chargefox':'chargefox','jolt':'jolt',
    'exploren':'exploren','evup':'evup','engie':'engie','everty':'everty',
    'eveaustralia':'eveaustralia','wevolt':'wevolt'
}
def canonical(text):
    key=re.sub('[^a-z0-9]','',str(text).lower())
    return ALIASES.get(key,key)

def street(text):
    text=str(text).lower().replace('\\n',' ')
    text=text.replace('new south wales',' ').replace('australia',' ').replace('nsw',' ')
    text=re.sub(r'\b\d{4}\b',' ',text)
    replacements={'street':'st','road':'rd','avenue':'ave','parade':'pde','highway':'hwy','drive':'dr','terrace':'tce','place':'pl','lane':'ln','way':'wy','crescent':'cres','circuit':'cct','close':'cl','boulevard':'blvd','boulevarde':'blvd','freeway':'motorway','fwy':'motorway'}
    tokens=re.findall(r'[a-z]+|\d+',text)
    return [replacements.get(t,t) for t in tokens]

def address_evidence(left,right):
    a,b=street(left),street(right)
    # Require at least one shared street name immediately followed by a road suffix.
    suffixes={'st','rd','ave','pde','hwy','dr','tce','pl','ln','wy','cres','cct','cl','blvd','motorway'}
    pairs=lambda x:{(x[i-1],t) for i,t in enumerate(x) if i and t in suffixes}
    common=pairs(a)&pairs(b)
    typo=False
    if not common:
        def one_edit(x,y):
            if min(len(x),len(y))<5 or abs(len(x)-len(y))>1: return False
            if len(x)==len(y): return sum(u!=v for u,v in zip(x,y))==1
            if len(x)>len(y): x,y=y,x
            return any(y[:i]+y[i+1:]==x for i in range(len(y)))
        typo=any(sa==sb and one_edit(na,nb) for na,sa in pairs(a) for nb,sb in pairs(b))
        if not typo: return False,'street_not_confirmed'
    # House-number sets/ranges can differ (e.g. 1975/1985 vs 1985); require overlap.
    def numbers(tokens):
        result=set()
        for t in tokens:
            if t.isdigit(): result.add(int(t))
            elif result: break
        return result
    na,nb=numbers(a),numbers(b)
    if na and nb and not na&nb:
        # A short street number range is accepted only when one observed endpoint falls within it.
        overlap=(len(na)==2 and max(na)-min(na)<=100 and any(min(na)<=x<=max(na) for x in nb)) or (len(nb)==2 and max(nb)-min(nb)<=100 and any(min(nb)<=x<=max(nb) for x in na))
        if not overlap: return False,'house_number_conflict'
    if typo:
        return (True,'street_and_number_one_character_difference') if na and nb else (False,'street_typo_without_number')
    return True,'street_and_number' if na and nb else 'street_without_number'

def reconcile_postcode(row, site, data, distance, address_rule):
    """Resolve a conflicting *matching* postcode only with operator-backed evidence.

    Never changes the stored B postcode. A <=30 m location, exact numbered street,
    shared locality and matching address-suffix postcode are all mandatory.
    Directory-only provenance and typographical street matches cannot qualify.
    """
    source_post = re.search(r'\b(\d{4})\s*(?:Australia)?\s*$', row.station_address, re.I)
    external_post = re.search(r'\b(\d{4})\s*(?:Australia)?\s*$', site['address'], re.I)
    operator_keys = {'evie': 'evie', 'tesla': 'tesla', 'ampol': 'ampol', 'bppulse': 'bp'}
    backed = any(operator_keys.get(s['key']) == canonical(row.operator_name)
                 for s in data.get('sources', []) if s['key'] in operator_keys)
    locality = data.get('locality', {}).get('name', '').lower().strip()
    # ChargeAlong detail stores locality beside site/sources, not inside site.
    shared_locality = bool(locality) and locality in row.station_address.lower() and locality in site['address'].lower()
    return bool('postcode_address_conflict' in row.quality_flags
                and source_post and external_post and source_post[1] == external_post[1]
                and address_rule == 'street_and_number' and distance <= 30
                and backed and shared_locality)

def rebuild(b,c,ident,distance_m):
    ocm=json.loads((ROOT/'data/handoff/ocm_cache.json').read_text())
    ca=json.loads((ROOT/'data/handoff/chargealong_cache.json').read_text())
    candidates={}
    for key,records in ca.items():
        bucket=candidates.setdefault(key.split('|')[0],{})
        for record in records: bucket[record['public_id']]=record
    for path in (ROOT/'data/external/chargealong_nearby').glob('*.json'):
        records=json.loads(path.read_text(encoding='utf-8'))['response']['data']['sites']
        bucket=candidates.setdefault(path.stem,{})
        for record in records: bucket[record['public_id']]=record
    details={}
    for path in (ROOT/'data/external/chargealong_sites').glob('*.json'):
        envelope=json.loads(path.read_text(encoding='utf-8'))
        details[path.stem]=envelope
    original_log=pd.read_csv(ROOT/'data/handoff/matching_log.csv',dtype=str,keep_default_na=False).set_index('charger_id')
    original=c.set_index('charger_id')
    matches=[];attributes=[];evidence=[];provenance=[];changes=[]
    def add_attr(cid,name,value,unit,source,eid,url,when,notes=''):
        if value is None or value=='' or value==[] or str(value).lower()=='unknown': return
        attributes.append(dict(attribute_id=ident('attr',cid,name,source),charger_id=cid,attribute_name=name,
            attribute_value=json.dumps(value,ensure_ascii=False) if isinstance(value,(list,dict)) else str(value),
            attribute_unit=unit,original_attribute_name=name,source_name=source,external_id=eid,source_url=url,
            retrieved_at_utc=when,notes=notes))
    for _,row in b.iterrows():
        cid=row.charger_id;prior=original.loc[cid];oldlog=original_log.loc[cid]
        selected=None;eligible=[]
        # Replay all OCM candidates using deterministic evidence rather than inheriting
        # a decision label. The original C selection remains in the change audit.
        ocm_eligible=[]
        for record in ocm.get(cid,[]):
            eid=str(record['ID'])
            addr=record['AddressInfo']
            distance=distance_m(float(row.latitude),float(row.longitude),float(addr['Latitude']),float(addr['Longitude']))
            op=record.get('OperatorInfo',{}).get('Title','')
            post=str(addr.get('Postcode','')).strip()
            op_ok=canonical(op)==canonical(row.operator_name)
            postcode_ok=not post or post==row.postcode
            address_ok,address_rule=address_evidence(row.station_address,addr.get('AddressLine1',''))
            connections=record.get('Connections',[])
            dc_evidence=any(x.get('CurrentTypeID')==30 or x.get('CurrentType',{}).get('Title')=='DC' or float(x.get('PowerKW') or 0)>22 for x in connections)
            threshold=500 if address_rule=='street_and_number' and post==row.postcode else 100
            if address_rule=='street_and_number_one_character_difference':
                threshold=30
                postcode_ok=bool(post) and post==row.postcode
            ok=op_ok and postcode_ok and distance<=threshold and address_ok and dc_evidence and 'postcode_address_conflict' not in row.quality_flags
            evidence.append(dict(charger_id=cid,source='Open Charge Map',external_id=eid,distance_m=distance,
                operator_match=op_ok,address_rule=address_rule,postcode_match=postcode_ok,independent_source=True,eligible=ok,
                reason='accepted_candidate' if ok else 'OCM_evidence_incomplete_or_conflicting',source_address=row.station_address,external_address=addr.get('AddressLine1','')))
            if ok: ocm_eligible.append((distance,eid,record))
        if ocm_eligible:
            distance,eid,record=min(ocm_eligible,key=lambda x:(x[0],x[1]))
            # C's batch processing timestamp is known, while raw HTTP retrieval time
            # was not embedded in the original OCM cache. Do not invent it.
            when=oldlog.retrieved_at_utc or None
            selected=('Open Charge Map',eid,record,distance,when,'OCM cache replay: operator, street/number, postcode and DC evidence; <=100 m or <=500 m with house-number and postcode agreement; nearest eligible')
        # Re-evaluate all delivered nearby candidates, not just C's chosen fallback.
        if selected is None:
            for eid,nearby in candidates.get(cid,{}).items():
                if eid not in details: continue
                envelope=details[eid];data=envelope['response']['data'];site=data['site']
                independent=any(s['key']!='nswev' for s in data.get('sources',[]))
                distance=distance_m(float(row.latitude),float(row.longitude),float(site['lat']),float(site['lng']))
                labels=[site.get('operator',''),site.get('network',''),site.get('network_name','')]
                # Explicit operator-owned provenance is useful when directory network is unbranded.
                provider_operators={'ampol':'ampol','bppulse':'bp','evie':'evie','tesla':'tesla'}
                labels += [provider_operators[s['key']] for s in data.get('sources',[]) if s['key'] in provider_operators]
                op_ok=canonical(row.operator_name) in {canonical(x) for x in labels if x}
                address_ok,address_rule=address_evidence(row.station_address,site['address'])
                p=re.search(r'\b(\d{4})\s*(?:Australia)?\s*$',site['address'],re.I)
                post=p.group(1) if p else ''
                postcode_ok=not post or post==row.postcode
                resolved_postcode = reconcile_postcode(row, site, data, distance, address_rule)
                if resolved_postcode:
                    postcode_ok = True
                # A connector standard or substantive pricing/access text is genuinely new.
                standards=[x for x in site.get('standards',[]) if x not in ('other','unknown')]
                cost=site.get('cost',{})
                novel=bool(standards or cost.get('text') or site.get('access_text') or cost.get('kind') in ('paid','free'))
                dc_evidence=any(str(x.get('current','')).lower()=='dc' for x in data.get('connectors',[])) or float(site.get('max_kw') or 0)>22
                threshold=250 if address_rule=='street_and_number' and post and post==row.postcode else 100
                if address_rule=='street_and_number_one_character_difference':
                    threshold=30
                    postcode_ok=bool(post) and post==row.postcode
                conflict_ok = 'postcode_address_conflict' not in row.quality_flags or resolved_postcode
                ok=independent and novel and dc_evidence and op_ok and postcode_ok and address_ok and distance<=threshold and conflict_ok
                reasons=[]
                for condition,reason in [(independent,'TfNSW_only'),(novel,'no_substantive_new_attribute'),(dc_evidence,'DC_not_supported'),(op_ok,'operator'),(postcode_ok,'postcode'),(address_ok,address_rule),(distance<=threshold,'distance_over_threshold'),(conflict_ok,'source_postcode_conflict')]:
                    if not condition: reasons.append(reason)
                evidence.append(dict(charger_id=cid,source='ChargeAlong',external_id=eid,distance_m=distance,
                    operator_match=op_ok,address_rule=address_rule,postcode_match=postcode_ok,independent_source=independent,
                    eligible=ok,reason=('accepted_postcode_reconciled_operator_locality_30m' if resolved_postcode else 'accepted_candidate') if ok else ';'.join(reasons),source_address=row.station_address,external_address=site['address']))
                if ok: eligible.append((distance,eid,data,envelope['retrieved_at_utc']))
            if eligible:
                eligible.sort(key=lambda x:(x[0],x[1]))
                distance,eid,data,when=eligible[0]
                selected=('ChargeAlong',eid,data,distance,when,'Cached nearby candidates + detail API: independent source, new attribute, operator/street/number/postcode; <=100 m or <=250 m with house-number and postcode agreement; nearest eligible')
                selected_rule = address_evidence(row.station_address, data['site']['address'])[1]
                if reconcile_postcode(row, data['site'], data, distance, selected_rule):
                    selected = (*selected[:5], selected[5] + '; source postcode conflict reconciled for matching only: operator-backed, same locality, numbered street and address postcode, <=30 m; raw postcode retained')
        if selected:
            source,eid,record,distance,when,method=selected
            if source=='Open Charge Map':
                url='https://openchargemap.org/site/poi/details/'+eid
                connectors=record.get('Connections',[])
                standards=sorted({x.get('ConnectionType',{}).get('Title') for x in connectors if x.get('ConnectionType',{}).get('Title')})
                add_attr(cid,'plug_types',standards,None,source,eid,url,when)
                add_attr(cid,'pricing',record.get('UsageCost'),None,source,eid,url,when,'Historical source text; not a current tariff quote.')
                add_attr(cid,'access_type',record.get('UsageType',{}).get('Title'),None,source,eid,url,when)
                add_attr(cid,'status',record.get('StatusType',{}).get('Title'),None,source,eid,url,when,'Source observation, not live availability.')
                add_attr(cid,'external_number_of_points',record.get('NumberOfPoints'),'points',source,eid,url,when,'Not verified charging bays.')
                power=[float(x['PowerKW']) for x in connectors if x.get('PowerKW')]
                add_attr(cid,'external_max_power_kw',max(power) if power else None,'kW',source,eid,url,when,'Corroborative, excluded from new-attribute coverage.')
                provider=record.get('DataProvider',{})
                provenance.append(dict(charger_id=cid,source_key='ocm',provider=provider.get('Title','Open Charge Map'),external_id=eid,licence=provider.get('License','See source record'),source_url=url))
            else:
                site=record['site'];url='https://chargealong.io'+site['path']
                add_attr(cid,'plug_types',[x for x in site.get('standards',[]) if x not in ('other','unknown')],None,source,eid,url,when)
                cost=site.get('cost',{})
                if cost.get('text') or cost.get('kind') in ('paid','free'):
                    add_attr(cid,'pricing',cost,None,source,eid,url,when,'Preserved price object including conditions; not a live quote.')
                add_attr(cid,'access_text',site.get('access_text'),None,source,eid,url,when)
                add_attr(cid,'access_type',site.get('usage'),None,source,eid,url,when)
                add_attr(cid,'status',site.get('status'),None,source,eid,url,when,'Secondary directory status; excluded as sole coverage evidence.')
                add_attr(cid,'external_plug_count',site.get('plugs'),'plugs',source,eid,url,when,'Not charging bays; excluded from new-attribute coverage.')
                add_attr(cid,'external_max_power_kw',site.get('max_kw'),'kW',source,eid,url,when,'Excluded from new-attribute coverage.')
                for p in record['sources']:
                    provenance.append(dict(charger_id=cid,source_key=p['key'],provider=p['provider'],external_id=str(p['external_id']),licence=p.get('licence','See source'),source_url='https://api.chargealong.io/v1/sites/'+eid))
            matches.append(dict(charger_id=cid,supplied_location_id=row.location_id,match_status='matched',source_name=source,external_id=eid,
                source_url=url,retrieved_at_utc=when,confidence=None,match_distance_m=distance,match_method=method,failure_reason=None,cache_record_verified=True))
        else:
            matches.append(dict(charger_id=cid,supplied_location_id=row.location_id,match_status='needs_review' if candidates.get(cid) or ocm.get(cid) else 'unmatched',
                source_name=None,external_id=None,source_url=None,retrieved_at_utc=None,confidence=None,match_distance_m=None,
                match_method='Strict cache replay',failure_reason='No candidate passed all evidence and novelty checks',cache_record_verified=False))
        final=matches[-1]
        changes.append(dict(charger_id=cid,location_id=row.location_id,original_status=prior.final_selection_status,original_source=prior.final_source,
            final_status=final['match_status'],final_source=final['source_name'],original_external_id=prior.external_id,final_external_id=final['external_id']))
    return matches,attributes,evidence,provenance,changes
