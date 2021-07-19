import os

class Config(object):
    BASE_URL = os.environ.get('BASE_URL')
    API_USER = os.environ.get('API_USER')
    API_PW = os.environ.get('API_PW')
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'DEBUG')
    BEARER_FILE = os.environ.get('BEARER_FILE')
    LOG_FILE = os.environ.get('LOG_FILE', '/var/log/observer.log')
    DATA_SOURCE_ID = os.environ.get('DATA_SOURCE_ID')
    DATA_SOURCE = os.environ.get('DATA_SOURCE')
    MAX_QUEUE_ITEMS = os.environ.get('MAX_QUEUE_ITEMS', 100)
    READ_INTERVAL = os.environ.get('READ_INTERVAL', 3)
    OBSERVATION_INTERVAL = os.environ.get('OBSERVATION_INTERVAL', 60)
    DO_POST = os.environ.get('DO_POST', True) in (True, 'true', '1', 't')
    PUSH_PROMETHEUS = os.environ.get('PUSH_PROMETHEUS', True) in (True, 'true', '1', 't')
