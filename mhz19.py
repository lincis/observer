import subprocess
import json
import mh_z19
from Observer.Observer import Observer
import RPi.GPIO as GPIO
import time

RELAY_PIN = 23

class ObserverMHZ19(Observer):
    def __init__(self, name, session = None, *args, **kwargs):
        self.data_types = {
            'mhz19_co2': {'name': 'CO2', 'description': 'CO2 concentration from MH-Z19B', 'units': 'ppm'}
        }
        super(ObserverMHZ19, self).__init__(session = session, name = name, *args, **kwargs)
        mh_z19.abc_off()
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(RELAY_PIN, GPIO.OUT)
        GPIO.output(RELAY_PIN, GPIO.HIGH)

    def observe(self):
#        raw_data = subprocess.run(['python', '-m', 'mh_z19'], stdout=subprocess.PIPE)
        try:
            co2 = mh_z19.read().get('co2', None)
        except:
            GPIO.output(RELAY_PIN, GPIO.LOW)
            time.sleep(10)
            GPIO.output(RELAY_PIN, GPIO.HIGH)
            co2 = mh_z19.read().get('co2', None)
        self.logger.info('CO2 = %d ppm' % (co2))
        return {
            'mhz19_co2': co2
        }

if __name__ == '__main__':
    import sys

    if len(sys.argv) != 2:
        sys.exit('Syntax: %s COMMAND' % sys.argv[0])

    cmd = sys.argv[1].lower()
    service = ObserverMHZ19(name = 'mhz19b', pid_dir = '/var/run')

    if cmd == 'start':
        service.start()
    elif cmd == 'stop':
        service.stop()
    elif cmd == 'status':
        if service.is_running():
            print ("Service is running.")
        else:
            print ("Service is not running.")
    elif cmd == 'restart':
        while service.is_running():
            service.stop()
            time.sleep(1)
        service.start()
    else:
        sys.exit('Unknown command "%s".' % cmd)
