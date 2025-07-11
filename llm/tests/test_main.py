import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
os.environ.pop("HTTP_PROXY", None); os.environ.pop("HTTPS_PROXY", None)
from fastapi.testclient import TestClient
import main as m

client = TestClient(m.app)

def fake_completion(*args, **kwargs):
    return {"choices": [{"message": {"content": '{"decision":"approve","reason":"ok"}'}}]}

def fake_completion_msg(*args, **kwargs):
    return {"choices": [{"message": {"content": '{"is_spam": false, "reason":"clean"}'}}]}

def test_vet_join(monkeypatch):
    monkeypatch.setattr(m.litellm, 'completion', fake_completion)
    resp = client.post('/vet_join', json={'name':'John Doe','note':'Agentics'})
    assert resp.status_code == 200
    assert resp.json()['decision'] == 'approve'

def test_vet_message(monkeypatch):
    monkeypatch.setattr(m.litellm, 'completion', fake_completion_msg)
    resp = client.post('/vet_message', json={'author':'123','body':'hello'})
    assert resp.status_code == 200
    assert resp.json()['is_spam'] is False
