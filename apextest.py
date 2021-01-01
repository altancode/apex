

# 2020-12-24 18:46:13: Got "b'!\x89\x01PMPM0D\n'"
# 2020-12-24 18:46:52: Got "b'!\x89\x01PMPM0C\n'"
# 2020-12-24 18:47:57: Got "b'!\x89\x01PMPM0D\n'"
# 2020-12-24 18:48:27: Got "b'!\x89\x01PMPM0D\n'"
# 2020-12-24 18:49:26: Got "b'!\x89\x01PMPM0D\n'"
# 2020-12-24 18:49:56: Got "b'!\x89\x01PMPM0E\n'"
# 2020-12-24 18:50:30: Got "b'!\x89\x01PMPM0C\n'"

##
## imports
##

import logging
from logging.handlers import RotatingFileHandler
import time
import sys
import datetime

import x0ip 
import x0serial
import x0state

##
## code
##

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






def tstring():
    """Return a time string"""
    now = datetime.datetime.now()
    ptime = now.strftime("%Y-%m-%d %H:%M:%S")
    return ptime    

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

    log.info(f'Test started...')


    log.debug(f'Scenario 0')
    testcomn = X0CommTest(0)
    teststate = x0state.X0State(testcomn,log)

    teststate.set(b'01')

    teststate.action()
    teststate.action()
    teststate.action()

#

    log.debug(f'\nScenario 1')
    testcomn = X0CommTest(1)
    teststate = x0state.X0State(testcomn,log)

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
    teststate = x0state.X0State(testcomn,log)

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
    teststate = x0state.X0State(testcomn,log)

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
    teststate = x0state.X0State(testcomn,log)

    teststate.set(None)

    teststate.action()
    teststate.action()
    teststate.action()
    teststate.action()
    teststate.action()

    log.debug(f'\nScenario 5')
    testcomn = X0CommTest(5)
    teststate = x0state.X0State(testcomn,log)

    teststate.set(b'01')

    teststate.action()
    teststate.action()
    teststate.action()
    teststate.action()
    teststate.action()

    log.debug(f'\nScenario 6')
    testcomn = X0CommTest(6)
    teststate = x0state.X0State(testcomn,log)

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

