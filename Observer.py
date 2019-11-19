import logging
import time
from threading import Timer
from .config import Config
import configparser
import requests
from datetime import datetime
import json

from service import Service

class Observer(Service):
    def __init__(self, name, session = None):
        super(Observer, self).__init__(name = name)
        fh = logging.FileHandler("observer.log")
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.config = Config()
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)
        self.logger.setLevel(getattr(logging, self.config.LOG_LEVEL))
        if not session:
            self.session = requests.Session()
        else:
            self.session = session
        self.get_bearer()
        self.create_source_and_type()
        if not self.data_types:
            self.data_types = {'default': {'name': 'Default data type', 'units': 'default', 'description': 'Base class built in type'}}
        self.logger.debug("Init completed")

    def get_bearer(self, renew = False):
        config = configparser.ConfigParser()
        try:
            config.read(self.config.BEARER_FILE)
        except:
            pass
        if not 'Bearer' in config.sections():
            config['Bearer'] = {}
        b_config = config['Bearer']
        if renew or not b_config.get('Value', None):
            response = self.session.request('post', '%s/authorize' % self.config.BASE_URL
                , data = json.dumps({'username': self.config.API_USER, 'password': self.config.API_PW})
            )
            self.logger.debug('Auth response: %s', response.text)
            if not response.ok:
                raise Exception('Authorization failed: %s' % response.text)
            config['Bearer'] = {'Value': response.json()['access_token']}
            with open(self.config.BEARER_FILE, 'w') as configfile:
                config.write(configfile)
        self.bearer = config.get('Bearer', 'Value')

    def header(self):
        return {'Authorization': 'Bearer %s' % self.bearer}

    def create_source_and_type(self):
        def implementation():
            url = '%s/sources/%s' % (self.config.BASE_URL, self.config.DATA_SOURCE_ID)
            self.logger.info('Post to %s' % url)
            response = self.session.request('post', url,
                data = json.dumps({'name': self.config.DATA_SOURCE}), headers = self.header()
            )
            if not response.ok:
                raise Exception('Creating source failed: %s' % response.text)
            for type_id, type_def in self.data_types.items():
                url = '%s/types/%s' % (self.config.BASE_URL, type_id)
                self.logger.info('Post to %s' % url)
                response = self.session.request('post', url,
                    data = json.dumps(type_def), headers = self.header()
                )
                if not response.ok:
                    raise Exception('Creating source failed: %s' % response.text)
        try:
            implementation()
        except:
            self.get_bearer()
            implementation()

    def observe_and_upload(self):
        def send_data():
            data_to_send = {'Data': []}
            for type_id in self.data_types.keys():
                value = observation.get(type_id, None)
                if not value:
                    continue
                data_to_send['Data'].append({
                    'data_source_id': self.config.DATA_SOURCE_ID,
                    'data_type_id': type_id,
                    'value': value,
                    'entity_created': obs_time
                })
            self.logger.debug('Send data to %s: %s' % ('%s/data' % (self.config.BASE_URL), data_to_send))
            response = self.session.request('post', '%s/data' % (self.config.BASE_URL),
                data = json.dumps(data_to_send), headers = self.header()
            )
            if not response.ok:
                raise Exception('Creating source failed: %s' % response.text)
        observation = self.observe()
        self.logger.debug('Observerd: %s' % observation)
        obs_time = datetime.now().isoformat()
        try:
            send_data()
        except Exception as e:
            self.logger.info('Data sending failed: %s, will retry' % str(e))
            try:
                self.get_bearer()
                send_data()
            except Exception as e:
                self.logger.error('Data sending failed: %s' % str(e))
                raise

    def run(self):
        while not self.got_sigterm():
            try:
                self.observe()
                self.logger.debug("Observed")
            except:
                self.logger.exception("Failed to observe")
            time.sleep(5)

    def observe(self):
        raise NotImplementedError
