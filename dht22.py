#import adafruit_dht
#import board
import Adafruit_DHT as dht
from Observer.Observer import Observer
from prometheus_client import Gauge

class ObserverDH22(Observer):
#    dhtDevice = adafruit_dht.DHT22(board.D18)
#    dhtDevice = adafruit_dht.DHT22(18)
    def __init__(self, name, session = None, *args, **kwargs):
        self.data_types = {
            'dht22_temperature': {'name': 'Temperature', 'description': 'Temperature from DHT22 sensor', 'units': '℃'},
            'dht22_humidity': {'name': 'Humidity', 'description': 'Humidity from DHT22 sensor', 'units': '%'}
        }
        super(ObserverDH22, self).__init__(session = session, name = name, *args, **kwargs)
        try:
            self.prom_gauges['dht22_temperature'] = Gauge('dht22_temperature', 'Temperature from DHT22 sensor, ℃', registry = self.prom_registry)
            self.prom_gauges['dht22_humidity'] = Gauge('dht22_humidity', 'Humidity from DHT22 sensor, %', registry = self.prom_registry)
        except Exception as e:
            self.logger.warn('Failed to create gauges: %s', str(e))

    def observe(self):
#        temperature = self.dhtDevice.temperature
#        humidity = self.dhtDevice.humidity
        humidity, temperature = dht.read_retry(dht.DHT22, 18)
        self.logger.info('Temp=%.1f*C  Humidity=%.1f' % (temperature, humidity))
        return {
            'dht22_temperature': round(temperature, 1),
            'dht22_humidity': round(humidity, 1)
        }

if __name__ == '__main__':
    service = ObserverDH22(name = 'dh22')
    service.run()
