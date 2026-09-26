"""Retrieve the assignment's fixed official source releases without manual downloads.

USYD CODE CITATION ACKNOWLEDGEMENT
This file was generated with OpenAI Codex assistance and must be reviewed by the team.
"""
from pathlib import Path
import hashlib
import json
from datetime import datetime, timezone
from urllib.request import Request, urlopen
import zipfile

ROOT = Path(__file__).resolve().parents[1]
CATALOGUE = 'https://data.gov.au/data/api/3/action/package_show?id=nsw-2-ev-charging-locations'
ABS_PAGE = 'https://www.abs.gov.au/statistics/standards/australian-statistical-geography-standard-asgs/edition-4-july-2026-june-2031/access-and-downloads/digital-boundary-files'
ABS_URL = ABS_PAGE + '/SA4_2026_AUST_SHP_GDA2020.zip'

def fetch(url):
    with urlopen(Request(url, headers={'User-Agent': 'COMP5339-assignment-data-retrieval/1.0'}), timeout=90) as response:
        return response.read()

def acquire(refresh=False):
    raw = ROOT / 'data/raw'
    raw.mkdir(parents=True, exist_ok=True)
    metadata = raw / 'tfnsw_metadata.json'
    if refresh or not metadata.exists():
        metadata.write_bytes(fetch(CATALOGUE))
    catalogue = json.loads(metadata.read_text(encoding='utf-8'))
    resources = [r for r in catalogue['result']['resources'] if r['url'].endswith('/ev_20251216.csv')]
    if len(resources) != 1:
        raise RuntimeError('The official catalogue no longer lists the required December 2025 release.')
    manifest_path = raw / 'retrieval_manifest.json'
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {}
    for name, url in [('ev_20251216.csv', resources[0]['url']), ('SA4_2026_AUST_SHP_GDA2020.zip', ABS_URL)]:
        target = raw / name
        if refresh or not target.exists():
            body = fetch(url)
            if name.endswith('.zip') and not body.startswith(b'PK'):
                raise ValueError('ABS did not return a ZIP file')
            if name.endswith('.csv') and not body.lstrip(b'\xef\xbb\xbf').startswith(b'OBJECTID,'):
                raise ValueError('TfNSW did not return the expected CSV; check the official download access')
            target.write_bytes(body)
            manifest[name] = {'url': url, 'retrieved_at_utc': datetime.now(timezone.utc).isoformat()}
        record = manifest.setdefault(name, {'url': url, 'retrieved_at_utc': None, 'note': 'Cached file; original retrieval time not recorded by this script'})
        record.update(sha256=hashlib.sha256(target.read_bytes()).hexdigest(), bytes=target.stat().st_size)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    shpdir = raw / 'sa4'
    shpdir.mkdir(exist_ok=True)
    with zipfile.ZipFile(raw / 'SA4_2026_AUST_SHP_GDA2020.zip') as archive:
        for member in archive.infolist():
            destination = (shpdir / member.filename).resolve()
            if not destination.is_relative_to(shpdir.resolve()):
                raise ValueError('Unsafe path in boundary archive')
        archive.extractall(shpdir)
    return raw

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--refresh', action='store_true')
    acquire(parser.parse_args().refresh)
