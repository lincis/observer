import subprocess
import json
from Observer.Observer import Observer

class ObserverMHZ19(Observer):
    def __init__(self, name, session = None, *args, **kwargs):
        self.data_types = {
            'mhz19_co2': {'name': 'CO2', 'description': 'CO2 concentration from MH-Z19B', 'units': 'ppm'}
        }
        super(ObserverMHZ19, self).__init__(session = session, name = name, *args, **kwargs)

    def observe(self):
        raw_data = subprocess.run(['python', '-m', 'mh_z19'], stdout=subprocess.PIPE)
        if raw_data == 'null' or raw_data is None:
            self.logger.warning('Cannot read CO2 from MH-Z19')
            return {}
        co2 = json.loads(raw_data.stdout.decode('utf-8')).get('co2', None)
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
