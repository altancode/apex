##
## imports
##

import time
import misc

##
## code
##

class X0RefCmd:
    """The main Apex state object that does the magic"""

    def __init__(self, inComm, useLog, timeoutConfig):

        global log
        log = useLog

        self.desired = None
        self.comm = inComm
        self.state = ''
        self.timeout = 0
        self.refAckOffset = timeoutConfig['jvcRefAck']
        self.defaultOffset = timeoutConfig['jvcDefault']
        self.opAckOffset = timeoutConfig['jvcOpAck']
        self.checkwaitacktimeout = 0
        self.opcmd = b''
        self.keepaliveOffset = 5
        self.nextKeepalive = time.time() + self.keepaliveOffset
        self.chatty = False


    def action(self):
        # this is where the work happens

        if self.state == '':
            # no unexpected data coming from source so we start
            log.debug(f'Inside state "{self.state}"')

            cmd = b'\x3F\x89\x01' + self.desired + b'\x0a'
            self.opcmd = cmd
            log.debug(f'Sending REFERENCE command {self.opcmd}')
            ok = self.comm.send(cmd)
            if not ok:
                # do not move to next state!
                # basically we'll try again next time
                log.debug(f'Could not send refernece command')
            else:
                # it was sent
                self.state = 'waitRefACK'
                self.timeout = time.time() + self.refAckOffset
        
        elif self.state == 'waitRefACK':
            log.debug(f'Inside state "{self.state}"')

            # quick test of whether socket is connected
            ok = self.comm.send(b'')
            if not ok:
                # no socket even after send tried to create one
                log.debug(f'JVC connection lost and not ready yet.  Restarting...')

                self.state = ''

            else:
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
                            log.warning(f'Giving up... JVC powered off?')
                            self.desired = None
                            self.checkwaitacktimeout = 0

                else:
                    log.debug(f'Got data {rxData}')
                    # we got something
                    self.checkwaitacktimeout = 0

                    exp = b'\x06\x89\x01' + self.desired[0:2] + b'\x0a'
                    if rxData == exp:
                        # got the ack
                        log.debug(f'Got the reference ACK {rxData}')
                        self.state = 'waitRefData'
                        self.timeout = time.time() + self.defaultOffset

                    else:
                        # what happened?
                        log.warning(f'Wanted {exp} but got {rxData}.  Ignoring...')


        elif self.state == 'waitRefData':
            log.debug(f'Inside state "{self.state}"')

            # see if there's a response
            rxData = self.comm.read()

            if rxData == b'':
                # got nothing.  Have we timed out?
                if time.time() > self.timeout:
                    # oops.  Start over
                    log.debug(f'Timeout in {self.state}.   Starting over')
                    self.state = ''
                    self.desired = None

            else:
                # we got something
                exp = b'@\x89\x01' + self.desired[0:2]
                if len(rxData) > len(exp) and exp[0:5] == rxData[0:5]:
                    # looks good
                    # got the data.  Is it different?

                    responseData = rxData[5:-1]

                    log.debug(f'Reference command response {responseData}')

                    self.state = ''
                    self.desired = None

                    return (True, responseData)

                else:
                    # what happened?
                    log.warning(f'Wanted {exp} but got {rxData}.  Ignoring...')

        else:
            log.error('**** YIKES {self.state}')
            

        if not self.desired:
            # we are done
            return (True,None)
        else:
            # more to do
            return (False,None)


    def set(self, cmd:str, data: bytearray):
        
        combined = bytes(cmd,'utf-8') + data
        if self.desired:
            # same mode
            log.warning(f'!!!! Already sending command {combined}')
        else:
            self.desired = combined
            log.info(f'Asked to send reference command {combined}')

            # definitely need to restart the state machine
            self.state = ''
            self.action()
