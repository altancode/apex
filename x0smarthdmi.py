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

class X0SmartHDMI:
    """Change HDMI and ensure it changes"""

    def __init__(self, inComm, useLog, timeoutConfig):

        self.log = useLog
        self.cfg = timeoutConfig
        self.desired = None
        self.jvcip = inComm
        self.state = ''
        self.timeout = 0
        self.opAckOffset = timeoutConfig['jvcOpAckProfile']
        self.operation = None


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
            self.log.debug(f'State "{self.state}" ')

            self.log.info(f'Checking if HDMI is {self.desired}')

            self.operation = x0refcmd.X0RefCmd(self.jvcip, self.log, self.cfg)
            self.operation.set('IP',b'')

            self.state = 'validating'

        elif self.state == 'validating':

            finished, rsp = self.operation.action()

            if finished:
                self.log.info(f'JVC verified HDMI is {rsp}')

                # 6 - HDMI1
                # 7 - HDMI2
                if (self.desired == b'6' and rsp == b'6') or (self.desired == b'7' and rsp == b'7'):
                    self.log.info(f'No need to change since HDMI state is correct already {self.desired} {rsp}')
                    self.state = ''
                    self.desired = None
                else:
                    self.log.info(f'Need to change HDMI state {self.desired} {rsp}')

                    self.operation = x0opcmd.X0OpCmd(self.jvcip, self.log, self.cfg)
                    self.operation.set('IP',self.desired)

                    self.state = 'setting'            

        elif self.state == 'setting':

            finished, rsp = self.operation.action()

            if finished:
                self.log.info(f'JVC performed HDMI operation and returned {rsp}')

                self.state = ''
                self.desired = None

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
            self.desired = b'6'
            if cmd == '2':
                self.desired = b'7'
            self.log.info(f'!!!! Asked to set HDMI State to {self.desired}')

            # definitely need to restart the state machine
            self.state = ''
            self.action()
