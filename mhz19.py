import subprocess
import json
from Observer.Observer import Observer
import time
import serial
import time
import traceback
import getrpimodel
import struct
import platform
import argparse
import sys
import json
import os.path
from prometheus_client import Gauge

# setting
version = "0.3.9"
pimodel        = getrpimodel.model
pimodel_strict = getrpimodel.model_strict()

if os.path.exists('/dev/serial0'):
  partial_serial_dev = 'serial0'
elif pimodel == "3 Model B" or pimodel_strict == "Zero W":
  partial_serial_dev = 'ttyS0'
else:
  partial_serial_dev = 'ttyAMA0'

serial_dev = '/dev/%s' % partial_serial_dev
stop_getty = 'sudo systemctl stop serial-getty@%s.service' % partial_serial_dev
start_getty = 'sudo systemctl start serial-getty@%s.service' % partial_serial_dev

# major version of running python
p_ver = platform.python_version_tuple()[0]

def connect_serial():
    return serial.Serial(serial_dev,
                        baudrate=9600,
                        bytesize=serial.EIGHTBITS,
                        parity=serial.PARITY_NONE,
                        stopbits=serial.STOPBITS_ONE,
                        timeout=1.0)
RELAY_PIN = 23

class ObserverMHZ19(Observer):
    def __init__(self, name, session = None, *args, **kwargs):
        self.data_types = {
            'mhz19_co2': {'name': 'CO2', 'description': 'CO2 concentration from MH-Z19B', 'units': 'ppm'}
        }
        super(ObserverMHZ19, self).__init__(session = session, name = name, *args, **kwargs)
        try:
            self.prom_gauges['mhz19_co2'] = Gauge('mhz19_co2', 'CO2 concentration from MH-Z19B, ppm', registry = self.prom_registry)
        except Exception as e:
            self.logger.warn('Failed to create gauges: %s', str(e))
        subprocess.call(stop_getty, stdout = subprocess.PIPE, shell = True)
        self.con_serial = connect_serial()

    def observe(self):
        co2 = None
        while 1:
            result = self.con_serial.write(b"\xff\x01\x86\x00\x00\x00\x00\x00\x79")
            s = self.con_serial.read(9)

            if p_ver == '2':
                if len(s) >= 4 and s[0] == "\xff" and s[1] == "\x86":
                    co2 = ord(s[2])*256 + ord(s[3])
                break
            else:
                if len(s) >= 4 and s[0] == 0xff and s[1] == 0x86:
                    co2 = s[2]*256 + s[3]
                break
        if co2 is None:
            raise Exception('Could not read CO2 conventration')
        return {
            'mhz19_co2': co2
        }

    def __del__(self):
        print('Destructor start tty')
        subprocess.call(start_getty, stdout = subprocess.PIPE, shell = True)

if __name__ == '__main__':
    service = ObserverMHZ19(name = 'mhz19b')
    service.run()
