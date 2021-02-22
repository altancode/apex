##
## imports
##

import socket
import select
import json

##
## Code
##

class x0NetControl:
    """Receive commands from the network"""

    def __init__(self, useLog, port):
        self.port = port
        self.log = useLog
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.bind(('',self.port))
        self.s.listen()

        self.readList = [self.s]

    def action(self):

        results = []

        readable, _writable, errored = select.select(self.readList, [], self.readList, 0)
        # self.log.debug(f'readabout {readable}')
        # self.log.debug(f'errored {errored}') 
        for sock in readable:

            try:
                if sock is self.s:
                    # new connection
                    client_socket, address = self.s.accept()
                    self.readList.append(client_socket)
                    self.log.debug(f'Connection from {address}')
                else:
                    data = sock.recv(1024)
                    if data == b'':
                        # socket is closed
                        self.log.debug(f'{sock} needs to be closed because empty received')
                        sock.close()
                        self.readList.remove(sock)

                    self.log.debug(f'{sock} Received {data}')

                    try:
                        if data != b'':
                            j = json.loads(data)
                            results.append(j)
                    except Exception as ex:
                        self.log.error(f'{sock} Exception {ex} Could not parse {data}')
                        raise

            except Exception as ex:
                self.log.error(f'{sock} Exception {ex} Could not parse {data}')
                sock.close()
                self.readList.remove(sock)

        for sock in errored:
            sock.close()
            self.readList.remove(sock)

        return results
