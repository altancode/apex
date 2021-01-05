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
        self.buffer = b''
        self.ignoreACK = b'\x06\x89\x01\x00\x00\n'
        self.chatty = False

    def connect(self):
        self.log.debug(f'Inside connect with peer {self.peer}')
        if self.socket != 0:
            self.log.debug(f'Socket is not zero so closing it')
            self.close()

        self.log.debug(f'Creating new socket')
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.socket.settimeout(self.timeout)
        self.connected = False

        try:
            self.socket.connect(self.peer)

            # improve later
            temp = self.socket.recv(20)
            self.log.debug(f'JVC Sync1 is {temp}')
            self.socket.send(b'PJREQ')
            temp = self.socket.recv(20)
            self.log.debug(f'JVC Sync2 is {temp}')

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
            self.log.debug(f'Unexpected trying to send while not connected')
            return False

        try:
            self.socket.sendall(data)
            return True
        except Exception as ex:
            self.log.debug(f'socket send exception {ex}')
            self.close()

            return False

    def read(self, emptyIt = False):
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
            rxData = self.socket.recv(200)
            if rxData == b'':
                if self.chatty:
                    self.log.debug('Socket read returned nothing')
                return b''
            else:
                if self.chatty:
                    self.log.debug(f'Socket read returned {len(rxData)} bytes.   Buffer is {len(self.buffer)}')

                self.buffer += rxData
                
                while True:
                    if self.chatty:
                        self.log.debug(f'buffer is {self.buffer}')

                    first = self.buffer.find(b'\n')
                    if first > 0:
                        # we found it
                        r = self.buffer[0:first+1]
                        self.buffer = self.buffer[first+1:]
                        if self.chatty:
                            self.log.debug(f'buffer reduced to {self.buffer}')

                        if emptyIt:
                            # ignore r and loop again
                            if self.chatty:
                                self.log.debug(f'Discarding {r}')
                            pass

                        elif r == self.ignoreACK:
                            # we always ignore this
                            if self.chatty:
                                self.log.debug(f'Ignoring {r}')
                            pass

                        else:
                            # ok to return it
                            if self.chatty:
                                self.log.debug(f'returning {r}')
                            return r
    
                    else:
                        # didn't get a full line
                        # nothing to return yet
                        return b''

        except socket.timeout:
            if self.chatty:
                self.log.debug(f'Returning nothing because of timeout')
            return b''

        except Exception as ex:
            self.log.debug(f'Exception from recv {ex}')
            self.close()

            return b''

