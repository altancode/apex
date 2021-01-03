##
## imports
##


##
## code
##

class X0Passthrough:
    """THe main Apex state object that does the magic"""

    def __init__(self, inComm, useLog,timeoutConfig):

        global log
        log = useLog

        self.desired = None
        self.comm = inComm
        self.state = ''

    def action(self):
        # this is where the work happens

        if self.desired == None:
            return

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

            cmd = self.desired
            log.info(f'Sending passthrough command {cmd}')
            sent = self.comm.send(cmd)
            if sent:
                self.state = ''
                self.desired = None

                self.comm.close()
        
       

    def set(self, inDesired):
        self.desired = inDesired
        log.info(f'Asked to send passthrough {self.desired}')

        self.comm.close()
        self.state = ''

        self.action()
