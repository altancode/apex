
import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath('..'))))

import x0genericcmd


class X0OnkyoReceiverCmd(x0genericcmd.X0GenericCmd):
    """
    Implements the communications for Onkyo Receivers
    """

    def makeDesired(self, cmd, data):
        """ Returns the internal encoding of the command and data 
        
        cmd: the requested command
        data: the data related to the command
        """

        desired = bytes(cmd,'utf-8') + data
        self.log.debug(f'makeDesired returning "{desired}"')

        return desired


    def makeOpCmd(self):
        """Takes the self.desired parameter and makes a command that can be sent to the remote device
        
        Sometimes this simply adds a CR or LF to the self.desired
        Other times more complex headers, etc. will be needed

        """
        eiscp = b'!1' + self.desired + b'\n'
        datasize = len(eiscp)
        header = b'ISCP' + b'\x00\x00\x00\x10' + datasize.to_bytes(4, 'big') + b'\01' + b'\00\00\00'

        opcmd = header + eiscp

        self.log.debug(f'makeOpCmd returning "{opcmd}"')

        return opcmd


    def makeAckOffset(self, timeoutConfig):
        """Return a timeout in seconds for how long we should wait before receiving an Ack

        timeoutConfig: dictionary that can be used to retrieve the timeout
        """
        return timeoutConfig['hdfury_generic_ack']


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

#target b'ISCP\x00\x00\x00\x10\x00\x00\x00\x08\x01\x00\x00\x00!1PWR' but 
#rxData b'ISCP\x00\x00\x00\x10\x00\x00\x00\  n\x01\x00\x00\x00!1PWR00\x1a\r\n'.

        match = False

        # first drop the last 3 bytes from the rxData as this is EOL+CR+LF and we don't need to compare it
        rxData = rxData[:-3]

        # verify first 8 bytes match
        # this is the ISCP and the fixed header size
        if rxData[:8] == opcmd[:8]:
            # they match
            #wantedLen = int.from_bytes(opcmd[8:12],'big')
            #gotLen = int.from_bytes(rxData[8:12],'big')

            # turns out there's no need to compare the lengths
            #log.debug(f'wantedLen {wantedLen}, gotLen {gotLen}')
            # the rxData always has an addition LF and EOF so we subtract 2

            wantedRest = opcmd[16:21]
            gotRest = rxData[16:21]

            match = (wantedRest == gotRest)

            if match:
                self.log.debug(f'Match!  wantedRest {wantedRest} gotRest {gotRest}')


        if not match:
            self.log.debug(f'NO MATCH on lengths')
            self.log.debug(f'rxData {rxData}')
            self.log.debug(f'opcmd  {opcmd}')

        self.log.debug(f'isMatchingAck returning {match}')
        return match


    def makeCmdResult(self, rxData):
        """When a matching response is found this function will convert it into the values returned to the caller
        
        rxData: the data received from the device
        
        """

        # example
        # b'ISCP\x00\x00\x00\x10\x00\x00\x00\n\x01\x00\x00\x00!1PWR01\x1a\r\n
        # all the beginning is fixed
        # we remove the last 3 because it's an EOF CR and LF

        result = rxData[21:-3]
        self.log.debug(f'makeCmdResult returning "{result}"')
        return result


def getDetails():
    details = {
        'name': 'onkyo_iscp',
        'cmdobj': X0OnkyoReceiverCmd,
        'config_ip': 'ip',
        'config_port': 'port',
        'config_timeout_ack': 'onkyo_iscp_ack',
        'delimiter': b'\x1a\r\n'
    }

    return details
