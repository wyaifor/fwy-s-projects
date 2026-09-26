"""Independent checks of the submitted database, source preservation and match evidence.

USYD CODE CITATION ACKNOWLEDGEMENT
Generated with OpenAI Codex assistance; team review required.
"""
import argparse
from datetime import datetime,timezone
import json
from pathlib import Path
import duckdb
import pandas as pd
from acquire import ROOT

def validate(database=None):
    path=Path(database) if database else ROOT/'output/ev_chargers.duckdb'
    con=duckdb.connect(str(path),read_only=True);con.execute('LOAD spatial')
    checks=[]
    def check(name, condition, detail):
        checks.append({'check':name,'passed':bool(condition),'detail':detail})
    def scalar(sql): return con.execute(sql).fetchone()[0]
    raw=pd.read_csv(ROOT/'data/raw/ev_20251216.csv',dtype=str,keep_default_na=False)
    check('all source records retained',scalar('SELECT count(*) FROM charger')==len(raw),len(raw))
    check('DC population retained',scalar("SELECT count(*) FROM charger WHERE charger_type='DC'")==433,433)
    check('upcoming not inferred DC',scalar("SELECT count(*) FROM charger WHERE charger_type='Upcoming'")==98,98)
    for table,key in [('charger','charger_id'),('location','location_id'),('operator','operator_id'),('region','sa4_code'),('augmentation_match','charger_id'),('augmentation_attribute','attribute_id')]:
        count=scalar(f'SELECT count(*)-count(DISTINCT {key}) FROM {table}')
        check(table+' unique keys',count==0,count)
    check('all regions edition 4',scalar('SELECT count(*) FROM region WHERE boundary_year<>2026')==0,2026)
    invalid=scalar('SELECT count(*) FROM region WHERE geom IS NULL OR NOT ST_IsValid(geom)')
    check('all region geometries valid',invalid==0,invalid)
    check('every charger has NSW SA4',scalar('SELECT count(*) FROM charger_analysis WHERE sa4_code IS NULL')==0,0)
    check('polygon match geometry valid',scalar("SELECT count(*) FROM location l JOIN region r USING(sa4_code) WHERE l.spatial_method='covers' AND NOT ST_Covers(r.geom,l.geom)")==0,0)
    check('coastal exception bounded',scalar("SELECT count(*) FROM location WHERE spatial_method='nearest_boundary_within_10m' AND (spatial_distance_m>10 OR spatial_distance_m IS NULL)")==0,0)
    check('no orphan attributes',scalar('SELECT count(*) FROM augmentation_attribute a LEFT JOIN augmentation_match m USING(charger_id) WHERE m.charger_id IS NULL')==0,0)
    check('attributes only for verified matches',scalar("SELECT count(*) FROM augmentation_attribute a JOIN augmentation_match m USING(charger_id) WHERE m.match_status<>'matched' OR NOT m.cache_record_verified")==0,0)
    check('no unknown values published',scalar("SELECT count(*) FROM augmentation_attribute WHERE lower(trim(attribute_value)) IN ('unknown','[]','','none','null')")==0,0)
    check('no false bay/access semantics',scalar("SELECT count(*) FROM augmentation_attribute WHERE attribute_name='charging_bays' OR (attribute_name='access_type' AND attribute_value IN ('fast','ultra-fast','ac'))")==0,0)
    check('ChargeAlong includes non-TfNSW provenance',scalar("SELECT count(*) FROM augmentation_match m WHERE source_name='ChargeAlong' AND NOT EXISTS(SELECT 1 FROM external_provenance p WHERE p.charger_id=m.charger_id AND p.source_key<>'nswev')")==0,0)
    check('every matched record adds a substantive attribute',scalar("SELECT count(*) FROM augmentation_match m WHERE match_status='matched' AND NOT EXISTS(SELECT 1 FROM augmentation_attribute a WHERE a.charger_id=m.charger_id AND a.attribute_name IN ('plug_types','pricing','access_text'))")==0,0)
    coverage=con.execute('SELECT * FROM dc_augmentation_coverage').fetchone()
    check('coverage denominator uses all DC source records',coverage[0]==433,coverage[0])
    check('location metric reported separately',coverage[3]==431,coverage[3])
    check('50 percent augmentation target',coverage[2]>=0.5,{'numerator':coverage[1],'denominator':coverage[0],'coverage':coverage[2]})
    check('record threshold requires at least 217',coverage[1]>=217,coverage[1])
    for row in con.execute('SELECT source_row,operator_raw,rating_raw,number_of_plugs FROM charger ORDER BY source_row').fetchall():
        original=raw.iloc[row[0]-1]
        assert (row[1],row[2],row[3])==(original.Operator,original.Charger_rating,int(original.Number_of_plugs))
    check('raw operator rating and plug count preserved',True,len(raw))
    b=pd.read_csv(ROOT/'data/b_handoff/data/dc_chargers.csv',dtype=str)
    final=con.execute("SELECT charger_id,location_id,operator_id FROM charger WHERE charger_type='DC'").fetchdf()
    joined=b[['charger_id','location_id','operator_id']].merge(final,on='charger_id',suffixes=('_b','_final'),validate='one_to_one')
    check('all B and C identifiers preserved',len(joined)==433 and (joined.location_id_b==joined.location_id_final).all() and (joined.operator_id_b==joined.operator_id_final).all(),len(joined))
    # DDL must independently recreate the same table definitions and views.
    schema=duckdb.connect();schema.execute('LOAD spatial');schema.execute((ROOT/'sql/schema.sql').read_text())
    names=[r[0] for r in con.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='main' AND table_type='BASE TABLE'").fetchall()]
    for name in names:
        a=con.execute(f'DESCRIBE {name}').fetchall();bdesc=schema.execute(f'DESCRIBE {name}').fetchall()
        check('DDL matches '+name,a==bdesc,len(a))
    for name in ['charger_analysis','qualifying_augmentation','dc_augmentation_coverage']:
        check('DDL view matches '+name,con.execute(f'DESCRIBE {name}').fetchall()==schema.execute(f'DESCRIBE {name}').fetchall(),name)
    schema.close();con.close()
    result={'validated_at_utc':datetime.now(timezone.utc).isoformat(),'database':path.name,'passed':all(c['passed'] for c in checks),'checks':checks}
    (ROOT/'data/processed/validation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))
    if not result['passed']: raise SystemExit(1)
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--database');validate(p.parse_args().database)
