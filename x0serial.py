##
## imports
##

import serial
import serial.tools.list_ports

##
## code
##

def showSerialPorts():
    ports = serial.tools.list_ports.comports()

    for port, desc, hwid in sorted(ports):
        print(f'{port} {desc} {hwid}')


class X0Serial:
    """Serial connectivity to HDFury and builds up full lines of data """

    def __init__(self, dev, useLog, timeoutConfig):

        self.log = useLog
        self.ser = serial.Serial()
        self.ser.baudrate = 19200
        self.ser.port = dev
        self.ser.timeout = timeoutConfig['hdfuryRead']

        self.buffer = b''

    def connect(self):
        self.ser.open()

        self.log.debug(f'Serial port is_open {self.ser.is_open}')


    def read(self):
        ## read and wait for a timeout
#        self.log.debug(f'Calling readline and buffer is "{self.buffer}"')
        data = self.ser.readline()
#        self.log.debug(f'Readline returned "{data}"')

        bytes = len(data)
        if bytes > 0:
            if data[bytes-1] == 0x0A:
                ## appears we have the end of a command
                result = self.buffer + data
                self.buffer = b''
                return result

            else:
                ## we got data but it doesn't have 0x0A at the end
                ## this means there's more data needed (hopefully)
                self.buffer = self.buffer + data
                return b''

        return b''
