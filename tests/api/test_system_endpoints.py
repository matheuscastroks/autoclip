from fastapi.testclient import TestClient
from engine.api.app import create_app

TOKEN = "test-token"

def test_system_profile_endpoint(tmp_path):
    app = create_app(tmp_path, token=TOKEN)
    client = TestClient(app, base_url="http://127.0.0.1:8765", headers={"Authorization": "Bearer " + TOKEN})
    res = client.get("/api/v1/system/profile")
    assert res.status_code == 200
    data = res.json()
    assert data["schema_version"] == "1.0"
    assert "recommended_tier" in data["profile"]
    assert "recommended_model_id" in data["profile"]
    assert data["profile"]["recommended_tier"] in (1, 2, 3)

def test_system_provision_status_idle(tmp_path):
    app = create_app(tmp_path, token=TOKEN)
    client = TestClient(app, base_url="http://127.0.0.1:8765", headers={"Authorization": "Bearer " + TOKEN})
    res = client.get("/api/v1/system/provision/status")
    assert res.status_code == 200
    assert res.json()["status"] in ("idle", "ready")

def test_system_provision_cancel(tmp_path):
    app = create_app(tmp_path, token=TOKEN)
    client = TestClient(app, base_url="http://127.0.0.1:8765", headers={"Authorization": "Bearer " + TOKEN})
    res = client.post("/api/v1/system/provision/cancel")
    assert res.status_code == 200
    assert res.json()["cancelled"] is True
