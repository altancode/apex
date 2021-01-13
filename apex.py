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
import x0passthrough

##
## globals
##

log = None

##
## code
##

def processLoop(cfg, jvcip, vtxser, state, usePassthrough, slowdown):
    """Main loop which recevies HDFury data and intelligently acts upon it"""

    while True:
        try:

            if slowdown > 0:
                log.warning(f'Slowdown of {slowdown} enabled...')
                time.sleep(slowdown)

            state.action()

            rxData = vtxser.read()

            if rxData != b'':
                # we got something
                log.debug(f'HDFury said "{rxData}"')

                if usePassthrough:
                    # just pass it on
                    state.set(rxData)
                else:
                    # only support picture mode for intelligent operation
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

    formatter = logging.Formatter('%(asctime)s [%(levelname)s]: %(message)s')
    formatter.default_msec_format = '%s.%03d'
    log = logging.getLogger("jvcx0")
    log.setLevel(logging.DEBUG)

    # for stderr
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    handler.setLevel(logging.INFO)
    log.addHandler(handler)

    parser = argparse.ArgumentParser()
    parser.add_argument("--showserialports", "-ssp", action='store_true', help="List available serial ports")
    parser.add_argument("--configfile", "-cf", help="Specify location of configuration file")
    parser.add_argument("--passthrough", "-pt", action='store_true', help="Operate in passthrough mode")
    parser.add_argument("--logfile", "-lf", help="Specify log file location")

    args = parser.parse_args()

    logFile = './apex.log'
    if args.logfile:
        # user has specified a locaiton for the logging
        logFile = args.logfile

    # now that we have the log file name, we setup file logging
    handler = RotatingFileHandler(logFile, maxBytes=500*1024, backupCount=5)
    handler.setFormatter(formatter)
    log.addHandler(handler)

    log.info(f'Using log file {logFile}')

    if args.showserialports:
        # show the serial ports and exit
        x0serial.showSerialPorts()
        return

    cfgName = 'apex.yaml'
    if args.configfile:
        # user has specified a locaiton for the config file
        cfgName = args.configfile
    log.info(f'Using config located {cfgName}')

    usePassthrough = False
    if args.passthrough:
        usePassthrough = True

    # read config
    with open(cfgName) as file:
        cfg = yaml.full_load(file)

    if not 'timeouts' in cfg:
        cfg['timeouts'] = {}
        cfg['timeouts']['hdfuryRead'] = 0.1
        cfg['timeouts']['jvcIP'] = 0.25
        cfg['timeouts']['jvcRefAck'] = 0.25
        cfg['timeouts']['jvcDefault'] = 2
        cfg['timeouts']['jvcOpAck'] = 30

    if not 'closeOnComplete' in cfg:
        cfg['closeOnComplete'] = False

    if not 'slowdown' in cfg:
        cfg['slowdown'] = 0

    log.info(f'Apex started...')
    log.info(f'Using config {cfg}')
    if usePassthrough:
        log.info('Operating in EXPERIMENTAL passthrough mode')

    jvcip = x0ip.X0IP((cfg['jvcip'],cfg['jvcport']), log, cfg['timeouts'])
    jvcip.connect()

    vtxser = x0serial.X0Serial(cfg['hdfury'], log, cfg['timeouts'])
    try:
        vtxser.connect()
    except Exception as ex:
        log.error(f'Exception while accessing serial port ("{ex}"')
        return

    if not usePassthrough:
        state = x0state.X0State(jvcip, log, cfg['timeouts'], cfg['closeOnComplete'])
    else:
        state = x0passthrough.X0Passthrough(jvcip, log, cfg['timeouts'], cfg['closeOnComplete'])

    # this never returns
    processLoop(cfg, jvcip, vtxser, state, usePassthrough, cfg['slowdown'])


if __name__ == "__main__":
    apexMain()
