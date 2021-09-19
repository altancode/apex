##
## imports
##

import copy
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
import x0genericcmd
import x0opcmd
import x0refcmd
import x0netcontrol
import x0keys
import x0smartpower
import x0smarthdmi
import x0delay
import x0hdfurymode
import x0gammadstate
import traceback
import importlib
import pkgutil
from pprint import pformat
from pprint import pprint

## Constants

POWER_POWERANY = 0
POWER_POWERON = 1
POWER_POWEROFF = 2

##
## Classes
##

class ApexTaskEntry():
    """Class to hold values"""

    def __init__(self, who, what, why, requirePower):
        self.who = who
        self.what = what
        self.why = why
        self.requirePower = requirePower

    def __str__(self):
        return f'ApexTaskEntry {self.who} {self.what} {self.why} {self.requirePower}'

   
##
## globals
##

log = None

##
## code
##

def power2Str(pow):
    if pow == POWER_POWERANY:
        return 'POWER ANY'
    
    if pow == POWER_POWERON:
        return 'POWER ON'
    
    if pow == POWER_POWEROFF:
        return 'POWER OFF'

    return 'POWER UNKNOWN'

def convertPowerReq(op, defaultIfMissing=True):

    log.debug(f'covertPowerReq op is {op}')

#    reqPowerOn = op.get('requirePowerOn',True)
    reqPowerOn = op.get('requirePowerOn',defaultIfMissing)
    
    r = POWER_POWERANY
    if reqPowerOn:
        r = POWER_POWERON

    return r

def singleProfile2cmd(pname, profiles, cmdTargets, log, cfg, stateHDR):
    """takes a profile name and queues the associated commands"""

    jvcip = cmdTargets.get('jvc_pj')['conn']
#    hdfuryip = targetIPs.get('hdfury_generic', None)
#    onkyoip = targetIPs.get('onkyo_iscp', None)

    localQueue = []

    pdata = profiles.get(pname)
    if pdata:

        # we found the profile
        for op in pdata:

            # first we look for the target parameter
            # if it does not exist, we assume it is JVCPJ
            tar = op.get('target', None)
            if tar == None:
                op['target'] = 'jvc_pj'

            # check if the target is one we know
            cmdTarget = cmdTargets.get(op['target'])
            if cmdTarget and (op['target'] != 'jvc_pj'):

                if op.get('op') == 'raw' and type(op.get('cmd')) == str and type(op.get('data')) == str:
                    cmd = op.get('cmd')
                    data = op.get('data')
                    timeout = op.get('timeout', None)

                    updatedTimeouts = copy.deepcopy(cfg['timeouts'])
                    if timeout:
                        updatedTimeouts[cmdTarget['config_timeout_ack']] = int(timeout)/1000
                        log.debug(f"using timeout of {updatedTimeouts[cmdTarget['config_timeout_ack']]} for {cmd} {data}")

                    b = None
                    try:
                        b = bytes(data,'utf-8')
                    except Exception as ex:
                        log.error(f'Cannot convert data to binary {data} {ex}')

                    if b != None:
                        obj = cmdTarget['cmdobj'](cmdTarget['conn'], log, cfg['timeouts'])
#                        obj = x0genericcmd.X0OnkyoReceiverCmd(onkyoip, log, cfg['timeouts'])
                        localQueue.append(ApexTaskEntry(obj,(cmd,b), 'user', convertPowerReq(op, True)))
                else:
                    log.warning(f'Cannot parse operation {op}')

            ##
            ## Now all the special case stuff for JVC which isn't a plugin
            ##

            elif op.get('target') == 'jvc_pj':

                if op.get('op') == 'rccode' and type(op.get('data')) == str:
                    data = op.get('data')
                    b = None
                    try:
                        b = bytes(data,'utf-8')
                    except Exception as ex:
                        log.error(f'Cannot convert data to binary {data} {ex}')

                    if b:
                        log.debug(f'profile result {b}')
                        obj = x0opcmd.X0OpCmd(jvcip, log, cfg['timeouts'])
                        localQueue.append( ApexTaskEntry(obj,('RC',b), 'user', convertPowerReq(op, True) ))

                elif op.get('op') == 'apex-hdfurymode' and type(op.get('data')) == str:
                    data = op.get('data')
                    log.debug(f'apex-hdfurydelay result {data}')
                    obj = x0hdfurymode.X0HDFuryMode(log)          
                    # note we default the requirePowerOn to be FALSE here
                    localQueue.append(ApexTaskEntry(obj, (data, None), 'apex-hdfurymode', convertPowerReq(op, False) ))

                elif op.get('op') == 'apex-ongammad' and type(op.get('data')) == str:
                    # this is the command that appears in the profile
                    data = op.get('data')
                    log.debug(f'apex-ongammad result {data}')
                    obj = x0gammadstate.X0GammaDState(log)          
                    # note we default the requirePowerOn to be FALSE here
                    localQueue.append(ApexTaskEntry(obj, (data, None), 'apex-ongammad', convertPowerReq(op, False) ))

                elif op.get('op') == 'apex-delay' and type(op.get('data')) == str:
                    data = op.get('data')

                    val = None
                    try:
                        val = int(data)
                    except Exception as ex:
                        log.error(f'Cannot convert data to integer {data} {ex}')

                    if val:
                        log.debug(f'apex-delay result {val}')
                        obj = x0delay.X0Delay(jvcip, log, cfg['timeouts'])          
                        localQueue.append(ApexTaskEntry(obj, (val, None), 'user', convertPowerReq(op, True) ))

                elif op.get('op') == 'apex-hdmi' and type(op.get('data')) == str:
                    data = op.get('data')
                    cmd = '1'
                    if data == '2':
                        cmd = '2'

                    log.debug(f'apex-hdmi result {cmd}')
                    obj = x0smarthdmi.X0SmartHDMI(jvcip, log, cfg['timeouts'])          
                    localQueue.append(ApexTaskEntry(obj, (cmd, None), 'user', convertPowerReq(op, True) ))

                elif op.get('op') == 'apex-power' and type(op.get('data')) == str:
                    data = op.get('data')
                    cmd = 'off'
    #                reqPower = POWER_POWERON
                    if data == 'on':
                        cmd = 'on'
    #                    reqPower = POWER_POWEROFF

                    log.debug(f'apex-power result {cmd}')
                    obj = x0smartpower.X0SmartPower(jvcip, log, cfg['timeouts'])          
                    # localQueue.append(ApexTaskEntry(obj, (cmd, None), 'user', reqPower ))
                    localQueue.append(ApexTaskEntry(obj, (cmd, None), 'user', POWER_POWERANY ))
                
                elif op.get('op') == 'apex-pm' and type(op.get('data')) == str:
                    data = op.get('data')
                    b = None
                    try:
                        b = bytes(data,'utf-8')
                    except Exception as ex:
                        log.error(f'Cannot convert data to binary {data} {ex}')

                    if b:
                        log.debug(f'apex-pm profile result {b}')
                        localQueue.append(ApexTaskEntry(stateHDR, (b, None), 'user', convertPowerReq(op, True) ))

                elif op.get('op') == 'raw' and type(op.get('cmd')) == str and type(op.get('data')) == str:
                    cmd = op.get('cmd')
                    data = op.get('data')
                    timeout = op.get('timeout', None)

                    updatedTimeouts = copy.deepcopy(cfg['timeouts'])
                    if timeout:
                        updatedTimeouts['jvcOpAckTimeout'] = int(timeout)/1000
                        log.debug(f"using timeout of {updatedTimeouts['jvcOpAckTimeout']} for {cmd} {data}")

                    b = None
                    try:
                        b = bytes(data,'utf-8')
                    except Exception as ex:
                        log.error(f'Cannot convert data to binary {data} {ex}')

                    if b != None:
                        log.debug(f'profile result {cmd} {b}')
    #                    obj = x0opcmd.X0OpCmd(jvcip, log, cfg['timeouts'])
                        obj = x0opcmd.X0OpCmd(jvcip, log, updatedTimeouts)
                        localQueue.append(ApexTaskEntry(obj,(cmd,b), 'user', convertPowerReq(op, True) ))

                elif op.get('op') == 'raw' and type(op.get('cmd')) == str and type(op.get('numeric')) == int:
                    log.debug(f'inside number with {op}')
                    cmd = op.get('cmd')
                    num = op.get('numeric')

                    if -0x8000 <= num <= 0x7FFF:
                        if num < 0:
                            num = 0x10000 + num

                        b = None
                        try:
                            b = bytes('{:04X}'.format(num & 0xffff), 'utf-8')
                        except Exception as ex:
                            log.error(f'Cannot convert data to binary {num} {ex}')

                        if b:
                            log.debug(f'profile result {cmd} {b}')
                            obj = x0opcmd.X0OpCmd(jvcip, log, cfg['timeouts'])
                            localQueue.append(ApexTaskEntry(obj,(cmd,b), 'user', convertPowerReq(op, True) ))

                else:
                    log.warning(f'Cannot parse operation {op}')
            else:
                log.warning(f'Unknown target for operation {op}')
    else:
        log.warning(f'Ignoring Unknown profile {pname}')

    log.debug(f'New operations {localQueue}')
    return localQueue


def profile2cmd(indata, profiles, targetIPs, log, cfg, stateHDR):
    """takes an array of dictionaries each containing a profilename and queues the associated commands"""
    localQueue = []

    for r in indata:
        pname = r.get('profile')
        if pname:
            localQueue = localQueue + singleProfile2cmd(pname, profiles, targetIPs, log, cfg, stateHDR)

    return localQueue


def addPowerCheck(inlist, jvcip, log, cfg):
    outlist = []
    for x in inlist:
        obj = x0refcmd.X0RefCmd(jvcip, log, cfg['timeouts'])
        outlist.append(ApexTaskEntry(obj,('PW',b''), 'apex-checkpower', False))
        outlist.append(x)

    return outlist


def processLoop(cfg, cmdTargets, vtxser, stateHDR, slowdown, netcontrol, keyinput, profiles, secret):
    """Main loop which recevies HDFury data and intelligently acts upon it"""

    jvcip = cmdTargets.get('jvc_pj')['conn']
#    hdfuryip = targetIPs.get('hdfury_generic', None)
#    onkyoip = targetIPs.get('onkyo_iscp', None)

    watchGammaD = False
    nextGammaDTime = 0
    gammaDProfile = ''

    testOnetime = False
    taskQueue = []
    currentState = None

    chatty = False
    keepaliveOffset = 10
    nextKeepalive = time.time() + keepaliveOffset

    followHDFury = True
    jvcPowerState = POWER_POWEROFF

    # Start by asking the JVC model
    obj = x0refcmd.X0RefCmd(jvcip, log, cfg['timeouts'])
    taskQueue.append(ApexTaskEntry(obj,('MD',b''), 'boot-model', False))

    # # and ask the HDFury something
    # obj = x0genericcmd.X0HDFuryVertex2Cmd(hdfuryip, log, cfg['timeouts'])
    # taskQueue.append(ApexTaskEntry(obj,('get',b'ipaddr'), 'boot-hdfury-ip', False))

    # # and ask Onkyo something
    # obj = x0genericcmd.X0OnkyoReceiverCmd(onkyoip, log, cfg['timeouts'])
    # taskQueue.append(ApexTaskEntry(obj,('PWR',b'QSTN'), 'boot-onkyo-power', False))

    #
    # The Big Loop
    #

    while True:
        try:
            if slowdown > 0:
                log.warning(f'Slowdown of {slowdown} enabled...')
                time.sleep(slowdown)

            finished = True
            if currentState:
                # we have a state, so we just keep working at it
                finished,rsp = currentState.who.action()
                if finished:
                    if currentState.why == 'apex-checkpower':
                        log.debug(f'Finished processing task {rsp}')
                        lastPowered = jvcPowerState
                        # if rsp == b'1' or rsp == b'3':
                        if rsp == b'1':
                            # 1 is on
                            # 3 is reserved but appears to mean "warming up"
                            jvcPowerState = POWER_POWERON
                        else: 
                            jvcPowerState = POWER_POWEROFF

                        if lastPowered != jvcPowerState:
                            log.info(f'JVC Power State changed to {power2Str(jvcPowerState)} {jvcPowerState}')
                    
                    elif currentState.why == 'boot-model':
                        if rsp:
                            log.info(f'JVC Model is "{rsp.decode("utf-8")}"')

                    elif currentState.why == 'boot-hdfury-ip':
                        if rsp:
                            log.info(f'HDFury says IP is "{rsp.decode("utf-8")}"')

                    elif currentState.why == 'boot-onkyo-power':
                        if rsp:
                            log.info(f'Onkyo says Power is "{rsp.decode("utf-8")}"')

                    elif currentState.why == 'apex-hdfurymode':
                        if rsp:
                            followHDFury = False
                            if rsp == 'follow':
                                followHDFury = True

                            log.info(f'HDFuryFollowMode is now {rsp} ({followHDFury})')

                    elif currentState.why == 'apex-ongammad':
                        if rsp != None:
                            if rsp == '':
                                log.info(f'apex-ongammad disabled {rsp}')
                                watchGammaD = False
                                nextGammaDTime = 0
                                gammaDProfile = ''
                            else:
                                log.info(f'apex-ongammad enabled with profile "{rsp}"')
                                watchGammaD = True
                                nextGammaDTime = 0
                                gammaDProfile = rsp

                    elif currentState.why == 'apex-gammadcheck':
                        if rsp:
                            if rsp == b'7':
                                # it is gamma d
                                # look up the profile and add the commands
                                log.info(f'Noticed Gamma D!  Adding profile "{gammaDProfile}"" to queue')
                                taskQueue = taskQueue + singleProfile2cmd(gammaDProfile, profiles, cmdTargets, log, cfg, stateHDR)

            if finished:
                # get the next one to process
                currentState = None
                if len(taskQueue) > 0:
                    log.debug(f'Grabbing next operation... Queue is {len(taskQueue)}')
                    for i,val in enumerate(taskQueue):
                        log.debug(f'   {i+1}: {val}')

                    next = taskQueue.pop(0)

                    if ( (jvcPowerState == POWER_POWEROFF) and (next.requirePower == POWER_POWERON) ) or \
                        ((jvcPowerState == POWER_POWERON) and (next.requirePower == POWER_POWEROFF)):
                        log.debug(f'Not performing operation because jvcPowerState is {jvcPowerState} and {next}')
                    else:
                        currentState = next
                        log.debug(f'Next operation is class {type(next.who)} w/{next.what}')
                        currentState.who.set(next.what[0],next.what[1])

            if currentState == None:
                # empty stuff we don't want, such as stale responses or keep alive ack
                jvcip.read(emptyIt = True)

                # maybe schedule a gammad check?
                if watchGammaD and time.time() > nextGammaDTime:
                    log.debug(f'adding gammad check to queue')
                    obj = x0refcmd.X0RefCmd(jvcip, log, cfg['timeouts'])
                    taskQueue.append(ApexTaskEntry(obj,('PM',b'GT'), 'apex-gammadcheck', True))

                    # this is the soonest it can happen again, but it could be later if the queue has multiple enttries
                    nextGammaDTime = time.time() + 1
                else:                
                    # check if keepalive time
                    if time.time() > nextKeepalive:
                        # it is!
                        cmd = b'!\x89\x01\x00\x00\n'
                        if chatty:
                            log.debug(f'Sending keep alive {cmd}')
                        ok = jvcip.send(cmd)
                        if not ok:
                            log.warning(f'Unable to send keep alive')
                
                        nextKeepalive = time.time() + keepaliveOffset

            if vtxser:
                rxData = vtxser.read()
                if rxData != b'':
                    # we got something from Vertex
                    log.debug(f'HDFury said "{rxData}"')

                    # only support picture mode for intelligent operation
                    example = b'!\x89\x01PMPM'
                    if len(rxData) >= len(example) and rxData[0:len(example)] == example:
                        pm = rxData[7:9]
                        profileName = '_APEX_PM' + misc.getPictureMode(pm)

                        if followHDFury:
                            log.info(f'HDFury said to activate profile {profileName} ({pm})')

                            if currentState and currentState.who == stateHDR:
                                # as an optimization we just change the currently running state
                                # this keeps the behavior we had prior
                                log.debug(f'Switching stateHDR in mid flight to {pm}')
                                stateHDR.set(pm,None)
                            else:
                                taskQueue = taskQueue + addPowerCheck(singleProfile2cmd(profileName, profiles, cmdTargets, log, cfg, stateHDR), jvcip, log, cfg)
                        else:
                            log.debug(f'Ignoring HDFury request to activate profile {profileName} ({pm})') 
                    else:
                        log.error(f'Ignoring HDFury {rxData} {rxData[0:len(example)]} {example}')

            if netcontrol:
                results = netcontrol.action()
                if len(results) > 0:
                    log.debug(f'Netcontrol results {results}')
                    verified = []
                    for r in results:
                        if r.get('secret') == secret:
                            verified.append(r)
                        else:
                            log.warning(f'Secret did not match in request for profile {r}')
                    taskQueue = taskQueue + addPowerCheck(profile2cmd(verified, profiles, cmdTargets, log, cfg, stateHDR), jvcip, log, cfg)

            if keyinput:
                results = keyinput.action()
                if len(results) > 0:
                    log.debug(f'keyinput results {results}')
                    taskQueue = taskQueue + addPowerCheck(profile2cmd(results, profiles, cmdTargets, log, cfg, stateHDR),  jvcip, log, cfg)

            if testOnetime:
                testOnetime = False

                obj = x0smartpower.X0SmartPower(jvcip, log, cfg['timeouts'])
                taskQueue.append(ApexTaskEntry(obj,('off',b''), 'user', False))

            #     obj = x0refcmd.X0RefCmd(jvcip, log, cfg['timeouts'])
            #     taskQueue.append(ApexTaskEntry(obj,('PW',b''), 'apex-checkpower', False))

        except Exception as ex:
            log.error(f'Big Problem Exception {ex}',exc_info=True)
#            traceback.print_exc()
            time.sleep(10)


def apexMain():
    """"Setup looging, connectivity and call main processing loop"""

    global log

    formatter = logging.Formatter('%(asctime)s [%(levelname)s] [%(module)s]: %(message)s')
    formatter.default_msec_format = '%s.%03d'
    log = logging.getLogger("jvcx0")
    log.setLevel(logging.DEBUG)

    # for stderr
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
#    handler.setLevel(logging.INFO)
    handler.setLevel(logging.DEBUG)
    log.addHandler(handler)

    parser = argparse.ArgumentParser()
    parser.add_argument("--showserialports", "-ssp", action='store_true', help="List available serial ports")
    parser.add_argument("--configfile", "-cf", help="Specify location of configuration file")
    parser.add_argument("--configfile2", "-cf2", help="Specify location of a second configuration file (merged with first")
    parser.add_argument("--logfile", "-lf", help="Specify log file location")

    args = parser.parse_args()

    logFile = './apex.log'
    if args.logfile:
        # user has specified a locaiton for the logging
        logFile = args.logfile

    # now that we have the log file name, we setup file logging
    handler = RotatingFileHandler(logFile, maxBytes=500*1024, backupCount=3)
    handler.setFormatter(formatter)
    log.addHandler(handler)

    log.info(f'Using log file {logFile}')

    if args.showserialports:
        # show the serial ports and exit
        x0serial.showSerialPorts()
        return

    cfg1 = {}
    cfgName1 = 'apex.yaml'
    if args.configfile:
        # user has specified a locaiton for the config file
        cfgName1 = args.configfile
    log.info(f'Using main config located at {cfgName1}')

    # read config
    with open(cfgName1) as file:
        try:
            cfg1 = yaml.full_load(file)
        except Exception as ex:
            log.error(f'Unable to parse YAML configuration {ex}', exc_info=True)
            raise ex

    cfg2 = {}
    cfgName2 = None
    if args.configfile2:
        # user has specified a locaiton for the config file
        cfgName2 = args.configfile2
        log.info(f'Using user config2 located at {cfgName2}')

        # read config
        with open(cfgName2) as file:
            try:
                cfg2 = yaml.full_load(file)
            except Exception as ex:
                log.error(f'Unable to parse YAML configuration {ex}', exc_info=True)
                raise ex

    # merge cfg and cfg2
    cfg = {}
    allKeysDict = { **cfg1, **cfg2 }
    keys = allKeysDict.keys()
    print('*** KEYS ***')
    pprint(keys)
    for key in keys:
        if isinstance(allKeysDict[key], dict):
            # it is a dictionary
            # merge the two dicts together.   cfg2 will win if conflict
            cfg[key] = { **cfg1.get(key,{}), **cfg2.get(key,{}) } 
        else:
            # not a dictionary
            # use value from cfg2 unless it does not exist, then use cfg1
            cfg[key] = cfg2.get(key, cfg1.get(key,None))

##
## This whole thing should be updated to use a table with defaults
## and fill in the values if needed
## rather than a bunch of if statements
##

    if not 'timeouts' in cfg:
        cfg['timeouts'] = {}

    # serial
    if not 'hdfuryRead' in cfg['timeouts']:
        cfg['timeouts']['hdfuryRead'] = 0.1

    if not 'hdfury_generic_ack' in cfg['timeouts']:
        cfg['timeouts']['hdfury_generic_ack'] = 2

    if not 'onkyo_iscp_ack' in cfg['timeouts']:
        cfg['timeouts']['onkyo_iscp_ack'] = 2

    if not 'jvcIP' in cfg['timeouts']:
        cfg['timeouts']['jvcIP'] = 0.25

    if not 'jvcRefAck' in cfg['timeouts']:
        cfg['timeouts']['jvcRefAck'] = 0.25

    if not 'jvcDefault' in cfg['timeouts']:
        cfg['timeouts']['jvcDefault'] = 2

    if not 'jvcOpAck' in cfg['timeouts']:
        cfg['timeouts']['jvcOpAck'] = 30
 
    if not 'jvcOpAckTimeout' in cfg['timeouts']:
        cfg['timeouts']['jvcOpAckTimeout'] = 60

    if not 'jvcPowerTimeout' in cfg['timeouts']:
        cfg['timeouts']['jvcPowerTimeout'] = 120

    if not 'closeOnComplete' in cfg:
        cfg['closeOnComplete'] = False

    if not 'slowdown' in cfg:
        cfg['slowdown'] = 0

    # if not 'netcontrolport' in cfg:
    #     cfg['netcontrolport'] = 0

    # if not 'netcontrolsecret' in cfg:
    #     cfg['netcontrolsecret'] = 'secret'

    log.info(f'Apex started...')
    log.debug(f'Using config {pformat(cfg)}')

    cmdTargets = {}

    if 'jvc_pj' in cfg:
        log.info(f'Connecting to JVC')
        jvcip = x0ip.X0IPJVC('jvcIP', (cfg['jvc_pj']['ip'], cfg['jvc_pj']['port']), log, cfg['timeouts'])
        jvcip.connect()
        cmdTargets['jvc_pj'] = { 'conn': jvcip } 
    else:
        log.warning('No jvc_pj configured')

    discovered_plugins = {
        name: importlib.import_module(name)
        for finder, name, ispkg
        in pkgutil.iter_modules()
        if name.startswith('apextarget_')
    }

    log.info('Discovered Apex Target Plugins:')
    for key in discovered_plugins:
        log.info(f'  {key}')

    for key in discovered_plugins:
        details = discovered_plugins[key].getDetails()
        pprint(details)
        conn = None
        if details['config_ip']:
            log.info(f'Setting up plugin {details["name"]}')
            c = cfg[details['name']]
            pprint(c)
            conn = x0ip.X0IPGeneric(
                details['config_timeout_ack'], 
                ( c [ details['config_ip'] ], c [ details['config_port'] ] ),
                log, 
                cfg['timeouts'], 
                details['delimiter']
            )
            conn.connect()
        cmdTargets[details['name']] = { 'conn': conn, 'cmdobj': details['cmdobj']}

    log.info('Enabled Apex Targets:')
    for key in cmdTargets:
        log.info(f'  {key}')

    vtxser = None
    if cfg.get('hdfury_serial',None):
        vtxser = x0serial.X0Serial(cfg['hdfury_serial']['device'], log, cfg['timeouts'])
        try:
            vtxser.connect()
            log.info(f"HDFury device at {cfg['hdfury_serial']['device']}")
        except Exception as ex:
            log.error(f'Exception while accessing serial port ("{ex}"')
            return
    else:
        log.info('No HDFury Serial device configured!')

    state = x0state.X0State(jvcip, log, cfg['timeouts'], cfg['closeOnComplete'])

    netcontrolSecret = ''
    netcontrol = None
    if 'netcontrol' in cfg:
        try:
            netcontrol = x0netcontrol.x0NetControl(log, cfg['netcontrol']['port'])
            netcontrolSecret = cfg['netcontrol'].get('secret','')
        except Exception as ex:
            log.error(f'Exception while enabling netcontrol.  Disabling... ("{ex}"')

    keyinput = None
    if 'keydevice' in cfg:
        try:
            keyinput = x0keys.x0Keys(log, cfg['keydevice'], cfg['keymap'])
        except Exception as ex:
            log.error(f'Exception while enabling keydevice.  Disabling... ("{ex}"')
     
    # this never returns
    processLoop(cfg, cmdTargets, vtxser, state, cfg['slowdown'], netcontrol, keyinput, cfg['profiles'], netcontrolSecret)


if __name__ == "__main__":
    apexMain()
