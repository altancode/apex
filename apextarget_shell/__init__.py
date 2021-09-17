
import os
import sys
import shlex
import subprocess
import time

# we need to adjust the path so we can include from the parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath('..'))))
import x0genericcmd

class X0ShellCmd(x0genericcmd.X0GenericCmd):
    """Command that launches a Shell"""

    def __init__(self, inComm, useLog, timeoutConfig, closeOnComplete = True):

        self.log = useLog
        self.desired = None
        self.state = ''
        self.timeout = 0
        self.opcmd = b''
        self.target = None
        self.sp = None
        self.refAckOffset = self.makeAckOffset(timeoutConfig)


    def makeDesired(self, cmd, data):
        """ Returns the internal encoding of the command and data 
        
        cmd: the requested command
        data: the data releated to the command
        """

        ## we don't use this
        pass


    def makeOpCmd(self):
        """Takes the self.desired parameter and makes a command that can be sent to the remote device
        
        Sometimes this simply adds a CR or LF to the self.desired
        Other times more complex headers, etc. will be needed

        """

        args = shlex.split(self.desired.decode('ascii'))
        self.log.debug(f'makeOpCmd returning {args}')
        return args


    def makeAckOffset(self, timeoutConfig):
        """Return a timeout in seconds for how long we should wait before receiving an Ack

        timeoutConfig: dictionary that can be used to retrieve the timeout
        """

        to = timeoutConfig.get('shell_ack', 5)
        self.log.debug(f'makeAckOffset returning {to}')
        return to


    def makeCmdRetries(self, timeoutConfig):
        """Returns the number of times the command should be retried if a timeout occurs

        timeoutConfig: dictionary that can be used to retrieve the value
        """

        retries = timeoutConfig.get('shell_retries', 1)
        self.log.debug(f'makeCmdRetries returning {retries}')
        return retries



    def isMatchingAck(self, rxData, opcmd):
        """Takes a value retrieved from the devices and converts it into a value for comparision with the target

        rxData: the data retrieved from the device

        if the result of this function matches the value returned from makeOpCmd then this response is
        the correct response
        """

        # we don't use this
        pass


    def makeCmdResult(self, rxData):
        """When a matching response is found this function will convert it into the values returned to the caller
        
        rxData: the data received from the device
        
        """

        # we don't use this
        pass


    def action(self):
        # this is where the work happens

        if self.state == '':
            self.log.debug(f'Inside state "{self.state}"')

            self.opcmd = self.makeOpCmd()

            self.state = 'waitACK'
            self.timeout = time.time() + self.refAckOffset    

            self.state = 'sendCmd'

        ## this is intentionally an if and not an elif
        ## we want the code above to potentially trigger this code below

        if self.state == 'sendCmd':
            self.log.debug(f'Inside state "{self.state}"')

            # https://docs.python.org/3/library/subprocess.html#subprocess.Popen

            try:
                self.log.debug(f'calling subprocess Popen with {self.opcmd}')
                self.sp = subprocess.Popen(self.opcmd)

                # it was started
                self.state = 'waitACK'

            except Exception as ex:
                self.log.debug(f'Exception from Popen {ex}')

                # we just give up
                self.log.warning(f'Giving up...')
                self.desired = None

        
        elif self.state == 'waitACK':
            self.log.debug(f'Inside state "{self.state}"')

            # quick test of whether socket is connected
            done = self.sp.poll() != None

            if done:
                # subprocess ended
                self.log.debug(f'Subprocess ended with {done}')
                self.state = ''
                self.desired = None

            else:
                # not done
                if time.time() > self.timeout:
                    # Waited too long
                    self.log.warning(f'Shell Timeout in {self.state}, killing subprocess')
                    self.sp.kill()

                    self.state = ''
                    self.desired = None
            

        if not self.desired:
            # we are done
            # return that we are done with no result
            return (True,None)
        else:
            # more to do
            return (False,None)


    def set(self, cmd, data):
        
        combined = bytes(cmd,'utf-8') + b' ' + data

        if self.desired:
            # same mode
            self.log.error(f'**** Already sending command {combined}')
        else:
            self.desired = combined
            self.log.debug(f'Asked to send command {combined}')

            # definitely need to restart the state machine
            self.state = ''
            self.action()




def getDetails():
    """ returns details about this Apex Target plugin, allowing Apex to use this functionality
    """
    details = {
        'name': 'shell',
        'cmdobj': X0ShellCmd,
        'config_ip': None,
        'config_port': None,
        'config_timeout_ack': None,
        'delimiter': None
    }

    return details
