class X0HDFuryMode:
    """Class to set and report the HDFury follow mode"""

    def __init__(self, useLog):
        self.log = useLog
        self.desired = None
        self.mode = 'follow'

    def action(self):
        if not self.desired:
            self.log.debug('Called with nothing to do')
            return True

        self.mode = self.desired
        self.log.info(f'HDFury mode changed to {self.mode}')

        # we are done
        return (True,self.mode)
    
    def set(self, cmd:str, data: bytearray):
        if self.desired:
            self.log.error(f'Already set HDFuryMode to {self.desired}')
        else:
            self.desired = 'follow'
            if cmd == 'ignore':
                self.desired = 'ignore'
            self.log.info(f'Asked to set HDFuryMode {self.desired}')

            self.action()