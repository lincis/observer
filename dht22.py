import Adafruit_DHT as dht

from Observer import Observer
class ObserverDH22(Observer):
    def observe(self):
        h,t = dht.read_retry(dht.DHT22, 18)
        self.logger.info('Temp=%.1f*C  Humidity=%.1f' % (t, h))
        return [t,h]

if __name__ == '__main__':
    import sys

    if len(sys.argv) != 2:
        sys.exit('Syntax: %s COMMAND' % sys.argv[0])

    cmd = sys.argv[1].lower()
    service = ObserverDH22('dh22', pid_dir='/tmp')

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
