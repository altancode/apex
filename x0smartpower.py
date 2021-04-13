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
        self.attempts = 0
        self.waitValidation = 0


    def action(self):

        # 1. Sent Power State
        # 2. Validate Power State
        # 3. Not not correct state, go back to 1

        # state is
        # '' 
        # 'setting'
        # 'validating'
        # 'delay'

        if not self.desired:
            self.log.debug('Called with nothing to do')

            # True means nothing more to do
            return True

        if self.state == '':
            self.log.debug(f'State "{self.state}" {self.attempts}')
            self.log.info(f'First checking whether JVC power state is {self.desired}')
            self.timeout = time.time() + self.timeoutOffset
            self.operation = x0refcmd.X0RefCmd(self.jvcip, self.log, self.cfg)
            self.operation.set('PW',b'')
            self.state = 'validating'

        if self.state == 'restart':
            self.log.debug(f'State "{self.state}" {self.attempts}')

            if self.attempts > 2:
                self.log.warning(f'Too many attempts ({self.attempts}) to set power correctly.   Giving up.')
                self.desired = None
                self.state = ''
            else:
                self.log.info(f'Telling JVC to set power state to {self.desired}')

                # need to make a opcmd
                self.timeout = time.time() + self.timeoutOffset
                self.operation = x0opcmd.X0OpCmd(self.jvcip, self.log, self.cfg)
                self.operation.set('PW',self.desired)

                self.state = 'setting'            

        elif self.state == 'setting':

            finished, rsp = self.operation.action()

            if finished:
                self.log.info(f'JVC performed power operation and returned {rsp}')

                # now we need to verify
                self.operation = x0refcmd.X0RefCmd(self.jvcip, self.log, self.cfg)
                self.operation.set('PW',b'')

                self.state = 'validating'

        elif self.state == 'validating':

            finished, rsp = self.operation.action()

            if finished:
                self.log.debug(f'JVC verified the power state is {rsp}')

                if time.time() > self.timeout:
                    # timeout occurred
                    self.log.debug('Timeout occurred in validating')
                    self.state = 'delay-restart'
                    # no extra delay below
                    self.waitUntil = time.time()

                else:
                    # 0 - standby
                    # 1 - lamp on
                    # 2 - cooling
                    # 3-  reserved (warming up?)

                    # if (self.desired == b'1' and rsp == b'3') or \
                    #     (self.desired == b'0' and rsp == b'2'):
                    if (rsp == b'3') or (rsp == b'2'):
                        # JVC is apparently warming up or cooling down
                        s = 'warming up'
                        if rsp == b'2':
                            s = 'cooling down'
                        self.log.debug(f'JVC is apparently {s}... Waiting... {self.desired} {rsp}')

                        # now we need to verify agian -- see if we come into full on mode
                        self.waitValidation = time.time() + 2
                        self.state = 'delay-validation'

                    else:
                        jvcIsOn = (rsp == b'1')
                        if ((self.desired == b'1' and jvcIsOn) or (self.desired == b'0' and (not jvcIsOn))):
                            self.log.info(f'Power state is as expected {self.desired} {rsp}')
                            self.state = ''
                            self.desired = None
                        else:
                            self.log.info(f'Inconsistent Power State (will try again) {self.desired} {rsp}')
                            self.state = 'delay-restart'
                            self.waitUntil = time.time()

        elif self.state == 'delay-validation':
            if time.time() > self.waitValidation:
                self.log.debug('delay-validation complete, attempting validation again')
                self.operation = x0refcmd.X0RefCmd(self.jvcip, self.log, self.cfg)
                self.operation.set('PW',b'')
                self.state = 'validating'

        elif self.state == 'delay-restart':
            if time.time() > self.waitUntil:
                self.log.debug('delay-restart complete, attempting again')
                self.attempts += 1
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
            self.attempts = 0
            self.state = ''
            self.action()
