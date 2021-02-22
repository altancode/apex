##
## imports
##

import socket
import select
import json

try:
    haveEvdev = True
    from evdev import InputDevice, categorize, ecodes
except ImportError:
    haveEvdev = False

##
## Code
##

class x0Keys:

    def __init__(self, useLog, inputDevice, inkeymap):
        if not haveEvdev:
            return

        self.log = useLog
        self.log.info(f'Starting up IR Keys... {inputDevice}')
        self.device = InputDevice(inputDevice)

        print(inkeymap)

        mapping = {}
        # work on the mappings
        if inkeymap:
            for key in inkeymap.keys():
                try:
                    code = eval('ecodes.' + key)
                    mapping[code] = inkeymap[key]
                except Exception as ex:
                    self.log.error(f'Unable ot map {key} {ex}')

        self.mapping = mapping
        self.log.debug(f'Mapping {self.mapping}')


    def action(self):
        if not haveEvdev:
            return []

        profiles = []

        r, _w, _x = select.select([self.device.fd], [], [], 0)
        if self.device.fd in r:
            for event in self.device.read():
                if event.type == ecodes.EV_KEY and event.value == 1:
                    # print(event.code)
                    # print(event.value)
                    self.log.debug(categorize(event))

                    if event.code in self.mapping:
                        profiles.append({'profile': self.mapping[event.code]['profile']})

        return profiles