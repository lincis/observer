import logging
import time
from configparser import ConfigParser
from threading import Timer

from service import find_syslog, Service

class Observer(Service):
    def __init__(self, *args, **kwargs):
        super(Observer, self).__init__(*args, **kwargs)
        # self.logger.addHandler(SysLogHandler(address=find_syslog(),
                               # facility=SysLogHandler.LOG_DAEMON))
        fh = logging.FileHandler("observer.log")
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)
        self.logger.setLevel(logging.DEBUG)
        self.logger.debug("Init completed")

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

# if __name__ == '__main__':
#     import sys
#
#     if len(sys.argv) != 2:
#         sys.exit('Syntax: %s COMMAND' % sys.argv[0])
#
#     cmd = sys.argv[1].lower()
#     service = ObserverDH22('dh22', pid_dir='/tmp')
#
#     if cmd == 'start':
#         service.start()
#     elif cmd == 'stop':
#         service.stop()
#     elif cmd == 'status':
#         if service.is_running():
#             print ("Service is running.")
#         else:
#             print ("Service is not running.")
#     elif cmd == 'restart':
#         while service.is_running():
#             service.stop()
#             time.sleep(1)
#         service.start()
#     else:
#         sys.exit('Unknown command "%s".' % cmd)
