from types import SimpleNamespace
import pytest
from test_projects import client

def model(name,actions=None):return SimpleNamespace(name='models/'+name,display_name=name,supported_actions=actions or ['generateContent'])

def test_catalog_uses_provider_ids_filters_and_deduplicates():
    from engine.api.gemini_connection import list_models
    closed=[];seen=[]
    class Models:
        def list(self,**kwargs):seen.append(kwargs);return iter([model('gemini-3.8-flash'),model('gemini-2.5-flash'),model('gemini-3.8-flash'),model('embedding',['embedContent'])])
    def factory(**kwargs):
        assert kwargs['api_key']=='fixture-key'
        return SimpleNamespace(models=Models(),close=lambda:closed.append(True))
    rows=list_models('fixture-key',client_factory=factory)
    assert {r['id'] for r in rows}=={'gemini-3.8-flash','gemini-2.5-flash'}
    assert all(r['name']=='models/'+r['id'] for r in rows)
    assert closed and seen

def test_get_status_does_not_make_network_request(client,monkeypatch):
    import engine.api.settings as settings
    monkeypatch.setattr(settings,'get_gemini_key',lambda:'fixture')
    connection=client.app.state.gemini_connection
    connection.catalog=lambda key:pytest.fail('No implicit network from status')
    assert client.get('/api/v1/config/gemini').json()['status']=='untested'

def test_saved_key_test_loads_catalog_and_refresh_detects_rotation(client,monkeypatch):
    import engine.api.settings as settings
    key=['fixture-a'];monkeypatch.setattr(settings,'get_gemini_key',lambda:key[0])
    client.app.state.gemini_connection.catalog=lambda k:[{'id':'gemini-3.8-flash','name':'models/gemini-3.8-flash','display_name':'Gemini Flash'}]
    result=client.post('/api/v1/config/gemini/test').json()
    assert result['status']=='valid' and result['models'][0]['id']=='gemini-3.8-flash'
    assert 'fixture-a' not in str(result)
    assert client.get('/api/v1/config/gemini').json()['status']=='valid'
    key[0]='fixture-b'
    result=client.get('/api/v1/config/gemini').json()
    assert result['status']=='untested' and result['models']==[]

@pytest.mark.parametrize('code,expected',[(400,'Chave'),(403,'permissão'),(429,'Limite'),(503,'indisponível')])
def test_bad_candidate_preserves_old_key_and_sanitizes_errors(client,monkeypatch,code,expected):
    import engine.api.settings as settings
    monkeypatch.setattr(settings,'get_gemini_key',lambda:'old-fixture')
    saved=[];monkeypatch.setattr(settings,'set_gemini_key',lambda key:saved.append(key))
    class Error(Exception):pass
    def fail(key):
        error=Error('SECRET fixture-new');error.code=code;raise error
    client.app.state.gemini_connection.catalog=fail
    response=client.put('/api/v1/config/credential',json={'key':'fixture-new'})
    assert response.status_code in (400,403,429,503)
    assert not saved and 'fixture-new' not in response.text and 'SECRET' not in response.text
    assert expected.lower() in response.text.lower()

def test_valid_candidate_is_saved_only_after_validation(client,monkeypatch):
    import engine.api.settings as settings
    key=['fixture-old'];events=[]
    monkeypatch.setattr(settings,'get_gemini_key',lambda:key[0])
    def save(value):events.append('saved');key[0]=value
    monkeypatch.setattr(settings,'set_gemini_key',save)
    def catalog(value):events.append('validated');return []
    client.app.state.gemini_connection.catalog=catalog
    response=client.put('/api/v1/config/credential',json={'key':'fixture-new'})
    assert response.status_code==200
    assert events==['validated','saved'] and response.json()['status']=='valid'
    assert response.json()['configured'] is True
