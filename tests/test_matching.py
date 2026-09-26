"""Focused regressions for false matches and rating semantics.

USYD CODE CITATION ACKNOWLEDGEMENT: generated with OpenAI Codex assistance.
"""
import sys
from pathlib import Path
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from augment import address_evidence,canonical,reconcile_postcode
from types import SimpleNamespace
from build import power,distance_m

class MatchingTests(unittest.TestCase):
    def test_postcode_reconciliation_requires_all_independent_signals(self):
        row=SimpleNamespace(station_address='221 Wolseley St, Jamisontown NSW 2750',operator_name='Evie Networks',quality_flags='postcode_address_conflict')
        site={'address':'221 Wolseley Street, Jamisontown New South Wales 2750'}
        data={'locality':{'name':'Jamisontown'},'sources':[{'key':'evie'}]}
        self.assertTrue(reconcile_postcode(row,site,data,13.5,'street_and_number'))
        self.assertFalse(reconcile_postcode(row,site,data,31,'street_and_number'))
        self.assertFalse(reconcile_postcode(row,site,data,13.5,'house_number_conflict'))
        self.assertFalse(reconcile_postcode(row,site,{'locality':{'name':'Jamisontown'},'sources':[{'key':'nswev'}]},13.5,'street_and_number'))
        self.assertFalse(reconcile_postcode(row,{'address':'221 Wolseley Street, Jamisontown NSW 2751'},data,13.5,'street_and_number'))
    def test_coverage_counts_records_once_and_keeps_unmatched_denominator(self):
        import duckdb
        con=duckdb.connect()
        con.execute("CREATE TABLE charger(charger_id VARCHAR,location_id VARCHAR,charger_type VARCHAR); INSERT INTO charger VALUES ('a','shared','DC'),('b','shared','DC'),('c','third','DC')")
        con.execute("CREATE TABLE qualifying_augmentation(charger_id VARCHAR); INSERT INTO qualifying_augmentation VALUES ('a'),('a')")
        ddl=(Path(__file__).resolve().parents[1]/'sql/schema.sql').read_text()
        con.execute(ddl[ddl.index('CREATE VIEW dc_augmentation_coverage AS'):].split(';')[0])
        self.assertEqual(con.execute('SELECT total_dc_records,augmented_records,total_dc_locations FROM dc_augmentation_coverage').fetchone(),(3,1,2))
        self.assertAlmostEqual(con.execute('SELECT coverage FROM dc_augmentation_coverage').fetchone()[0],1/3)
        con.close()
    def test_conflicting_house_numbers_rejected(self):
        self.assertFalse(address_evidence('7 Bungan St, Sydney 2103','2 Bungan Street, Mona Vale 2103')[0])
    def test_abbreviations_and_ranges(self):
        self.assertTrue(address_evidence('1985 Camden Valley Way, Prestons 2170','1975/1985 Camden Valley Wy, Prestons NSW 2170')[0])
    def test_typo_is_separate_evidence_class(self):
        self.assertEqual(address_evidence('60-62 Amherst St, Cammeray 2062','60-62 Amhurst Street, Cammeray NSW 2062')[1],'street_and_number_one_character_difference')
    def test_operator_alias_does_not_conflate_competitors(self):
        self.assertEqual(canonical('Ampol AmpCharge'),canonical('Ampol'))
        self.assertNotEqual(canonical('Chargefox'),canonical('Evie'))
    def test_composite_power_not_station_total(self):
        self.assertEqual(power('2x350kW & 6x175kW'),(350.0,'compound'))
        self.assertEqual(power('AC'),(None,'unknown'))
    def test_distance_in_metres(self):
        self.assertEqual(distance_m(-33,151,-33,151),0)
        self.assertAlmostEqual(distance_m(0,0,0,1),111195.08,places=1)

if __name__=='__main__': unittest.main()
