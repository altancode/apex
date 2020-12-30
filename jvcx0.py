##
## Apex (pre release)
## JVC + HDFurty Macro Optimiser (and more!)
##
## Please do not distribute
## Plan to eventually put into github 
## But need to clean up the code ;)
##

# 2020-12-24 18:46:13: Got "b'!\x89\x01PMPM0D\n'"
# 2020-12-24 18:46:52: Got "b'!\x89\x01PMPM0C\n'"
# 2020-12-24 18:47:57: Got "b'!\x89\x01PMPM0D\n'"
# 2020-12-24 18:48:27: Got "b'!\x89\x01PMPM0D\n'"
# 2020-12-24 18:49:26: Got "b'!\x89\x01PMPM0D\n'"
# 2020-12-24 18:49:56: Got "b'!\x89\x01PMPM0E\n'"
# 2020-12-24 18:50:30: Got "b'!\x89\x01PMPM0C\n'"

##
## Let's have some imports
##

import yaml
import logging
import sys
import serial
import time
import datetime
import socket
from logging.handlers import RotatingFileHandler

##
## Let's get started with code
##

class X0State:
    """THe main Apex state object that does the magic"""

    def __init__(self, inComm):
        self.desired = None
        self.comm = inComm
        self.state = ''
        self.timeout = 0
        self.ackoffset = 0.25
        self.offset = 2
        self.nextdata = b''
        self.checkwaitacktimeout = 0
        self.opcmd = b''

    def action(self):
        # this is where the work happens
#        log.debug(f'Action called in state "{self.state}" with desired {self.desired}')

        if self.desired == None:
            return

        # '' means nothing is going on
        # 'purgedone' means we've read any unexpected data and are ready to start our sequence
        # 'checkwaitack' means we have sent a Reference command and are waiting for the ack response
        # 'checkwaitdata' mean we received the ack but are now waiting for the actual data
        # 'setdataack' means we sent a command to change the state and are waiting the ack

        if self.state == '':
            # nothing going on, let's start the procoess
            log.debug(f'Inside state "{self.state}"')

            rxData = self.comm.read()

            if rxData == b'':
                log.debug(f'No unexpected data to purge')
                self.state = 'purgedone'
            else:
                # well... we got something we didn't expect
                # just toss it away and try to get nothing
                log.debug(f'Received data during purge {rxData}')

        elif self.state == 'purgedone':
            # no unexpected data coming from source so we start
            log.debug(f'Inside state "{self.state}"')

            cmd = b'?\x89\x01PMPM\n'
            log.info(f'Requesting current picture mode')
            log.debug(f'Sending REFERENCE command {cmd}')
            self.comm.send(cmd)

            self.state = 'checkwaitack'
            self.timeout = time.time() + self.ackoffset
        
        elif self.state == 'checkwaitack':
            log.debug(f'Inside state "{self.state}"')

            # see if there's a response
            rxData = self.comm.read()

            if rxData == b'':
                log.debug(f'Got no data')
                # got nothing.  Have we timed out?
                if time.time() > self.timeout:
                    # oops.  Start over
                    log.debug(f'Timeout in {self.state}.  {self.checkwaitacktimeout}.  Starting over')
                    self.state = ''

                    self.checkwaitacktimeout += 1
                    if self.checkwaitacktimeout > 40:
                        # we just give up
                        # projector powered off?
                        log.info(f'Giving up... JVC powered off?')
                        self.desired = None
                        self.checkwaitacktimeout = 0

                        ##
                        ## maybe disconnect and reconnect here?
                        ##

            else:
                log.debug(f'Got data {rxData}')
                # we got something
                self.checkwaitacktimeout = 0

                exp = b'\x06\x89\x01PM\x0A'
                l = len(exp)
                if len(rxData) >= l and rxData[0:l] == exp:
                    # got the ack
                    log.info(f'Got the Picture Mode reference ACK')
                    self.nextdata = rxData[l:]
                    log.debug(f'Set nextdata to {self.nextdata}')
                    self.state = 'checkwaitdata'
                    self.timeout = time.time() + self.offset

                else:
                    # what happened?
                    log.debug(f'{l} {rxData[0:l]}')
                    log.debug(f'Wanted {exp} but got {rxData}.  Starting over')
                    self.state = ''

        elif self.state == 'checkwaitdata':
            log.debug(f'Inside state "{self.state}"')

            # see if there's a response
            if self.nextdata == b'':
                rxData = self.comm.read()
            else:
                log.debug(f'Using next data {self.nextdata}')
                rxData = self.nextdata
                self.nextdata = b''

            if rxData == b'':
                # got nothing.  Have we timed out?
                if time.time() > self.timeout:
                    # oops.  Start over
                    log.debug(f'Timeout in {self.state}.   Starting over')
                    self.state = ''

            else:
                # check if it's the stuff jvc sends when processing is taking a whike?
                if rxData == b'\x06\x89\x01PM\n':
                    # extend timeout
                    log.debug(f'extending timeout...')
                    self.timeout = time.time() + self.offset

                else:
                    # we got something
                    exp = b'@\x89\x01PM'
                    if len(rxData) > len(exp) and exp[0:5] == rxData[0:5]:
                        # looks good
                        # got the data.  Is it different?

                        pjstate = rxData[5:7]
                        if pjstate == self.desired:
                            # already in this state
                            log.info(f'**** Already set to desired picture mode {self.desired}')
                            self.state = ''
                            self.desired = None

                            ## lets try closing the socket so it's opened next time
                            ## May help with unwanted delays when JVC closes the socket
                            self.comm.close()

                        else:
                            # start the command to change the state
                            log.info(f'**** Attempting to change picture mode to {self.desired}')

                            # ex: "b'!\x89\x01PMPM0D\n'"
                            cmd = b'!\x89\x01PMPM'
                            cmd += self.desired + b'\n'
                            log.debug(f'Sending Operation command {cmd}')
                            self.opcmd = cmd
                            self.comm.send(cmd)

                            self.state = 'setdataack'
#                            self.timeout = time.time() + self.offset
                            log.debug('trying timeout of 20 seconds')
                            self.timeout = time.time() + 20

                    else:
                        # what happened?
                        log.debug(f'Wanted {exp} but got {rxData}.  Starting over')
                        self.state = ''

        elif self.state == 'setdataack':
            log.debug(f'Inside state "{self.state}"')

            # see if there's a response
            rxData = self.comm.read()

            if rxData == b'':
                # got nothing.  Have we timed out?
                if time.time() > self.timeout:
                    # oops.  Start over
                    log.debug(f'Timeout in {self.state}.   Starting over')
                    self.state = ''

                ## try sending the opcmd
                log.debug('Sending opcmd again')
                self.comm.send(self.opcmd)

            else:
                # we got something
                exp = b'\x06\x89\x01PM\x0A'
                if rxData == exp:
                    # got the ack
                    log.debug(f'Got the ACK')

                    ##
                    ## SUCCESS!
                    ##
                    log.info(f'**** Picture Mode successfully changed to {self.desired}')
                    self.state = ''
                    self.desired = None

                    ## lets try closing the socket so it's opened next time
                    ## May help with unwanted delays when JVC closes the socket
                    self.comm.close()

                else:
                    # what happened?
                    log.debug(f'Wanted {exp} but got {rxData}.  Starting over')
                    self.state = ''


        else:
            log.error('**** YIKES {self.state}')
       

    def set(self, inDesired):
        self.desired = inDesired
        log.info(f'Desired picture mode is now {self.desired}')

        ## getting this while waiting for results may be an indication
        ## that the JVC will NOT respond
        ## so let's try restarting our state machine
        self.comm.close()
        self.state = ''

        self.action()


class X0CommTest:
    """Simulated IP object for testing"""

    def __init__(self, mode):
        self.mode = mode
        self.state = 0
        self.data = None
        pass


    def send(self,data):
        self.data = data


    def read(self):
        if self.mode == 0:
            ## no data to purge
            ## respond to state query with ACK
            ## respond to state query wtih answer that says same state
            ## that's it

            if self.state == 0:
                self.state = 1
                return b''

            if self.state == 1 and self.data == b'?\x89\x01PMPM\n':
                self.state = 2
                return b'\x06\x01PM\x0A'

            if self.state == 2:
                return b'@\x89\x01PM01'

        if self.mode == 1:
            ## same as mode 0 except...
            ## it takes too long to respond with the ack
            ## but everything should start over and end up saying we are in the right state already
            if self.state == 0:
                self.state = 1
                return b''

            if self.state == 1:
                time.sleep(5)
                self.mode = 0
                self.state = 0
                return b''

            log.debug(f'YIIKES {self.mode} {self.state}')
            return b''


        if self.mode == 2:
            ## return an unexpected response to the query
            if self.state == 0:
                self.state = 1
                return b''

            if  self.state == 1 and self.data == b'?\x89\x01PMPM\n':
                # return the unexpected data
                # then switch to mode 0
                self.mode = 0
                self.state = 0
                return b'\x06\x01XXX\n'

            log.debug(f'YIIKES {self.mode} {self.state}')
            return b''

        if self.mode == 3:
            # have a timeout when waiting for the query's data (not the ack)
            # then have it repeat but without a timeout
            if self.state == 0:
                self.state = 1
                return b''

            if self.state == 1 and self.data == b'?\x89\x01PMPM\n':
                self.state = 2
                return b'\x06\x01PM\x0A'

            if self.state == 2:
                time.sleep(2)
                self.state = 3
                return b''

            if self.state == 3:
                self.state = 4
                return b''

            if self.state == 4:
                self.state = 5
                return b'\x06\x01PM\x0A'

            if self.state == 5:
                self.state = 6
                return b'@\x89\x01PM01\n'

            log.debug(f'YIIKES {self.mode} {self.state}')


        if self.mode == 4:
            ## this tests the None desired state
            ## basically nothing should happen when action is called
            ## so this shouldn't ever be called
            log.debug(f'SHOULD NOT BE CALLED')

        if self.mode == 5:
            ## this is a full sequence
            ## includes changing the state
            if self.state == 0:
                self.state = 1
                return b''

            if self.state == 1 and self.data == b'?\x89\x01PMPM\n':
                # caller send request
                # we send initial ACK
                self.state = 2
                return b'\x06\x01PM\x0A'

            if self.state == 2:
                self.state = 3
                # now we send the actual response
                # but we don't return b'01' because we want the set to follow
                return b'@\x89\x01PM02'

            if self.state == 3:
                # now the caller should be doing a set, so we send ack
                self.state = 4
                return b'\x06\x01PM\x0A'

            log.debug(f'YIIKES {self.mode} {self.state}')


        if self.mode == 6:
            ## this is 5 with a timeout ... after the request to change state
            ## this is a full sequence
            ## includes changing the state

            if self.state == 0:
                self.state = 1
                return b''

            if self.state == 1 and self.data == b'?\x89\x01PMPM\n':
                # caller send request
                # we send initial ACK
                self.state = 2
                return b'\x06\x01PM\x0A'

            if self.state == 2:
                self.state = 3
                # now we send the actual response
                # but we don't return b'01' because we want the set to follow
                return b'@\x89\x01PM02'

            if self.state == 3:
                time.sleep(2)
                self.state = 4
                return b''

            if self.state == 4:
                # now the caller should be doing a set, so we send ack
                # but this will be late and unexpected
                self.state = 5
                return b'\x06\x01PM\x0A'

            if self.state == 5:
                # switch mode 5 which is a regular sequence
                self.state = 0
                self.mode = 5
                return b''

            log.debug(f'YIIKES {self.mode} {self.state}')


class X0IP:
    """IP object for Apex"""

    def __init__(self, peer):

        self.peer = peer
        self.socket = 0
        self.connected = False

    def connect(self):
        log.debug(f'Inside connect with peer {self.peer}')
        if self.socket != 0:
            log.debug(f'Socket is not zero so closing it')
            self.close()

        log.debug(f'Creating new socket')
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(0.25)
        self.connected = False

        try:
            self.socket.connect(self.peer)

            # this is a hack as I didn't kow it was needed
            # improve later
            temp = self.socket.recv(20)
            log.debug(f'Temp is {temp}')
            self.socket.send(b'PJREQ')
            temp = self.socket.recv(20)
            log.debug(f'Temp is {temp}')

            self.connected = True
        except Exception as ex:
            log.debug(f'connect exception {ex}')
            self.close()

        log.debug(f'Connected state is {self.connected}')
        return self.connected

    def close(self):
        log.debug(f'close socket was called')
        if self.socket != 0:
            self.socket.close()
            self.socket = 0
            self.connected = False


    def send(self,data):
        try:
            if not self.connected:
                log.debug(f'send called but not connected')
                self.connect()

        except Exception as ex:
            log.debug(f'Exception from connect during send {ex}')
            return b''

        if not self.connected:
            return False

        try:
            self.socket.sendall(data)
            return True
        except Exception as ex:
            log.debug(f'socket send exception {ex}')
            self.close()

            return False

    def read(self):
        try:
            if not self.connected:
                log.debug(f'read called but not connected')
                self.connect()

        except Exception as ex:
            log.debug(f'Exception from connect during recv {ex}')
            return b''

        if not self.connected:
            log.debug(f'Returning nothing because not connected')
            return b''

        try:
            rxData = self.socket.recv(20)
            if rxData == b'':
                log.debug('Socket read returned nothing')
                return b''
            else:
                log.debug(f'Socket read returned {len(rxData)} bytes')
                # this is currently assuming all the JVC data will be in aisngle UDP frame
                return rxData

        except socket.timeout:
            log.debug(f'Returning nothing because of timeout')
            return b''

        except Exception as ex:
            log.debug(f'Exception from recv {ex}')
            self.close()

            return b''



class X0Serial:
    """Serial object for Apex"""

    def __init__(self, dev):

        self.ser = serial.Serial()
        self.ser.baudrate = 19200
        self.ser.port = dev
        self.ser.timeout = 0.25

        self.buffer = b''

    def connect(self):
        self.ser.open()

        log.debug(f'is_open {self.ser.is_open}')


    def read(self):
        ## read and wait for a timeout
#        log.debug(f'Calling readline and buffer is "{self.buffer}"')
        data = self.ser.readline()
#        log.debug(f'Readline returned "{data}"')

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


def tstring():
    """Return a time string"""
    now = datetime.datetime.now()
    ptime = now.strftime("%Y-%m-%d %H:%M:%S")
    return ptime    


def jvcx0test():
    """Test Cases"""

    with open('apex.yaml') as file:
        cfg = yaml.full_load(file)

    jvcip = X0IP((cfg['jvcip'],cfg['jvcport']))
    jvcip.connect()

    vtxser = X0Serial(cfg['hdfury'])
    vtxser.connect()

    state = X0State(jvcip)

    state.set(b'02')
    x = 0
    while x < 100:

        state.action()
        x = x + 1

#        time.sleep(1)


def jvcx0():
    """Main Apex Loop"""

    with open('apex.yaml') as file:
        cfg = yaml.full_load(file)

    log.info(f'Using config {cfg}')

    jvcip = X0IP((cfg['jvcip'],cfg['jvcport']))
    jvcip.connect()

    vtxser = X0Serial(cfg['hdfury'])
    vtxser.connect()

    state = X0State(jvcip)

    while True:
        try:
            state.action()

            rxData = vtxser.read()

            if rxData != b'':
                # we got something
                log.debug(f'HDFury said "{rxData}"')

                example = b'!\x89\x01PMPM'
                if len(rxData) >= len(example) and rxData[0:len(example)] == example:
                    pm = rxData[7:9]
                    log.info(f'HDFury said to activate picture mode {pm}')
                    state.set(pm)
                else:
                    log.error(f'Ignoring {rxData} {rxData[0:len(example)]} {example}')

        except Exception as ex:
            log.error(f'Big Problem Exception {ex}')
            time.sleep(10)

##
##
##

if __name__ == "__main__":

    formatter = logging.Formatter('%(asctime)s - %(message)s')
    formatter.default_msec_format = '%s.%03d'
    log = logging.getLogger("jvcx0")
    log.setLevel(logging.DEBUG)

    # for files
    handler = RotatingFileHandler('./x0.log', maxBytes=500*1024, backupCount=5)
    handler.setFormatter(formatter)
    log.addHandler(handler)

    # for stderr
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    handler.setLevel(logging.INFO)
    log.addHandler(handler)

    log.info(f'Apex started...')

    jvcx0()

#    jvcx0test()
    sys.exit()


    log.debug(f'Scenario 0')
    testcomn = X0CommTest(0)
    teststate = X0State(testcomn)

    teststate.set(b'01')

    teststate.action()
    teststate.action()
    teststate.action()

#

    log.debug(f'\nScenario 1')
    testcomn = X0CommTest(1)
    teststate = X0State(testcomn)

    teststate.set(b'01')

    teststate.action()
    teststate.action()
    teststate.action()
    teststate.action()
    teststate.action()
    teststate.action()

#

    log.debug(f'\nScenario 2')
    testcomn = X0CommTest(2)
    teststate = X0State(testcomn)

    teststate.set(b'01')

    teststate.action()
    teststate.action()
    teststate.action()
    teststate.action()
    teststate.action()
    teststate.action()

#

    log.debug(f'\nScenario 3')
    testcomn = X0CommTest(3)
    teststate = X0State(testcomn)

    teststate.set(b'01')

    teststate.action()
    teststate.action()
    teststate.action()
    teststate.action()
    teststate.action()
    teststate.action()
    teststate.action()

    log.debug(f'\nScenario 4')
    testcomn = X0CommTest(4)
    teststate = X0State(testcomn)

    teststate.set(None)

    teststate.action()
    teststate.action()
    teststate.action()
    teststate.action()
    teststate.action()

    log.debug(f'\nScenario 5')
    testcomn = X0CommTest(5)
    teststate = X0State(testcomn)

    teststate.set(b'01')

    teststate.action()
    teststate.action()
    teststate.action()
    teststate.action()
    teststate.action()

    log.debug(f'\nScenario 6')
    testcomn = X0CommTest(6)
    teststate = X0State(testcomn)

    teststate.set(b'01')

    teststate.action()
    teststate.action()
    teststate.action()
    teststate.action()
    teststate.action()
    teststate.action()
    teststate.action()
    teststate.action()
    teststate.action()
    teststate.action()
    teststate.action()

