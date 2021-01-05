##
## imports
##

import time
import misc

##
## code
##

class X0State:
    """THe main Apex state object that does the magic"""

    def __init__(self, inComm, useLog,timeoutConfig, closeOnComplete):

        global log
        log = useLog

        self.desired = None
        self.comm = inComm
        self.state = ''
        self.timeout = 0
        self.refAckOffset = timeoutConfig['jvcRefAck']
        self.defaultOffset = timeoutConfig['jvcDefault']
        self.opAckOffset = timeoutConfig['jvcOpAck']
        self.nextdata = b''
        self.checkwaitacktimeout = 0
        self.opcmd = b''
        self.closeOnComplete = closeOnComplete
        self.keepaliveOffset = 5
        self.nextKeepalive = time.time() + self.keepaliveOffset
        self.chatty = False


    def action(self):
        # this is where the work happens
#        log.debug(f'Action called in state "{self.state}" with desired {self.desired}')

        if self.desired == None:
            # enoty stuff we don't want, such as stale responses or keep alive ack
            self.comm.read(emptyIt = True)

            # check if keepalive time
            if time.time() > self.nextKeepalive:
                # it is!
                cmd = b'!\x89\x01\x00\x00\n'
                if self.chatty:
                    log.debug(f'Sending keep alive {cmd}')
                ok = self.comm.send(cmd)
                if not ok:
                    log.warning(f'Unable to send keep alive')
        
                self.nextKeepalive = time.time() + self.keepaliveOffset

            return

        # '' means nothing is going on
        # 'checkwaitack' means we have sent a Reference command and are waiting for the ack response
        # 'checkwaitdata' mean we received the ack but are now waiting for the actual data
        # 'setdataack' means we sent a command to change the state and are waiting the ack

        if self.state == '':
            # no unexpected data coming from source so we start
            log.debug(f'Inside state "{self.state}"')

            cmd = b'?\x89\x01PMPM\n'
            log.info(f'Requesting current picture mode')
            log.debug(f'Sending REFERENCE command {cmd}')
            ok = self.comm.send(cmd)
            if not ok:
                # do not move to next state!
                # basically we'll try again next time
                log.debug(f'Could not send refernece command')
            else:
                # it was sent
                self.state = 'checkwaitack'
                self.timeout = time.time() + self.refAckOffset
        
        elif self.state == 'checkwaitack':
            log.debug(f'Inside state "{self.state}"')

            # quick test of whether socket is connected
            ok = self.comm.send(b'')
            if not ok:
                # no socket even after send tried to create one
                log.debug(f'JVC connection lost and not ready yet.  Restarting...')

                self.state = ''

            else:
                # see if there's a response
                rxData = self.comm.read()

                if rxData == b'':
                    log.debug(f'Got no data')
                    # got nothing.  Have we timed out?
                    if time.time() > self.timeout:
                        # oops.  Start over
                        log.debug(f'Timeout in {self.state}.  {self.checkwaitacktimeout}.  Starting over')
                        self.state = ''

                        self.checkwaitacktimeout += 1
                        if self.checkwaitacktimeout > 40:
                            # we just give up
                            # projector powered off?
                            log.warning(f'Giving up... JVC powered off?')
                            self.desired = None
                            self.checkwaitacktimeout = 0

                            ##
                            ## maybe disconnect and reconnect here?
                            ##

                else:
                    log.debug(f'Got data {rxData}')
                    # we got something
                    self.checkwaitacktimeout = 0

                    exp = b'\x06\x89\x01PM\x0A'
                    l = len(exp)
                    if len(rxData) >= l and rxData[0:l] == exp:
                        # got the ack
                        log.info(f'Got the Picture Mode reference ACK')
                        self.nextdata = rxData[l:]
                        log.debug(f'Set nextdata to {self.nextdata}')
                        self.state = 'checkwaitdata'
                        self.timeout = time.time() + self.defaultOffset

                    else:
                        # what happened?
                        log.debug(f'{l} {rxData[0:l]}')
                        log.warning(f'Wanted {exp} but got {rxData}.  Starting over')
                        self.state = ''

        elif self.state == 'checkwaitdata':
            log.debug(f'Inside state "{self.state}"')

            # see if there's a response
            if self.nextdata == b'':
                rxData = self.comm.read()
            else:
                log.debug(f'Using next data {self.nextdata}')
                rxData = self.nextdata
                self.nextdata = b''

            if rxData == b'':
                # got nothing.  Have we timed out?
                if time.time() > self.timeout:
                    # oops.  Start over
                    log.debug(f'Timeout in {self.state}.   Starting over')
                    self.state = ''

            else:
                # check if it's the stuff jvc sends when processing is taking a whike?
                # this may not really be needed
                if rxData == b'\x06\x89\x01PM\n':
                    # extend timeout
                    log.warning(f'extending timeout...')
                    self.timeout = time.time() + self.defaultOffset

                else:
                    # we got something
                    exp = b'@\x89\x01PM'
                    if len(rxData) > len(exp) and exp[0:5] == rxData[0:5]:
                        # looks good
                        # got the data.  Is it different?

                        pjstate = rxData[5:7]
                        if pjstate == self.desired:
                            # already in this state
                            log.info(f'**** Already set to desired picture mode {misc.getPictureMode(self.desired)} {self.desired}')
                            self.state = ''
                            self.desired = None

                            ## lets try closing the socket so it's opened next time
                            ## May help with unwanted delays when JVC closes the socket
                            if self.closeOnComplete:
                                self.comm.close()

                        else:
                            # start the command to change the state
                            log.info(f'**** Attempting to change picture mode to {misc.getPictureMode(self.desired)} {self.desired}')

                            # ex: "b'!\x89\x01PMPM0D\n'"
                            cmd = b'!\x89\x01PMPM'
                            cmd += self.desired + b'\n'
                            log.debug(f'Sending Operation command {cmd}')
                            self.opcmd = cmd
                            ok = self.comm.send(cmd)
                            if not ok:
                                log.warning(f'Send failed in {self.state}.   Consider optimisation')

                            self.state = 'setdataack'
                            self.timeout = time.time() + self.opAckOffset


                    else:
                        # what happened?
                        log.warning(f'Wanted {exp} but got {rxData}.  Starting over')
                        self.state = ''

        elif self.state == 'setdataack':
            log.debug(f'Inside state "{self.state}"')

            # see if there's a response
            rxData = self.comm.read()

            if rxData == b'':
                # got nothing.  Have we timed out?
                if time.time() > self.timeout:
                    # oops.  Start over
                    log.debug(f'Timeout in {self.state}.   Starting over')
                    self.state = ''

                ## try sending the opcmd
                log.debug('Sending opcmd again')
                ok = self.comm.send(self.opcmd)
                if not ok:
                    log.warning(f'Send failed in {self.state}.   Consider optimisation')

            else:
                # we got something
                exp = b'\x06\x89\x01PM\x0A'
                if rxData == exp:
                    # got the ack
                    log.debug(f'Got the ACK')

                    ##
                    ## SUCCESS!
                    ##
                    log.info(f'**** Picture Mode successfully changed to {misc.getPictureMode(self.desired)} {self.desired}')
                    self.state = ''
                    self.desired = None

                    ## lets try closing the socket so it's opened next time
                    ## May help with unwanted delays when JVC closes the socket
                    if self.closeOnComplete:
                        self.comm.close()

                else:
                    # what happened?
                    log.warning(f'Wanted {exp} but got {rxData}.  Starting over')
                    self.state = ''


        else:
            log.error('**** YIKES {self.state}')
       

    def set(self, inDesired):
        
        if inDesired == self.desired:
            # same mode
            log.info(f'!!!! Desired picture mode is same as previouos {misc.getPictureMode(self.desired)} {self.desired}')
        else:
            self.desired = inDesired
            log.info(f'!!!! Desired picture mode is now {misc.getPictureMode(self.desired)} {self.desired}')

            ## getting this while waiting for results may be an indication
            ## that the JVC will NOT respond
            ## so let's try restarting our state machine
#            self.comm.close()

            # definitely need to restart the state machine
            self.state = ''
            self.action()
