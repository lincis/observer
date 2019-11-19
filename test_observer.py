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
        print(body)
        return json.dumps({'access_token': 'random_token'})

    def _sources_test_src(self, request, body):
        return ''

    def _types_pytest_data(self, request, body):
        return ''

    def _heeeehe(self, request, body):
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
