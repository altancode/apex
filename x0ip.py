##
## imports
##

from abc import ABC, abstractmethod
import socket

##
## code
##


class AbstractIP(ABC):

    def __init__(self, name, peer, useLog, timeoutConfig, delimit = None):
        self.name = name
        self.log = useLog
        self.peer = peer
        self.socket = None
        self.connected = False
        self.timeout = timeoutConfig[self.name]
        self.buffer = b''
        self.chatty = True 
        self.delimit = delimit

    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def close(self):
        pass

    @abstractmethod
    def send(self,data):
        pass

    @abstractmethod
    def read(self, emptyIt = False):
        pass



class X0IPJVC(AbstractIP):
    """IP connectivity to JVC"""

    def __init__(self, name, peer, useLog, timeoutConfig, delimit = None):
        self.name = name
        self.log = useLog
        self.peer = peer
        self.socket = None
        self.connected = False
#        self.timeout = timeoutConfig['jvcIP']
        self.timeout = timeoutConfig[self.name]
        self.buffer = b''
        self.ignoreACK = b'\x06\x89\x01\x00\x00\n'
        self.chatty = False

    def connect(self):
        self.log.debug(f'Inside connect with peer {self.peer}')
        if self.socket != None:
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
        if self.socket != None:
            self.socket.close()
            self.socket = None
            self.connected = False
            self.buffer = b''


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
        if emptyIt and (not self.connected):
            # if we aren't connected then there's nothing to do for emptyIt
            return b''
        
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
            # don't do a socket read if we have a message buffered
            haveit = (self.buffer.find(b'\n') >= 0)
            if haveit:
                self.log.debug(f'Using buffered data len={len(self.buffer)}, data={self.buffer}')

            rxData = b''
            if not haveit:
                rxData = self.socket.recv(200)

            if (not haveit) and (rxData == b''):
                # no message in buffer and nothing received from network
                if self.chatty:
                    self.log.debug('Socket read returned nothing')
                return b''
            else:
                if self.chatty and (not haveit):
                    self.log.debug(f'Socket read returned {len(rxData)} bytes.   Buffer is {len(self.buffer)}')

                self.buffer += rxData
                
                while True:
                    if self.chatty:
                        self.log.debug(f'buffer is {self.buffer}')

                    first = self.buffer.find(b'\n')
                    if first >= 0:
                        # we found it
                        moreThanOne = self.buffer[first+1:].find(b'\n') >= 0
                        if self.chatty or moreThanOne:
                            self.log.debug(f'buffer is {len(self.buffer)} data:{self.buffer}')

                        r = self.buffer[0:first+1]
                        self.buffer = self.buffer[first+1:]

                        if self.chatty or moreThanOne:
                            self.log.debug(f'buffer reduced to len:{len(self.buffer)} data:{self.buffer}')

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
            self.log.debug(f'Exception from recv {ex}', exc_info=True)
            self.close()

            return b''



class X0IPGeneric(AbstractIP):
    """IP connectivity to JVC"""

    def __init__(self, name, peer, useLog, timeoutConfig, delimit = b'\x1a\r\n'):
        self.name = name
        self.log = useLog
        self.peer = peer
        self.socket = None
        self.connected = False
        self.timeout = timeoutConfig[self.name]
        self.chatty = True
        self.buffer = b''
        self.delimit = delimit

    def connect(self):
        self.log.debug(f'Inside connect with peer {self.peer}')
        if self.socket != None:
            self.log.debug(f'Socket is not zero so closing it')
            self.close()

        self.log.debug(f'Creating new socket')
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        self.socket.settimeout(self.timeout)
        self.connected = False

        try:
            self.socket.connect(self.peer)
            self.connected = True
        except Exception as ex:
            self.log.debug(f'connect exception {ex}')
            self.close()

        self.log.debug(f'Connected state is {self.connected}')
        return self.connected

    def close(self):
        self.log.debug(f'close socket was called and socket is {self.socket}')
        if self.socket != None:
            self.socket.close()
            self.socket = None
            self.connected = False
            self.buffer = b''

    def send(self,data):
        self.log.debug('send called')
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

            self.log.debug(f'returning false')
            return False


    def read(self, emptyIt = False):
        self.log.debug(f'read called')
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
            # don't do a socket read if we have a message buffered
            haveit = (self.buffer.find(self.delimit) >= 0)
            if haveit:
                self.log.debug(f'Using buffered data len={len(self.buffer)}, data={self.buffer}')

            rxData = b''
            if not haveit:
                rxData = self.socket.recv(2000)
                self.log.debug(f'Called recv and got {rxData}')

            if (not haveit) and (rxData == b''):
                # no message in buffer and nothing received from network
                if self.chatty:
                    self.log.debug('Socket read returned nothing')
                return b''
            else:
                if self.chatty and (not haveit):
                    self.log.debug(f'Socket read returned {len(rxData)} bytes.   Buffer is {len(self.buffer)}')

                self.buffer += rxData
                
                while True:
                    if self.chatty:
                        self.log.debug(f'buffer is {self.buffer}')

                    first = self.buffer.find(self.delimit)
                    if first >= 0:
                        # we found it
                        moreThanOne = self.buffer[first+len(self.delimit):].find(self.delimit) >= 0
                        if self.chatty or moreThanOne:
                            self.log.debug(f'buffer is {len(self.buffer)} data:{self.buffer}')

                        r = self.buffer[0:first+len(self.delimit)]
                        self.buffer = self.buffer[first+len(self.delimit):]

                        if self.chatty or moreThanOne:
                            self.log.debug(f'buffer reduced to len:{len(self.buffer)} data:{self.buffer}')

                        if emptyIt:
                            # ignore r and loop again
                            if self.chatty:
                                self.log.debug(f'Discarding {r}')
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
            self.log.debug(f'Exception from recv {ex}', exc_info=True)
            self.close()

            return b''


    # def read(self, emptyIt = False):
    #     try:
    #         if not self.connected:
    #             self.log.debug(f'read called but not connected')
    #             self.connect()

    #     except Exception as ex:
    #         self.log.debug(f'Exception from connect during recv {ex}')
    #         return b''

    #     if not self.connected:
    #         self.log.debug(f'Returning nothing because not connected')
    #         return b''

    #     try:
    #         rxData = self.socket.recv(200)

    #         if (rxData == b''):
    #             # no message in buffer
    #             if self.chatty:
    #                 self.log.debug('Socket read returned nothing')
    #             return b''
    #         else:
    #             if self.chatty:
    #                 self.log.debug(f'returning {rxData}')
    #             return rxData

    #     except socket.timeout:
    #         if self.chatty:
    #             self.log.debug(f'Returning nothing because of timeout')
    #         return b''

    #     except Exception as ex:
    #         self.log.debug(f'Exception from recv {ex}')
    #         self.close()

    #         return b''

