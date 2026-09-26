# NSW EV Charger Data Integration and DuckDB Validation

Course data-engineering project that integrates the NSW Transport for NSW EV-charger release with ASGS SA4 boundaries and auditable external attributes. This public package contains reproducible source code, SQL, tests and non-sensitive validation summaries only. It deliberately excludes raw data, cached third-party responses, course handoffs, reports and generated databases.

## Verified snapshot

- 1,958 source records: 1,427 AC, 433 DC and 98 Upcoming.
- 1,957 records use polygon spatial assignment; one coastal record uses a documented 1.765 m nearest-boundary fallback within the project tolerance.
- The local checked build defines nine database tables and three views.
- Validation checked source retention, key uniqueness, spatial assignment, provenance and coverage.

## Candidate role and AI boundary

Wanyi Feng handled final integration and result checking. The project used substantial AI assistance for implementation and writing; this package does not claim independent implementation.

## Reproduce

1. Create a Python 3.11+ environment and run `pip install -r requirements.txt`.
2. Obtain the current official TfNSW charger release and ASGS boundary files under `data/raw/` as described by `src/acquire.py`.
3. Run `python src/build.py`, `python src/validate.py`, then `python -m unittest discover -s tests -v`.

The included `evidence/summary.json` and `evidence/validation.json` are the checked local snapshot. See source comments and SQL for required inputs.

## Public-data and privacy boundary

No personal contact details, student identifiers, API keys, raw/course handoff files, cached external responses, or generated databases are included. Check the upstream source licences before redistributing reconstructed data.
