"""Collect read-only GitHub source snapshots; never execute upstream code."""
import concurrent.futures, datetime, io, json, pathlib, urllib.request, zipfile

ROOT = pathlib.Path(__file__).parent / 'research' / 'snapshots'
REPOS = ['Gutsken/Autoclip', 'Marsic1/openshorts', 'Steezy-code/clipper', 'jameselle/clipper', 'WyattBlue/auto-editor']

def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'autoclip-editor-research', 'Accept': 'application/vnd.github+json'})
    with urllib.request.urlopen(req, timeout=60) as response:
        return response.read()

def collect(repo):
    target = ROOT / repo.replace('/', '__')
    target.mkdir(parents=True, exist_ok=True)
    metadata = json.loads(get('https://api.github.com/repos/' + repo))
    commit = json.loads(get('https://api.github.com/repos/' + repo + '/commits/' + metadata['default_branch']))
    sha = commit['sha']
    evidence = {'fetched_at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'repo': repo, 'metadata': metadata, 'commit': commit}
    for kind in ['releases', 'actions/runs?per_page=5']:
        try:
            evidence[kind] = json.loads(get('https://api.github.com/repos/' + repo + '/' + kind))
        except Exception as exc:
            evidence[kind] = {'error': str(exc)}
    (target / 'evidence.json').write_text(json.dumps(evidence, indent=2), encoding='utf-8')
    archive = zipfile.ZipFile(io.BytesIO(get('https://codeload.github.com/' + repo + '/zip/' + sha)))
    for member in archive.infolist():
        relative = pathlib.PurePosixPath(*pathlib.PurePosixPath(member.filename).parts[1:])
        if not relative.parts or '..' in relative.parts or member.is_dir():
            continue
        dest = target / 'source' / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(archive.read(member))
    return {'repo': repo, 'sha': sha, 'date': commit['commit']['committer']['date'], 'license': metadata.get('license'), 'archived': metadata['archived'], 'files': len(archive.infolist())}

if __name__ == '__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        futures = {pool.submit(collect, repo): repo for repo in REPOS}
        for future in concurrent.futures.as_completed(futures):
            try:
                print(json.dumps(future.result()), flush=True)
            except Exception as exc:
                print(json.dumps({'repo': futures[future], 'error': str(exc)}), flush=True)
