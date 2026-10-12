"""Summarize source and CI inventory, without claiming test coverage."""
import json, pathlib, re

root = pathlib.Path(__file__).parent
rows = []
for folder in sorted((root / 'snapshots').iterdir()):
    evidence_path = folder / 'evidence.json'
    if not evidence_path.exists():
        continue
    e = json.loads(evidence_path.read_text(encoding='utf-8'))
    source = folder / 'source'
    files = list(source.rglob('*'))
    tests = [p for p in files if p.is_file() and (p.name.startswith('test_') or '.test.' in p.name or p.parent.name == 'tests')]
    definitions = sum(len(re.findall(r'(?m)^\s*(?:async\s+)?def test_|\btest\(', p.read_text(encoding='utf-8', errors='replace'))) for p in tests if p.suffix in ['.py', '.ts'])
    workflows = [str(p.relative_to(source)) for p in (source / '.github/workflows').glob('*')]
    runs = e.get('actions/runs?per_page=5', {})
    row = {'repo': e['repo'], 'sha': e['commit']['sha'], 'commit_date': e['commit']['commit']['committer']['date'], 'fork': e['metadata']['fork'], 'parent': e['metadata'].get('parent', {}).get('full_name'), 'archived': e['metadata']['archived'], 'test_files': len(tests), 'test_definitions_rough': definitions, 'workflows': workflows, 'releases': [{'tag': r['tag_name'], 'published_at': r['published_at']} for r in e.get('releases', [])[:3]] if isinstance(e.get('releases'), list) else e.get('releases'), 'recent_ci': [{'name': r['name'], 'sha': r['head_sha'], 'conclusion': r['conclusion'], 'url': r['html_url']} for r in runs.get('workflow_runs', [])]}
    rows.append(row)
(root / 'inventory.json').write_text(json.dumps(rows, indent=2), encoding='utf-8')
print(json.dumps(rows, indent=2))
