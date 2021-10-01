##
## imports
##

from abc import ABC, abstractmethod
import time
import misc

##
## code
##

class X0GenericCmd(ABC):
    """The main Apex state object that does the magic"""

    def __init__(self, inComm, useLog, timeoutConfig, closeOnComplete = True):

        self.log = useLog
        self.desired = None
        self.comm = inComm
        self.state = ''
        self.timeout = 0
        self.refAckOffset = self.makeAckOffset(timeoutConfig)
        self.cmdRetries = self.makeCmdRetries(timeoutConfig)
        self.checkwaitacktimeout = 0
        self.opcmd = b''
        self.chatty = False
        self.target = None
        self.closeOnComplete = closeOnComplete

        self.log.debug(f'refAckOffset {self.refAckOffset}, cmdRetries {self.cmdRetries}')


    @abstractmethod
    def makeDesired(self, cmd, data):
        """ Returns the internal encoding of the command and data 
        
        cmd: the requested command
        data: the data releated to the command
        """
        pass


    @abstractmethod
    def makeOpCmd(self):
        """Takes the self.desired parameter and makes a command that can be sent to the remote device
        
        Sometimes this simply adds a CR or LF to the self.desired
        Other times more complex headers, etc. will be needed

        """
        pass

    @abstractmethod
    def makeAckOffset(self, timeoutConfig):
        """Return a timeout in seconds for how long we should wait before receiving an Ack

        timeoutConfig: dictionary that can be used to retrieve the timeout
        """
        pass

    @abstractmethod
    def makeCmdRetries(self, timeoutConfig):
        """Returns the number of times the command should be retried if a timeout occurs

        timeoutConfig: dictionary that can be used to retrieve the value
        """
        pass


    @abstractmethod
    def isMatchingAck(self, rxData, opcmd):
        """Takes a value retrieved from the devices and converts it into a value for comparision with the target

        rxData: the data retrieved from the device

        if the result of this function matches the value returned from makeOpCmd then this response is
        the correct response
        """
        pass

    @abstractmethod
    def makeCmdResult(self, rxData):
        """When a matching response is found this function will convert it into the values returned to the caller
        
        rxData: the data received from the device
        
        """
        pass


    def action(self):
        # this is where the work happens

        if self.state == '':
            self.log.debug(f'Inside state "{self.state}" {self.checkwaitacktimeout}')

            self.opcmd = self.makeOpCmd()

            self.state = 'waitACK'
            print(f'Setting timeout')
            self.timeout = time.time() + self.refAckOffset    

            self.state = 'sendCmd'

        ## this is intentionally an if and not an elif
        ## we want the code above to potentially trigger this code below

        if self.state == 'sendCmd':
            self.log.debug(f'Inside state "{self.state}" {self.checkwaitacktimeout}')

            self.log.debug(f'Sending command {self.opcmd}')

            # send the command
            ok = self.comm.send(self.opcmd)
            print(f'OK is {ok}')
            if not ok:
                # do not move to next state!
                # basically we'll try again next time
                self.log.debug(f'Could not send command')
                if time.time() > self.timeout:
                    # oops.  Start over
                    self.log.debug(f'Trying to send Timeout in {self.state}.  {self.checkwaitacktimeout}.  Starting over')
                    self.state = ''

                    self.checkwaitacktimeout += 1
                    if self.checkwaitacktimeout > self.cmdRetries:
                        # we just give up
                        self.log.warning(f'Giving up...')
                        self.desired = None
                        self.checkwaitacktimeout = 0

            else:
                # it was sent
                self.state = 'waitACK'
#                self.timeout = time.time() + self.refAckOffset
        
        elif self.state == 'waitACK':
            self.log.debug(f'Inside state "{self.state}" {self.checkwaitacktimeout}')

            # quick test of whether socket is connected
            ok = self.comm.send(b'')
            if not ok:
                # no socket even after send tried to create one
                self.log.debug(f'connection lost and not ready yet.  Restarting...')

                # got nothing.  Have we timed out?
                if time.time() > self.timeout:
                    # oops.  Start over
                    self.log.debug(f'Connection Loss and Timeout in {self.state}.  {self.checkwaitacktimeout}.  Starting over')
                    self.state = ''

                    self.checkwaitacktimeout += 1
                    if self.checkwaitacktimeout > self.cmdRetries:
                        # we just give up
                        self.log.warning(f'Giving up...')
                        self.desired = None
                        self.checkwaitacktimeout = 0
                else:
                    self.state = 'sendCmd'


            # sent ok
            else:
                # see if there's a response
                rxData = self.comm.read()

                if rxData == b'':
                    self.log.debug(f'Got no data')
                    # got nothing.  Have we timed out?
                    if time.time() > self.timeout:
                        # oops.  Start over
                        self.log.debug(f'Timeout in {self.state}.  {self.checkwaitacktimeout}.  Starting over')
                        self.state = ''

                        self.checkwaitacktimeout += 1
                        if self.checkwaitacktimeout > self.cmdRetries:
                            # we just give up
                            self.log.warning(f'Giving up...')
                            self.desired = None
                            self.checkwaitacktimeout = 0

                else:
                    self.log.debug(f'Got data {rxData}')
                    # we got something
                    self.checkwaitacktimeout = 0

                    if self.isMatchingAck(rxData,self.opcmd):
                        # got the ack
                        self.log.debug(f'Got the ACK {rxData}')

                        self.state = ''
                        self.desired = None

                        result = self.makeCmdResult(rxData)

                        if self.closeOnComplete:
                            self.log.debug(f'closing connection because closeOnComplete is {self.closeOnComplete}')
                            self.comm.close()

                        return (True, result)

                    else:
                        # what happened?
                        self.log.warning(f'Did not receive expected results with {rxData}.  Ignoring...')

        else:
            self.log.error('**** YIKES {self.state}')
            

        if not self.desired:
            # we are done
            if self.closeOnComplete:
                self.log.debug(f'closing connection because closeOnComplete is {self.closeOnComplete}')
                self.comm.close()

            # return that we are done with no result
            return (True,None)
        else:
            # more to do
            return (False,None)


    def set(self, cmd:str, data: bytearray):
        
#        print(f'cmd is {cmd}')
#        print(f'data is {data}')

        combined = self.makeDesired(cmd,data)
#        combined = bytes(cmd,'utf-8') + b' ' + data
#        print(f'combined {combined}')
        if self.desired:
            # same mode
            self.log.warning(f'!!!! Already sending command {combined}')
        else:
            self.desired = combined
            self.log.debug(f'Asked to send command {combined}')

            # definitely need to restart the state machine
            self.state = ''
            self.action()






