"""Check research artifacts and document links without claiming product validation."""
import hashlib, json, pathlib, re, xml.etree.ElementTree as ET

base = pathlib.Path(__file__).resolve().parent.parent
issues = []
documents = [base / 'README.md', *sorted((base / 'docs').glob('*.md'))]
for file in documents:
    text = file.read_text(encoding='utf-8')
    for target in re.findall(r'\]\(([^)]+)\)', text):
        if target.startswith(('http:', 'https:', '#')):
            continue
        if not (file.parent / target.split('#')[0]).exists():
            issues.append(f'{file.name}: missing link {target}')
sources = []
for evidence in sorted((base / 'research/snapshots').glob('*/evidence.json')):
    d = json.loads(evidence.read_text(encoding='utf-8'))
    sources.append({'repo': d['repo'], 'sha': d['commit']['sha']})
asr = []
for file in sorted((base / 'research/results').glob('*-asr.json')):
    d = json.loads(file.read_text(encoding='utf-8'))
    transcript = d.get('transcript', {})
    words = transcript.get('words') or [w for segment in transcript.get('segments', []) for w in segment.get('words', [])]
    asr.append({'candidate': d['candidate'], 'status': d['status'], 'seconds': d['wall_seconds'], 'words': len(words), 'sample_hash': d['sample_sha256'], 'error': d.get('error')})
tests = []
for file in sorted((base / 'research/results').glob('*-tests.xml')):
    xml = ET.parse(file)
    suites = xml.findall('.//testsuite')
    tests.append({'file': file.name, 'tests': sum(int(s.attrib.get('tests', 0)) for s in suites), 'failures': sum(int(s.attrib.get('failures', 0)) for s in suites), 'errors': sum(int(s.attrib.get('errors', 0)) for s in suites), 'skipped': sum(int(s.attrib.get('skipped', 0)) for s in suites)})
media = base / 'research/media/z0cf-eWBVCo.mp4'
manifest = json.loads((base / 'research/results/media-manifest.json').read_text(encoding='utf-8'))
if hashlib.file_digest(media.open('rb'), 'sha256').hexdigest() != manifest['sha256']:
    issues.append('source hash mismatch')
result = {'document_count': len(documents), 'snapshots': sources, 'asr': asr, 'tests': tests, 'source_hash_matches': 'source hash mismatch' not in issues, 'document_issues': issues, 'product_pipeline_validated': False, 'semantic_benchmark_completed': False}
(base / 'research/results/delivery-check.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result, indent=2))
raise SystemExit(1 if issues else 0)
