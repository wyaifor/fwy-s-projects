-- Open a database with the DuckDB Python connection or CLI, then LOAD spatial.
-- USYD CODE CITATION ACKNOWLEDGEMENT: generated with OpenAI Codex assistance.
LOAD spatial;

-- Count source records, not physical devices or verified operational stations.
SELECT sa4_code, sa4_name, charger_type, count(*) AS source_records
FROM charger_analysis GROUP BY ALL ORDER BY sa4_code, charger_type;

SELECT * FROM dc_augmentation_coverage;

-- The polygon and charger geometry columns use EPSG:7844.
SELECT c.charger_id,r.sa4_name
FROM charger_analysis c JOIN region r ON ST_Covers(r.geom,c.geom)
WHERE c.charger_type='DC' LIMIT 10;

-- Inspect accepted matching evidence and the added connector standards.
SELECT c.station_address,c.operator_name,m.source_name,m.match_distance_m,a.attribute_value
FROM charger_analysis c JOIN augmentation_match m USING(charger_id)
JOIN augmentation_attribute a USING(charger_id)
WHERE a.attribute_name='plug_types' ORDER BY m.match_distance_m DESC;
