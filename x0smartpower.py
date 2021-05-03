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

class X0SmartPower:
    """Change power state and ensure it changes"""

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
        #       potentially go to delay-restart
        #           restart
        #               setting
        #                   validating

        if not self.desired:
            self.log.error('Called with nothing to do')
            # True means nothing more to do
            return (True,None)

        if self.state == '':
            self.log.debug(f'State "{self.state}"')
            self.log.info(f'First checking whether JVC power state is {self.desired}')

            # we set this timeout once regardless of how many verifications or restarts occur
            # this timeout is the max time the process can take regardless of what individual steps occur
            self.timeout = time.time() + self.timeoutOffset

            # build the reference command
            self.operation = x0refcmd.X0RefCmd(self.jvcip, self.log, self.cfg)
            self.operation.set('PW',b'')
            self.state = 'validating'

        elif self.state == 'restart':
            self.log.debug(f'State "{self.state}"')
            self.log.info(f'Telling JVC to set power state to {self.desired}')

            # need to make a opcmd
            self.operation = x0opcmd.X0OpCmd(self.jvcip, self.log, self.cfg)
            self.operation.set('PW',self.desired)

            self.state = 'setting'            

        elif self.state == 'setting':
            finished, rsp = self.operation.action()

            if finished:
                self.log.info(f'JVC performed power operation and returned {rsp}')

                # now we need to verify the JVC actually did what it said
                self.operation = x0refcmd.X0RefCmd(self.jvcip, self.log, self.cfg)
                self.operation.set('PW',b'')

                self.state = 'validating'

        elif self.state == 'validating':
            finished, rsp = self.operation.action()

            if finished:
                self.log.debug(f'JVC says power state is rsp:{rsp}')

                if time.time() > self.timeout:
                    # Too much time has passed
                    # unfortuntaely there's nothing else we can do, we are giving up
                    self.log.error(f'UNABLE TO GET JVC TO CHANGE POWER STATE. rsp:{rsp}')
                    self.state = ''
                    self.desired = None

                else:
                    # 0 - standby
                    # 1 - lamp on
                    # 2 - cooling
                    # 3 - reserved (warming up?)
                    # 4 - error

                    if (rsp == b'3') or (rsp == b'2'):
                        # JVC is apparently warming up or cooling down
                        s = 'WARMING UP'
                        if rsp == b'2':
                            s = 'COOLING DOWN'
                        self.log.info(f'JVC is {s}... Waiting... Desired: {self.desired} rsp: {rsp}')

                        # now we need to verify again -- see if we come into a full mode (1-on or 0-standby)
                        self.delayValidationUntil = time.time() + 2
                        self.state = 'delay-validation'

                    elif ((self.desired == b'1' and rsp == b'1') or (self.desired == b'0' and rsp == b'0')):
                        self.log.info(f'SUCCESS!  Power state is as expected. desired:{self.desired} rsp:{rsp}')
                        self.state = ''
                        self.desired = None
                    else:
                        self.log.info(f'Inconsistent Power State, attempting to change.  desired:{self.desired} rsp:{rsp}')
                        self.state = 'delay-restart'
                        self.delayRestartUntil = time.time() + 1


        elif self.state == 'delay-validation':
            if time.time() > self.delayValidationUntil:
                self.log.debug('delay-validation complete, validating power state again')
                self.operation = x0refcmd.X0RefCmd(self.jvcip, self.log, self.cfg)
                self.operation.set('PW',b'')
                self.state = 'validating'

        elif self.state == 'delay-restart':
            if time.time() > self.delayRestartUntil:
                self.log.debug('delay-restart complete, attempting to change power state')
                self.state = 'restart'

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
            if cmd == 'on':
                self.desired = b'1'
            self.log.info(f'Asked to set Power State to {self.desired}')

            # definitely need to restart the state machine
            self.state = ''
            self.action()
