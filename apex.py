##
## imports
##

import argparse
import time
import yaml
import logging
from logging.handlers import RotatingFileHandler
import x0state
import x0ip
import x0serial
import x0state
import misc

##
## globals
##

log = None

##
## code
##

def processLoop(cfg, jvcip, vtxser, state):
    """Main loop which recevies HDFury data and intelligently acts upon it"""

    while True:
        try:
            state.action()

            rxData = vtxser.read()

            if rxData != b'':
                # we got something
                log.debug(f'HDFury said "{rxData}"')

                example = b'!\x89\x01PMPM'
                if len(rxData) >= len(example) and rxData[0:len(example)] == example:
                    pm = rxData[7:9]
                    log.info(f'HDFury said to activate picture mode {misc.getPictureMode(pm)} ({pm})')
                    state.set(pm)
                else:
                    log.error(f'Ignoring {rxData} {rxData[0:len(example)]} {example}')

        except Exception as ex:
            log.error(f'Big Problem Exception {ex}')
            time.sleep(10)


def apexMain():
    """"Setup looging, connectivity and call main processing loop"""

    global log

    formatter = logging.Formatter('%(asctime)s - %(message)s')
    formatter.default_msec_format = '%s.%03d'
    log = logging.getLogger("jvcx0")
    log.setLevel(logging.DEBUG)

    # for files
    handler = RotatingFileHandler('./apex.log', maxBytes=500*1024, backupCount=5)
    handler.setFormatter(formatter)
    log.addHandler(handler)

    # for stderr
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    handler.setLevel(logging.INFO)
    log.addHandler(handler)

    log.info(f'Apex started...')

    parser = argparse.ArgumentParser()
    parser.add_argument("--showserialports", "-ssp", help="List available serial ports")

    args = parser.parse_args()

    if args.showserialports:
        x0serial.showSerialPorts()
        return

    # read config
    with open('apex.yaml') as file:
        cfg = yaml.full_load(file)

    if not 'timeouts' in cfg:
        cfg['timeouts']['hdfuryRead'] = 0.25
        cfg['timeouts']['jvcIP'] = 0.25
        cfg['timeouts']['jvcRefAck'] = 0.25
        cfg['timeouts']['jvcDefault'] = 2
        cfg['timeouts']['jvcOpAck'] = 20

    log.info(f'Using config {cfg}')

    jvcip = x0ip.X0IP((cfg['jvcip'],cfg['jvcport']), log, cfg['timeouts'])
    jvcip.connect()

    vtxser = x0serial.X0Serial(cfg['hdfury'], log, cfg['timeouts'])
    vtxser.connect()

    state = x0state.X0State(jvcip, log, cfg['timeouts'])

    # this never returns
    processLoop(cfg, jvcip, vtxser, state)


if __name__ == "__main__":
    apexMain()
