"""Build an auditable, complete DuckDB database from official data and B/C snapshots.

USYD CODE CITATION ACKNOWLEDGEMENT
Generated with OpenAI Codex assistance. The team must review and understand this code.
The original B/C programs were not supplied; their delivered files remain immutable inputs.
"""
import ast
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import duckdb
import pandas as pd
from acquire import ROOT, acquire

def ident(prefix, *values):
    return prefix + '_' + hashlib.sha256(json.dumps(values, ensure_ascii=False).encode()).hexdigest()[:24]

def clean(value):
    return re.sub(r'\s+', ' ', str(value).replace('\\n', ' ')).strip()

def nullable(value):
    return str(value).strip() or None

def read_csv(path):
    return pd.read_csv(path, dtype=str, keep_default_na=False)

def external_id(value):
    return re.sub(r'\.0$', '', str(value))

def distance_m(lat1, lon1, lat2, lon2):
    a, b = math.radians(lat1), math.radians(lat2)
    h = math.sin((b-a)/2)**2 + math.cos(a)*math.cos(b)*math.sin(math.radians(lon2-lon1)/2)**2
    return 6371008.8 * 2 * math.asin(min(1,math.sqrt(h)))

def power(text):
    """Maximum per-unit rating, never multiply a quantity into a kW figure."""
    text = clean(text)
    values = re.findall(r'(\d+(?:\.\d+)?)\s*kW', text, flags=re.I)
    if values:
        return max(map(float, values)), 'compound' if len(values)>1 else 'single'
    if re.fullmatch(r'\d+(?:\.\d+)?', text):
        return float(text), 'unit_assumed_kw'
    return None, 'unknown'

def put(con, table, records):
    if not records:
        return
    frame = pd.DataFrame(records)
    con.register('_stage', frame)
    cols = ','.join('"'+c+'"' for c in frame.columns)
    con.execute(f'INSERT INTO {table} ({cols}) SELECT {cols} FROM _stage')
    con.unregister('_stage')

def build(refresh=False, output=None):
    rawdir = acquire(refresh)
    processed = ROOT / 'data/processed'
    processed.mkdir(exist_ok=True)
    database = Path(output) if output else ROOT / 'output/ev_chargers.duckdb'
    database.parent.mkdir(parents=True, exist_ok=True)
    # Build a new sibling first; an unsuccessful build never destroys a prior database.
    staged = database.with_suffix('.building.duckdb')
    if staged.exists():
        staged.unlink()
    con = duckdb.connect(str(staged))
    con.execute('INSTALL spatial; LOAD spatial;')
    con.execute((ROOT/'sql/schema.sql').read_text())
    manifest = json.loads((rawdir/'retrieval_manifest.json').read_text())
    datasets = []
    for file, key, title, version in [('ev_20251216.csv','tfnsw','TfNSW EV charging locations','2025-12-16'),('SA4_2026_AUST_SHP_GDA2020.zip','abs','ABS SA4 boundaries','ASGS Edition 4 2026')]:
        m = manifest[file]
        datasets.append(dict(dataset_id=key,title=title,source_url=m['url'],source_version=version,retrieved_at_utc=m['retrieved_at_utc'],sha256=m['sha256']))
    put(con,'source_dataset',datasets)
    shp = str(rawdir/'sa4/SA4_2026_AUST_GDA2020.shp').replace("'", "''")
    con.execute(f"INSERT INTO region SELECT SA4_CODE26,SA4_NAME26,STE_CODE26,AREASQKM26,2026,'EPSG:7844',geom FROM ST_Read('{shp}') WHERE STE_CODE26='1'")
    raw = read_csv(rawdir/'ev_20251216.csv')
    b = read_csv(ROOT/'data/b_handoff/data/dc_chargers.csv')
    c = read_csv(ROOT/'data/handoff/combined_augmentation_results.csv')
    assert b.charger_id.is_unique and c.charger_id.is_unique
    assert set(b.charger_id)==set(c.charger_id)
    b_by_row = {}
    for _, row in b.iterrows():
        numbers = json.loads(row.source_row_numbers)
        assert len(numbers)==1, 'A source merge needs explicit reconciliation'
        number = numbers[0]
        original = raw.iloc[number-1]
        for column in raw.columns:
            assert original[column] == row['raw_'+column], (number, column)
        b_by_row[number] = row
    assert len(b_by_row)==sum(raw.Charger_Type=='DC')
    issues, chargers, locations, operators = [], [], {}, {}
    cleaned = []
    for number, (_, row) in enumerate(raw.iterrows(),1):
        inherited = b_by_row.get(number)
        flags = []
        if inherited is not None:
            cid, lid, oid = inherited.charger_id, inherited.location_id, inherited.operator_id
            address, opname, postcode = inherited.station_address, inherited.operator_name, inherited.postcode
            flags = inherited.quality_flags.split(';') if inherited.quality_flags else []
        else:
            cid = ident('chg',number, row.to_dict())
            address = clean(row.Station_address)
            opname = clean(row.Operator)
            if opname.lower()=='non-networked': opname='Non-networked'
            # Preserve uncertain corporate aliases instead of conflating service/network identities.
            oid = ident('op',opname)
            known = b[b.operator_name==opname]
            if len(known): oid=known.iloc[0].operator_id
            postcode = re.sub(r'\.0$','',clean(row.PCODE))
            found = re.search(r'\b(\d{4})\s*(?:Australia)?\s*$',address,re.I)
            address_postcode = found.group(1) if found else ''
            if not postcode and address_postcode:
                postcode=address_postcode; flags.append('postcode_from_address')
            elif postcode and address_postcode and postcode!=address_postcode:
                flags.append('postcode_address_conflict')
            if not row.OBJECTID: flags.append('missing_source_id')
            if not row.Station_name: flags.append('missing_station_name')
            if not row.LGANAME: flags.append('missing_lga')
            if not row.Source: flags.append('missing_source_label')
            lid = ident('loc',address.lower(),float(row.Latitude),float(row.Longitude))
        rating, status = power(row.Charger_rating)
        if status=='unknown': flags.append('unknown_power')
        if status=='unit_assumed_kw' and 'rating_unit_assumed' not in flags: flags.append('rating_unit_assumed')
        lat,lon=float(row.Latitude),float(row.Longitude)
        if not (-90<=lat<=90 and -180<=lon<=180): raise ValueError(f'Invalid coordinate at source row {number}')
        loc=dict(location_id=lid,station_address=address,postcode=nullable(postcode),latitude=lat,longitude=lon)
        if lid in locations: assert locations[lid]==loc, 'Location identity is inconsistent'
        locations[lid]=loc
        operators[oid]=dict(operator_id=oid,operator_name=opname)
        charger=dict(charger_id=cid,location_id=lid,operator_id=oid,source_dataset_id='tfnsw',source_row=number,
            source_object_id=nullable(row.OBJECTID),station_name=nullable(clean(row.Station_name)),operator_raw=row.Operator,
            charger_type=row.Charger_Type,number_of_plugs=int(row.Number_of_plugs),rating_raw=row.Charger_rating,
            max_rating_kw=rating,lga_raw=nullable(row.LGANAME),source_label=nullable(row.Source),quality_flags=';'.join(sorted(set(flags))))
        chargers.append(charger)
        cleaned.append({**charger,**loc,'operator_name':opname})
        for flag in sorted(set(flags)):
            issues.append(dict(issue_id=ident('issue',cid,flag),charger_id=cid,issue_type=flag,detail='Source quality flag; original values retained in raw CSV and handoff'))
    # Point in polygon, explicitly transforming longitude/latitude in WGS84 to GDA2020.
    loc_frame=pd.DataFrame(locations.values());con.register('_locations',loc_frame)
    con.execute("CREATE TEMP TABLE points AS SELECT *, ST_Transform(ST_Point(longitude,latitude),'EPSG:4326','EPSG:7844',always_xy:=true) AS geom FROM _locations")
    counts=con.execute('SELECT location_id,count(r.sa4_code) FROM points p LEFT JOIN region r ON ST_Covers(r.geom,p.geom) GROUP BY location_id HAVING count(r.sa4_code)>1').fetchall()
    assert not counts, f'Ambiguous polygon matches: {counts}'
    con.execute("INSERT INTO location SELECT p.location_id,p.station_address,p.postcode,p.latitude,p.longitude,r.sa4_code,CASE WHEN r.sa4_code IS NULL THEN 'unmatched' ELSE 'covers' END,CASE WHEN r.sa4_code IS NULL THEN NULL ELSE 0 END,'EPSG:7844',p.geom FROM points p LEFT JOIN region r ON ST_Covers(r.geom,p.geom)")
    # Only a <=10 m coastal tolerance; do not snap distant or invalid coordinates into NSW.
    unmatched=con.execute("SELECT location_id FROM location WHERE sa4_code IS NULL").fetchall()
    for (lid,) in unmatched:
        nearest=con.execute("SELECT r.sa4_code, ST_Distance(ST_Transform(r.geom,'EPSG:7844','EPSG:7856',always_xy:=true),ST_Transform(l.geom,'EPSG:7844','EPSG:7856',always_xy:=true)) d FROM region r,location l WHERE l.location_id=? AND r.geom IS NOT NULL ORDER BY d LIMIT 1",[lid]).fetchone()
        if nearest and nearest[1]<=10:
            con.execute("UPDATE location SET sa4_code=?,spatial_method='nearest_boundary_within_10m',spatial_distance_m=? WHERE location_id=?",[nearest[0],nearest[1],lid])
        for item in chargers:
            if item['location_id']==lid:
                issues.append(dict(issue_id=ident('issue',item['charger_id'],'coastal_point'),charger_id=item['charger_id'],issue_type='coastal_point',detail=f'No polygon covers point; nearest boundary {nearest}; 10 m tolerance applied only if eligible'))
    put(con,'operator',list(operators.values()));put(con,'charger',chargers)
    con.unregister('_locations')
    from augment import rebuild
    matches,attributes,cache_checks,provenance,transformations=rebuild(b,c,ident,distance_m)
    put(con,'augmentation_match',matches)
    put(con,'augmentation_attribute',attributes)
    put(con,'external_provenance',provenance)
    put(con,'quality_issue',issues)
    comparison=con.execute('SELECT c.charger_id,l.sa4_code,l.spatial_method FROM charger c JOIN location l USING(location_id) WHERE charger_type=\'DC\'').fetchdf().merge(b[['charger_id','sa4_code','sa4_name']],on='charger_id',suffixes=('_2026','_2021'))
    comparison.to_csv(processed/'sa4_version_comparison.csv',index=False)
    pd.DataFrame(cache_checks).to_csv(processed/'candidate_evidence.csv',index=False)
    pd.DataFrame(transformations).to_csv(processed/'match_changes.csv',index=False)
    con.execute('SELECT * FROM charger_analysis ORDER BY source_row').fetchdf().drop(columns=['geom']).to_csv(processed/'chargers.csv',index=False)
    con.execute('SELECT * FROM augmentation_attribute ORDER BY charger_id,attribute_name').fetchdf().to_csv(processed/'augmentation_attributes.csv',index=False)
    con.execute('SELECT * FROM quality_issue').fetchdf().to_csv(processed/'quality_issues.csv',index=False)
    totals={t:con.execute(f'SELECT count(*) FROM {t}').fetchone()[0] for t in ['source_dataset','region','operator','location','charger','augmentation_match','augmentation_attribute','external_provenance','quality_issue']}
    coverage=con.execute('SELECT * FROM dc_augmentation_coverage').fetchdf().to_dict('records')[0]
    summary=dict(built_at_utc=datetime.now(timezone.utc).isoformat(),duckdb_version=duckdb.__version__,tables=totals,
        raw_rows=len(raw),raw_exact_duplicate_rows=int(raw.duplicated().sum()),charger_types=dict(Counter(raw.Charger_Type)),
        missing_raw={col:int((raw[col]=='').sum()) for col in raw.columns},coverage=coverage,
        spatial_methods=con.execute('SELECT spatial_method,count(*) records FROM charger_analysis GROUP BY spatial_method').fetchdf().to_dict('records'),
        sa4_changed_dc_records=int((comparison.sa4_code_2026!=comparison.sa4_code_2021).sum()),
        matching_statuses=dict(Counter(m['match_status'] for m in matches)),attribute_counts=con.execute('SELECT source_name,attribute_name,count(*) n FROM augmentation_attribute GROUP BY ALL ORDER BY 1,2').fetchdf().to_dict('records'),
        original_c_augmented_locations=int(c.loc[c.final_selection_status=='accepted','location_id'].nunique()),
        matched_by_source=dict(Counter(m['source_name'] for m in matches if m['match_status']=='matched')),
        cache_verified_matches=sum(m['cache_record_verified'] for m in matches),
        detail_cache_files=len(list((ROOT/'data/external/chargealong_sites').glob('*.json'))),
        candidate_evidence_rows=len(cache_checks))
    (processed/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    con.execute('CHECKPOINT');con.close()
    staged.replace(database)
    print(json.dumps(summary,indent=2))
    return database

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--refresh',action='store_true',help='Redownload official TfNSW and ABS files')
    parser.add_argument('--output',help='Alternative database path')
    args=parser.parse_args();build(args.refresh,args.output)
