-- USYD CODE CITATION ACKNOWLEDGEMENT
-- Generated with OpenAI Codex assistance; team review required.
-- Run after INSTALL spatial; LOAD spatial; in a new DuckDB database.
CREATE TABLE source_dataset (
    dataset_id VARCHAR PRIMARY KEY, title VARCHAR NOT NULL, source_url VARCHAR NOT NULL,
    source_version VARCHAR, retrieved_at_utc TIMESTAMPTZ, sha256 VARCHAR
);
CREATE TABLE region (
    sa4_code VARCHAR PRIMARY KEY, sa4_name VARCHAR NOT NULL,
    state_code VARCHAR NOT NULL, area_sqkm DOUBLE, boundary_year INTEGER NOT NULL,
    geometry_crs VARCHAR NOT NULL, geom GEOMETRY
);
CREATE TABLE operator (
    operator_id VARCHAR PRIMARY KEY, operator_name VARCHAR NOT NULL UNIQUE
);
CREATE TABLE location (
    location_id VARCHAR PRIMARY KEY, station_address VARCHAR NOT NULL, postcode VARCHAR,
    latitude DOUBLE CHECK (latitude BETWEEN -90 AND 90),
    longitude DOUBLE CHECK (longitude BETWEEN -180 AND 180),
    sa4_code VARCHAR REFERENCES region(sa4_code),
    spatial_method VARCHAR NOT NULL, spatial_distance_m DOUBLE,
    geometry_crs VARCHAR NOT NULL, geom GEOMETRY
);
CREATE TABLE charger (
    charger_id VARCHAR PRIMARY KEY, location_id VARCHAR NOT NULL REFERENCES location(location_id),
    operator_id VARCHAR NOT NULL REFERENCES operator(operator_id),
    source_dataset_id VARCHAR NOT NULL REFERENCES source_dataset(dataset_id),
    source_row INTEGER NOT NULL UNIQUE, source_object_id VARCHAR, station_name VARCHAR,
    operator_raw VARCHAR NOT NULL, charger_type VARCHAR NOT NULL CHECK (charger_type IN ('AC','DC','Upcoming')),
    number_of_plugs INTEGER CHECK (number_of_plugs >= 0),
    rating_raw VARCHAR, max_rating_kw DOUBLE CHECK (max_rating_kw > 0),
    lga_raw VARCHAR, source_label VARCHAR, quality_flags VARCHAR
);
CREATE TABLE augmentation_match (
    charger_id VARCHAR PRIMARY KEY REFERENCES charger(charger_id),
    supplied_location_id VARCHAR NOT NULL, match_status VARCHAR NOT NULL,
    source_name VARCHAR, external_id VARCHAR, source_url VARCHAR,
    retrieved_at_utc TIMESTAMPTZ, confidence DOUBLE CHECK (confidence BETWEEN 0 AND 1),
    match_distance_m DOUBLE, match_method VARCHAR, failure_reason VARCHAR,
    cache_record_verified BOOLEAN NOT NULL
);
CREATE TABLE augmentation_attribute (
    attribute_id VARCHAR PRIMARY KEY,
    charger_id VARCHAR NOT NULL REFERENCES augmentation_match(charger_id),
    attribute_name VARCHAR NOT NULL, attribute_value VARCHAR NOT NULL,
    attribute_unit VARCHAR, original_attribute_name VARCHAR NOT NULL,
    source_name VARCHAR NOT NULL, external_id VARCHAR NOT NULL, source_url VARCHAR NOT NULL,
    retrieved_at_utc TIMESTAMPTZ, notes VARCHAR,
    UNIQUE(charger_id, attribute_name, source_name)
);
CREATE TABLE quality_issue (
    issue_id VARCHAR PRIMARY KEY, charger_id VARCHAR REFERENCES charger(charger_id),
    issue_type VARCHAR NOT NULL, detail VARCHAR NOT NULL
);
CREATE TABLE external_provenance (
    charger_id VARCHAR NOT NULL REFERENCES augmentation_match(charger_id),
    source_key VARCHAR NOT NULL, provider VARCHAR NOT NULL,
    external_id VARCHAR NOT NULL, licence VARCHAR, source_url VARCHAR NOT NULL,
    PRIMARY KEY(charger_id, source_key, external_id)
);
CREATE VIEW charger_analysis AS
SELECT c.*, o.operator_name, l.station_address, l.postcode, l.latitude, l.longitude,
       l.sa4_code, r.sa4_name, l.spatial_method, l.geom
FROM charger c JOIN operator o USING(operator_id)
JOIN location l USING(location_id) LEFT JOIN region r USING(sa4_code);
CREATE VIEW qualifying_augmentation AS
SELECT a.* FROM augmentation_attribute a JOIN augmentation_match m USING(charger_id)
WHERE m.match_status='matched' AND m.cache_record_verified
AND lower(trim(a.attribute_value)) NOT IN ('unknown','[]','','none','null')
AND (a.attribute_name IN ('plug_types','pricing','access_text')
     OR (a.source_name='Open Charge Map' AND a.attribute_name='access_type'));
CREATE VIEW dc_augmentation_coverage AS
SELECT count(DISTINCT c.charger_id) AS total_dc_records,
       count(DISTINCT a.charger_id) AS augmented_records,
       count(DISTINCT a.charger_id)::DOUBLE / nullif(count(DISTINCT c.charger_id),0) AS coverage,
       count(DISTINCT c.location_id) AS total_dc_locations,
       count(DISTINCT CASE WHEN a.charger_id IS NOT NULL THEN c.location_id END) AS augmented_locations,
       count(DISTINCT CASE WHEN a.charger_id IS NOT NULL THEN c.location_id END)::DOUBLE
         / nullif(count(DISTINCT c.location_id),0) AS location_coverage
FROM charger c LEFT JOIN qualifying_augmentation a USING(charger_id)
WHERE c.charger_type='DC';
