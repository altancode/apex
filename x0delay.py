##
## imports
##

import time
import misc

##
## code
##

class X0Delay:
    """Delay processing a specified number of milliseconds"""

    def __init__(self, inComm, useLog, timeoutConfig):

        self.log = useLog
        self.desired = None
        self.comm = inComm
        self.state = ''
        self.timeout = 0
        self.opAckOffset = timeoutConfig['jvcOpAckProfile']
        self.opcmd = b''
        self.timeoutResend = 0
        self.opAckResend = 1


    def action(self):
        # this is where the work happens
#        log.debug(f'Action called in state "{self.state}" with desired {self.desired}')

        if not self.desired:
            self.log.debug('Called with nothing to do')
            return True

        # '' means nothing is going on
        # 'wait' means we sent a command to change the state and are waiting the ack

        if self.state == '':
            self.log.debug(f'Inside state "{self.state}"')

            self.state = 'wait'
            self.timeout = time.time() + self.desired/1000
        
        elif self.state == 'wait':
            self.log.debug(f'Inside state "{self.state}"')

            if time.time() > self.timeout:
                ##
                ## Delay complete!
                ##
                self.log.info(f'Delay has completed {self.desired} ms')
                self.state = ''
                self.desired = None
        else:
            self.log.error('**** YIKES {self.state}')

        if not self.desired:
            # we are done
            return (True,None)
        else:
            # more to do
            return (False,None)

       
    def set(self, cmd:str, data: bytearray):
        
        if self.desired:
            # same mode
            self.log.error(f'Already set delay to {self.desired} ms')
        else:
            self.desired = int(cmd)
            self.log.info(f'Asked to set dekay {self.desired} ms')

            # definitely need to restart the state machine
            self.state = ''
            self.action()
