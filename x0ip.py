##
## imports
##

import socket

##
## code
##

class X0IP:
    """IP connectivity to JVC"""

    def __init__(self, peer, useLog, timeoutConfig):
        self.log = useLog
        self.peer = peer
        self.socket = 0
        self.connected = False
        self.timeout = timeoutConfig['jvcIP']

    def connect(self):
        self.log.debug(f'Inside connect with peer {self.peer}')
        if self.socket != 0:
            self.log.debug(f'Socket is not zero so closing it')
            self.close()

        self.log.debug(f'Creating new socket')
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(self.timeout)
        self.connected = False

        try:
            self.socket.connect(self.peer)

            # improve later
            temp = self.socket.recv(20)
            self.log.debug(f'Temp is {temp}')
            self.socket.send(b'PJREQ')
            temp = self.socket.recv(20)
            self.log.debug(f'Temp is {temp}')

            self.connected = True
        except Exception as ex:
            self.log.debug(f'connect exception {ex}')
            self.close()

        self.log.debug(f'Connected state is {self.connected}')
        return self.connected

    def close(self):
        self.log.debug(f'close socket was called')
        if self.socket != 0:
            self.socket.close()
            self.socket = 0
            self.connected = False


    def send(self,data):
        try:
            if not self.connected:
                self.log.debug(f'send called but not connected')
                self.connect()

        except Exception as ex:
            self.log.debug(f'Exception from connect during send {ex}')
            return False

        if not self.connected:
            self.log.debug(f'Unpexged trying to send while not connected')
            return False

        try:
            self.socket.sendall(data)
            return True
        except Exception as ex:
            self.log.debug(f'socket send exception {ex}')
            self.close()

            return False

    def read(self):
        try:
            if not self.connected:
                self.log.debug(f'read called but not connected')
                self.connect()

        except Exception as ex:
            self.log.debug(f'Exception from connect during recv {ex}')
            return b''

        if not self.connected:
            self.log.debug(f'Returning nothing because not connected')
            return b''

        try:
            rxData = self.socket.recv(20)
            if rxData == b'':
                self.log.debug('Socket read returned nothing')
                return b''
            else:
                self.log.debug(f'Socket read returned {len(rxData)} bytes')
                # this is currently assuming all the JVC data will be in aisngle UDP frame
                return rxData

        except socket.timeout:
            self.log.debug(f'Returning nothing because of timeout')
            return b''

        except Exception as ex:
            self.log.debug(f'Exception from recv {ex}')
            self.close()

            return b''

