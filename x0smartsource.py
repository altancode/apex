##
## imports
##

import time
import x0opcmd
import x0refcmd
import logging

##
## globals
##


##
## code
##

class X0SmartSource:
    """Wait until JVC says source is valid nor not"""

    def __init__(self, inComm, useLog, timeoutConfig):

        self.log = useLog
        self.cfg = timeoutConfig
        self.desired = None
        self.jvcip = inComm
        self.state = ''
        self.timeout = 0
        self.timeoutOffset = timeoutConfig['jvcPowerTimeout']
        self.operation = None
        self.delayValidationUntil = 0


    def action(self):

        # 1. Sent Power State
        # 2. Validate Power State
        # 3. Not not correct state, go back to 1

        # Flow:
        # ''
        #   validating
        #       potentially finish with timeout
        #       potentially finish successfully
        #       potentilly go to delay-validation
        #           validating

        if not self.desired:
            self.log.error('Called with nothing to do')
            # True means nothing more to do
            return (True,None)

        if self.state == '':
            self.log.debug(f'State "{self.state}"')
            self.log.info(f'First checking whether JVC source is {self.desired}')

            # we set this timeout once regardless of how many verifications or restarts occur
            # this timeout is the max time the process can take regardless of what individual steps occur
            self.timeout = time.time() + self.timeoutOffset

            # build the reference command
            self.operation = x0refcmd.X0RefCmd(self.jvcip, self.log, self.cfg)
            self.operation.set('SC',b'')
#           self.operation.set('IFIS',b'')
            self.state = 'validating'

        elif self.state == 'validating':
            finished, rsp = self.operation.action()

            if finished:
                self.log.debug(f'JVC says source is rsp:{rsp}')

                if time.time() > self.timeout:
                    # Too much time has passed
                    # unfortuntaely there's nothing else we can do, we are giving up
                    self.log.error(f'UNABLE TO GET JVC SOURCE STATE. rsp:{rsp}')
                    self.state = ''
                    self.desired = None

                else:
#                   if (b'0B' == rsp):
                    if (self.desired != rsp):
                        self.log.info(f'JVC source did not match... Desired: {self.desired} rsp: {rsp}')

                        # now we need to verify again
                        self.delayValidationUntil = time.time() + 0.5
                        self.state = 'delay-validation'

                    else:
                        self.log.info(f'SUCCESS!  JVC source is as expected. desired:{self.desired} rsp:{rsp}')
                        self.state = ''
                        self.desired = None


        elif self.state == 'delay-validation':
            if time.time() > self.delayValidationUntil:
                self.log.debug('delay-validation complete, validating JVC source')
                self.operation = x0refcmd.X0RefCmd(self.jvcip, self.log, self.cfg)
                self.operation.set('SC',b'')
#               self.operation.set('IFIS',b'')
                self.state = 'validating'

        else:
            self.log.error(f'**** YIKES {self.state}')


        if not self.desired:
            # we are done
            return (True,None)
        else:
            # more to do
            return (False,None)

       

    def set(self, cmd:str, data: bytearray):
        
        if self.desired:
            # same mode
            self.log.error(f'!!!! Already sending command {self.desired} {cmd} {data}')
        else:
            self.desired = b'0'
            if cmd == '1':
                self.desired = b'1'
            self.log.info(f'Asked to wait for JVC source {self.desired}')

            # definitely need to restart the state machine
            self.state = ''
            self.action()
