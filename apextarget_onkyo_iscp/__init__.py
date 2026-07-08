
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
        return timeoutConfig['onkyo_iscp_ack']


    def makeCmdRetries(self, timeoutConfig):
        """Returns the number of times the command should be retried if a timeout occurs

        timeoutConfig: dictionary that can be used to retrieve the value
        """

        return 40


    # length of the fixed eISCP header (magic + header size + data size + version + reserved)
    HEADER_LEN = 16
    # the ISCP message unit prefix ("!" + unit type) followed by a 3-char command
    CMD_LEN = len(b'!1') + 3

    def _payload(self, packet):
        """Strip the eISCP framing and return the bare ISCP message (e.g. b'!1PWR01').

        Tolerates response terminators of [EOF], [EOF][CR] or [EOF][CR][LF] (the spec
        allows CR, LF or CR+LF as the end character), and any CR/LF that carried over
        from a previous packet's terminator, by locating the ISCP header rather than
        assuming fixed leading/trailing byte counts.
        """
        start = packet.find(b'ISCP')
        if start < 0:
            return b''

        # skip the fixed header, then drop the trailing EOF/CR/LF terminator
        return packet[start + self.HEADER_LEN:].rstrip(b'\x1a\r\n')


    def isMatchingAck(self, rxData, opcmd):
        """Takes a value retrieved from the devices and converts it into a value for comparision with the target

        rxData: the data retrieved from the device

        if the result of this function matches the value returned from makeTarget then this response is
        the correct response
        """

#target b'ISCP\x00\x00\x00\x10\x00\x00\x00\x08\x01\x00\x00\x00!1PWR' but
#rxData b'ISCP\x00\x00\x00\x10\x00\x00\x00\  n\x01\x00\x00\x00!1PWR00\x1a\r\n'.

        # compare the "!1" + 3-char command prefix, ignoring the parameter/terminator
        gotRest = self._payload(rxData)[:self.CMD_LEN]
        wantedRest = self._payload(opcmd)[:self.CMD_LEN]

        match = bool(gotRest) and (gotRest == wantedRest)

        if match:
            self.log.debug(f'Match!  wantedRest {wantedRest} gotRest {gotRest}')
        else:
            self.log.debug(f'NO MATCH')
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
        # strip the framing, then drop the "!1PWR" command prefix to leave the parameter

        result = self._payload(rxData)[self.CMD_LEN:]
        self.log.debug(f'makeCmdResult returning "{result}"')
        return result


def getDetails():
    details = {
        'name': 'onkyo_iscp',
        'cmdobj': X0OnkyoReceiverCmd,
        'config_ip': 'ip',
        'config_port': 'port',
        'config_timeout_ack': 'onkyo_iscp_ack',
        # every ISCP data unit ends with [EOF] (0x1a); the optional trailing CR/LF is
        # handled by _payload, so we frame on the one guaranteed terminator byte
        'delimiter': b'\x1a'
    }

    return details
