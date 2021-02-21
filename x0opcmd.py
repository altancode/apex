##
## imports
##

import time
import misc

##
## code
##

class X0OpCmd:
    """Send an operation command (aka, change a setting)"""

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
#        log.debug(f'Action called in state "{self.state}" with desired {self.desired}')

        if not self.desired:
            log.debug('Called with nothing to do')
            return True

        # '' means nothing is going on
        # 'waitRefACK' means we have sent a Reference command and are waiting for the ack response
        # 'waitRefData' mean we received the ack but are now waiting for the actual data
        # 'waitOpACK' means we sent a command to change the state and are waiting the ack

        if self.state == '':
            log.debug(f'Inside state "{self.state}"')

            cmd = b'\x21\x89\x01' + self.desired + b'\x0a'
            self.opcmd = cmd
            log.debug(f'Sending OPERATION command {cmd}')
            ok = self.comm.send(cmd)
            if not ok:
                # do not move to next state!
                # basically we'll try again next time
                log.debug(f'Could not send OPERATION command')
            else:
                # it was sent
                self.state = 'waitOpACK'
                self.timeout = time.time() + self.opAckOffset
        
        elif self.state == 'waitOpACK':
            log.debug(f'Inside state "{self.state}"')

            # see if there's a response
            rxData = self.comm.read()

            if rxData == b'':
                # got nothing.  Have we timed out?
                if time.time() > self.timeout:
                    # oops.  Start over
                    log.debug(f'Timeout in {self.state}.   Giving up.')
                    self.state = ''
                    self.desired = None

                ## try sending the opcmd
                log.debug('Sending opcmd again')
                ok = self.comm.send(self.opcmd)
                if not ok:
                    log.warning(f'Send failed in {self.state}.   Consider optimisation')

            else:
                # we got something
                exp = b'\x06\x89\x01' + self.desired[0:2] + b'\x0a'
                if rxData == exp:
                    # got the ack
                    log.debug(f'Got the ACK {rxData}')

                    ##
                    ## SUCCESS!
                    ##
                    log.info(f'**** Operation Command Successfully Performed {self.desired}')
                    self.state = ''
                    self.desired = None
                else:
                    # what happened?
                    log.error(f'Wanted {exp} but got {rxData}.  Ignoring...')
        else:
            log.error('**** YIKES {self.state}')

        if not self.desired:
            # we are done
            return True
        else:
            # more to do
            return False

       

    def set(self, cmd:str, data: bytearray):
        
        combined = bytes(cmd,'utf-8') + data
        if self.desired:
            # same mode
            log.warning(f'!!!! Already sending command {combined}')
        else:
            self.desired = combined
            log.info(f'!!!! Asked to send command {combined}')

            # definitely need to restart the state machine
            self.state = ''
            self.action()
