class X0GammaDState:
    """Class to set and report the GammaD tracking"""

    def __init__(self, useLog):
        self.log = useLog
        self.desired = None
        self.mode = ''

    def action(self):
        if self.desired == None:
            self.log.debug('Called with nothing to do')
            return (True,self.mode)

        self.mode = self.desired
        self.log.debug(f'OnGammaD profile changed to "{self.mode}"')

        self.desired = None

        # we are done
        return (True,self.mode)
    
    def set(self, cmd:str, data: bytearray):
        if self.desired:
            self.log.error(f'Already set OnGammaD profile to {self.desired}')
        else:
            self.desired = cmd
            self.log.debug(f'Asked to set OnGammaD profile to "{self.desired}"')
