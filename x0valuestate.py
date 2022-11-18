class X0ValueState:
    """This is a class that does nothing"""

    def __init__(self, useLog):
        self.log = useLog
        self.desired = None

    def action(self):
        if self.desired == None:
            self.log.debug('X0ValueState Called when desired is still None')
            return (False,None)

        # we are done
        self.log.debug('we are done')
        return (True,self.desired)
    
    def set(self, cmd:str, data: bytearray):
        if self.desired:
            self.log.error(f'Already set X0ValueState value to {self.desired}')
        else:
            self.desired = cmd
            self.log.debug(f'Asked to set X0ValueState value to "{self.desired}"')
