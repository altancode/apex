
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath('..'))))

import x0genericcmd

print('I WAS CALLED')

class X0HDFuryVertex2Cmd(x0genericcmd.X0GenericCmd):
    """
    Implements the communications for the HDFury Vertex
    """

    def makeDesired(self, cmd, data):
        """ Returns the internal encoding of the command and data 
        
        cmd: the requested command
        data: the data releated to the command
        """

        return bytes(cmd,'utf-8') + b' ' + data

    def makeOpCmd(self):
        """Takes the self.desired parameter and makes a command that can be sent to the remote device
        
        Sometimes this simply adds a CR or LF to the self.desired
        Other times more complex headers, etc. will be needed

        """
        return self.desired + b'\x0a'

    def makeAckOffset(self, timeoutConfig):
        """Return a timeout in seconds for how long we should wait before receiving an Ack

        timeoutConfig: dictionary that can be used to retrieve the timeout
        """
        return timeoutConfig['hdfury_vertex2_ack']

    def makeCmdRetries(self, timeoutConfig):
        """Returns the number of times the command should be retried if a timeout occurs

        timeoutConfig: dictionary that can be used to retrieve the value
        """

        return 40

    def isMatchingAck(self, rxData, opcmd):
        """Takes a value retrieved from the devices and converts it into a value for comparision with the target

        rxData: the data retrieved from the device

        if the result of this function matches the value returned from makeTarget then this response is
        the correct response
        """

        # remove any CR or LF
        rxData = rxData.replace(b'\n',b'')
        rxData = rxData.replace(b'\r',b'')
        opcmd = opcmd.replace(b'\n',b'')
        opcmd = opcmd.replace(b'\r',b'')

        rx = rxData.split(b' ')[0]
        op = opcmd.split(b' ')[1]

        match = rx = op
        if match:
            self.log.debug('Match!')

        self.log.debug(f'\nrx {rx}\nop {op}')

        return rx == op

    def makeCmdResult(self, rxData):
        """When a matching response is found this function will convert it into the values returned to the caller
        
        rxData: the data received from the device
        
        """
        result = b''.join(rxData.split(b' ')[1:])
        result = result.replace(b'\r\n',b'')
        return result

def getDetails():
    details = {
        'name': 'hdfury_vertex2',
        'cmdobj': X0HDFuryVertex2Cmd,
        'config_ip': 'hdfuryip',
        'config_port': 'hdfuryport',
        'config_timeout_ack': 'hdfury_vertex2_ack',
        'delimiter': b'\n'
    }

    return details
