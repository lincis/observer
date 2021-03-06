import logging
import time
from threading import Timer
from .config import Config
import configparser
import requests
from datetime import datetime
import json
import redis
from prometheus_client import CollectorRegistry, push_to_gateway

from service import Service

class Observer:
    def __init__(self, name, session = None):
        self.config = Config()
        fh = logging.handlers.WatchedFileHandler(self.config.LOG_FILE)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        self.logger = logging.Logger(name = name)
        self.logger.addHandler(fh)
        self.logger.setLevel(getattr(logging, self.config.LOG_LEVEL))
        self.name = name
        self.redis = redis.Redis(host = 'localhost', port = 6379, db = 0, health_check_interval = 30)
        if self.config.PUSH_PROMETHEUS:
            self.prom_registry = CollectorRegistry()
            self.prom_gauges = {}
        if not session:
            self.session = requests.Session()
        else:
            self.session = session
        self.get_bearer()
        self.logger.debug("DO_POST = %s", self.config.DO_POST)
        self.logger.debug("PUSH_PROMETHEUS = %s", self.config.PUSH_PROMETHEUS)
        if self.config.DO_POST:
            self.create_source_and_type()
        if not self.data_types:
            self.data_types = {'default': {'name': 'Default data type', 'units': 'default', 'description': 'Base class built in type'}}
        self.data_queue = []
        self.logger.debug("Init completed")
        self.last_observation = None

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
        send_data = False
        if not self.last_observation:
            send_data = True and self.config.DO_POST
        elif (datetime.now() - self.last_observation).seconds >= self.config.OBSERVATION_INTERVAL:
            send_data = True and self.config.DO_POST
        if send_data:
            self.last_observation = datetime.now()
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
        self.redis.publish(self.name, json.dumps(observation))
        if self.config.PUSH_PROMETHEUS:
            try:
                for type_id in self.data_types.keys():
                    value = observation.get(type_id, None)
                    g = self.prom_gauges.get(type_id, None)
                    if g is not None:
                        g.set(value)
                push_to_gateway('localhost:9091', job = 'Observer_%s' % self.name, registry = self.prom_registry)
                self.logger.info('Push to Prometheus succesfull: %s', str(self.prom_gauges))
            except Exception as e:
                self.logger.warn('Push to prometheus failed: %s', str(e))

    def run(self):
        while True:
            try:
                self.observe_and_upload()
                self.logger.debug("Observed")
            except:
                self.logger.exception("Failed to observe")
                raise
            time.sleep(self.config.READ_INTERVAL)

    def observe(self):
        raise NotImplementedError
