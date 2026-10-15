from pathlib import Path

import pytest

from test_projects import client, source_folder


@pytest.mark.parametrize('contents', [b'{broken', b'[]', b'{}', b'\xff'])
def test_corrupt_analysis_is_distinct_from_not_started(client, tmp_path, contents):
    root = source_folder(tmp_path)
    pid = client.post('/api/v1/projects/import', json={'path': str(root)}).json()['id']
    assert client.get(f'/api/v1/projects/{pid}/analysis').json()['state'] == 'not_started'
    path = root / 'analysis.json'
    path.write_bytes(contents)

    detail = client.get(f'/api/v1/projects/{pid}').json()
    assert detail['artifacts']['analysis']['state'] == 'invalid'
    assert not detail['has_analysis']
    assert 'analysis.json' in detail['warnings'][0]
    response = client.get(f'/api/v1/projects/{pid}/analysis')
    assert response.status_code == 200
    assert response.json()['state'] == 'invalid'
    assert response.json()['diagnostic']
    assert path.read_bytes() == contents


def test_unreadable_artifact_is_distinct_from_missing(client, tmp_path, monkeypatch):
    root = source_folder(tmp_path)
    pid = client.post('/api/v1/projects/import', json={'path': str(root)}).json()['id']
    original = Path.read_bytes

    def blocked(path):
        if path == root / 'analysis.json':
            raise PermissionError('fixture')
        return original(path)

    monkeypatch.setattr(Path, 'read_bytes', blocked)
    detail = client.get(f'/api/v1/projects/{pid}').json()
    assert detail['artifacts']['analysis']['state'] == 'unavailable'
    assert client.get(f'/api/v1/projects/{pid}/analysis').json()['state'] == 'unavailable'
