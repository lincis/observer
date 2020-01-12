#import adafruit_dht
#import board
import Adafruit_DHT as dht
from Observer.Observer import Observer

class ObserverDH22(Observer):
#    dhtDevice = adafruit_dht.DHT22(board.D18)
#    dhtDevice = adafruit_dht.DHT22(18)
    def __init__(self, name, session = None, *args, **kwargs):
        self.data_types = {
            'dht22_temperature': {'name': 'Temperature', 'description': 'Temperature from DHT22 sensor', 'units': '℃'},
            'dht22_humidity': {'name': 'Humidity', 'description': 'Humidity from DHT22 sensor', 'units': '%'}
        }
        super(ObserverDH22, self).__init__(session = session, name = name, *args, **kwargs)

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
