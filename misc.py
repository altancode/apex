##
## code
## 

pmLookup = {
    b'00': 'Film',
    b'01': 'Cinema',
    b'02': 'Animation',
    b'03': 'Natural',
    b'04': 'HDR10'
    b'06': 'THX',
    b'0B': 'FrameAdaptHDR'
    b'0C': 'User1',
    b'0D': 'User2',
    b'0E': 'User3',
    b'0F': 'User4',
    b'10': 'User5',
    b'11': 'User6',
    b'14': 'HLG',
    b'16': 'PanaPQ'
}

def getPictureMode(bin):
    if bin in pmLookup:
        return pmLookup[bin]
    else:
        return 'Unknown' + bin.decode('ascii')