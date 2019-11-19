import pytest
import requests
import requests_staticmock
from .Observer import Observer
from .config import Config
import json
import os

config = Config()

class ParticularObserver(Observer):
    def __init__(self, session, name):
        self.data_types = {
            'pytest_data': {'name': 'Pytest data', 'description': 'Solely for tests', 'units': 'NA'}
        }
        super(ParticularObserver, self).__init__(session = session, name = name)

    def observe(self):
        return {'pytest_data': 43}

class MockNumericApi(requests_staticmock.BaseMockClass):
    def _authorize(self, request, body):
        post_json = json.loads(body)
        assert 'username' in post_json
        assert 'password' in post_json
        return json.dumps({'access_token': 'random_token'})

    def _sources_test_src(self, request, url, body):
        source_id = url.rpartition('/')
        assert source_id[-1] == config.DATA_SOURCE_ID
        post_json = json.loads(body)
        assert 'name' in post_json
        return ''

    def _types_pytest_data(self, request, url, body):
        type_id = url.rpartition('/')
        assert type_id[-1] == 'pytest_data'
        post_json = json.loads(body)
        assert 'name' in post_json
        assert 'units' in post_json
        return ''

    def _data(self, request, body):
        post_json = json.loads(body)
        assert 'Data' in post_json
        assert isinstance(post_json['Data'], list)
        for data_item in post_json['Data']:
            assert 'data_source_id' in data_item
            assert 'data_type_id' in data_item
            assert 'entity_created' in data_item
            assert 'value' in data_item
        return ''

@pytest.fixture(scope = "session")
def observer():
    session = requests.Session()
    with requests_staticmock.mock_session_with_class(session, MockNumericApi, config.BASE_URL):
        try:
            os.remove(config.LOG_FILE)
        except:
            pass
        yield ParticularObserver(session = session, name = "Pytest observer")


class TestObserver:

    def setup_class(self):
        pass


    def teardown_class(self):
        try:
            os.remove(config.BEARER_FILE)
        except:
            pass

    def test_token(self, observer):
        assert observer.bearer

    def test_observe(self, observer):
        observer.observe_and_upload()
