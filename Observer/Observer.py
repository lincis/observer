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
    def __init__(self, name, session = None, *args, **kwargs):
        super(Observer, self).__init__(name = name)
        self.config = Config()
        fh = logging.WatchedFileHandler(self.config.LOG_FILE)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
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
        self.data_queue = []
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
                , json = {'username': self.config.API_USER, 'password': self.config.API_PW}
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

    def post(self, url, data):
        def _impl():
            response = self.session.request('put', url,
                json = data, headers = self.header()
            )
            if not response.ok:
                raise Exception('Creating source failed: %s' % response.text)
            return response
        self.logger.info('Post to %s: %s' % (url, data))
        try:
            response = _impl()
        except:
            try:
                self.get_bearer()
                response = _impl()
            except Exception as e:
                self.logger.error('Post failed: %s' % str(e))
                raise
        self.logger.info('Post success: %s' % (response.text))


    def create_source_and_type(self):
        url = '%s/sources/%s' % (self.config.BASE_URL, self.config.DATA_SOURCE_ID)
        self.post(url, {'name': self.config.DATA_SOURCE})
        for type_id, type_def in self.data_types.items():
            url = '%s/types/%s' % (self.config.BASE_URL, type_id)
            self.post(url, type_def)

    def observe_and_upload(self):
        observation = self.observe()
        self.logger.debug('Observerd: %s' % observation)
        obs_time = datetime.now().isoformat()
        for type_id in self.data_types.keys():
            value = observation.get(type_id, None)
            if not value:
                continue
            self.data_queue.append({
                'data_source_id': self.config.DATA_SOURCE_ID,
                'data_type_id': type_id,
                'value': value,
                'entity_created': obs_time
            })
        while len(self.data_queue) > self.config.MAX_QUEUE_ITEMS:
            removed = self.data_queue.pop(0)
            self.logger.warn('Removing item from queue, because length increases %d: %s' % (self.config.MAX_QUEUE_ITEMS, removed))
        try:
            self.post('%s/data' % self.config.BASE_URL, {'Data': self.data_queue})
            self.data_queue = []
        except Exception as e:
            self.logger.error('Post failed: %s' % str(e))
            self.logger.info('%d items in queue' % len(self.data_queue))

    def run(self):
        while not self.got_sigterm():
            try:
                self.observe_and_upload()
                self.logger.debug("Observed")
            except:
                self.logger.exception("Failed to observe")
                raise
            time.sleep(self.config.OBSERVATION_INTERVAL)

    def observe(self):
        raise NotImplementedError
