# Quiz 2 source-to-site coverage audit

Quiz 2 scope was stated in the Week 10 lecture as all material covered since Quiz 1, i.e. Weeks 7-10. The lecturer also stated that some questions would use the complexity of former exam multiple-choice questions. The website therefore covers lecture concepts, tutorial code recognition, and comparison/trap questions.

## Week 7 - Temporal Data (40 slide pages)

- Slides 2-7 -> W7-01: ubiquity, historical data, temporal DBMS responsibilities.
- Slides 8-10 -> W7-02: instant, interval, period, DATE/TIME/TIMESTAMP and half-open boundaries.
- Slides 11-14 -> W7-03/W7-04: user-defined, valid and transaction time; temporal and bitemporal tables.
- Slides 15-16 -> W7-04: NOW/UC encodings; current, sequenced and nonsequenced queries.
- Slides 18-24 -> W7-05: conventional SQL limits, semi-temporal history and SQL:2011 PERIOD FOR.
- Slides 25-30 -> W7-05/W7-07: temporal aggregation, PostgreSQL ranges, GiST and range operations.
- Slides 32-40 -> W7-06 to W7-12: point/sequence representation, arrays, SQL tutorial operations and JSON anti-pattern.
- Week 8 tutorial notebook -> W7-07 to W7-12: EXTRACT, CTE, array_agg, UNNEST, LATERAL, cardinality, array_append and visualisation.

## Week 8 - Unstructured Data (59 slide pages)

- Slides 2-14 -> W8-01/W8-03/W8-08: structured vs unstructured, text/image data, RGB/gray/binary, classical and deep features.
- Slides 15-21 -> W8-02: supervised/unsupervised tasks and complete ML pipeline.
- Slides 22-36 -> W8-04 to W8-07: tokenisation, vector space, CountVectorizer parameters, TF-IDF, similarity, Word2Vec, BERT and GPT.
- Slides 37-44 -> W8-08: image preprocessing, descriptors/NN features, similarity search and analysis outcomes.
- Slides 45-50 -> W8-09: EXIF/IPTC/XMP, evidence limits and ExifTool commands.
- Slides 51-59 -> W8-10: interaction/polynomial, lag/rolling, domain features, categorical encoding, hashing, feature selection and AutoML.
- Week 8 tutorial notebook -> W8-11 plus cross-links to W7 code lessons.

## Week 9 - Stream Data Processing (51 slide pages)

- Slides 2-9 -> W9-01/W9-02: motivation, stream properties, DBMS vs DSMS and two-layer architecture.
- Slides 10-22 -> W9-03 to W9-06: Pub/Sub, MQTT topics/wildcards/retain/QoS, Kafka partitions, groups, ordering, replication and replay.
- Slides 23-32 -> W9-07/W9-08: stateful/stateless and all window classes including tuple-count, punctuation/session and agglomerative windows.
- Slides 33-36 -> W9-09/W9-10: event/ingestion/processing time, watermark and late-event handling.
- Slides 37-40 -> W9-11: table-table, stream-table and stream-stream joins.
- Slides 41-51 -> W9-12: Spark Streaming micro-batches/DStream, Flink pipelining and platform comparison.
- Tutorial notebook and MQTT scripts -> W9-04/W9-05/W9-12: callbacks, JSON decoding, plot window, publisher and subscriber.

## Week 10 - Scalable Data Engineering (65 slide pages)

- Slides 2-9 -> W10-01/W10-02: scale-up/out, speed-up, scalability goal, throughput, latency, elasticity and design principles.
- Slides 10-17 -> W10-02/W10-03: indexing, RAID/cache, row/column storage, Parquet and wide-column stores.
- Slides 18-21 -> W10-04: horizontal/vertical, round-robin/hash/range and parallelism.
- Slides 22-29 -> W10-05/W10-06: eager/lazy, single/multi-leader, MongoDB sharding and stale replicas.
- Slides 30-35 -> W10-07: strong consistency, availability and CAP scenarios.
- Slides 36-44 -> W10-08/W10-09: analytics stack, HDFS read path, Hadoop/YARN/Hive and frameworks.
- Slides 45-57 -> W10-09 to W10-11/W10-13: MapReduce, RDD, Spark stack, DataFrame API, lazy execution, Catalyst/CBO/AQE, Spark SQL and notebook setup.
- Slides 58-65 -> W10-12: Flink APIs, pipelining, lazy execution and Spark comparison.
- Week 10 tutorial and validated outputs -> W10-10/W10-11/W10-13: runnable PySpark SQL, time conversion, aligned arrays, actions and plotting.

## Automated completeness checks

- 48 lessons and 66 interactive quiz boxes.
- Every quiz box contains exactly one correct option and an explanation.
- 47 lessons have the common concept-foundation layer; the first lesson has a dedicated deeper rewrite.
- 27 lessons additionally contain source-gap full-coverage sections.
- No pre-question answer bridge remains.

## Excluded material

Runtime/JDK files, credentials, virtual environments, duplicated archives and browser logs are operational artefacts, not examinable concepts. Videos are represented through the matching lecture transcripts and slide decks.
