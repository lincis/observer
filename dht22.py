import Adafruit_DHT as dht

from Observer import Observer
class ObserverDH22(Observer):
    def observe(self):
        h,t = dht.read_retry(dht.DHT22, 18)
        self.logger.debug('Temp=%.1f*C  Humidity=%.1f' % (t, h))
        return [t,h]
