##
## imports
##

import argparse
import socket
import json
import logging
import yaml

##
## Code
##

def apexCmdMain():
    """"Send a NetCmd to Apex"""

    parser = argparse.ArgumentParser()
    parser.add_argument("--rccode", "-rcc", help="Specify remote control code to perform")
    parser.add_argument("--profile", "-pf", help="Specify profile to activate")
    parser.add_argument("--port", "-p", help="Specify port")
    parser.add_argument("--ip", "-ip", help="Specify IP address")
    parser.add_argument("--secret", "-s", help="Specify secret")
    parser.add_argument("--configfile", "-cf", help="Specify location of config file")
    parser.add_argument("--noconfigfile", "-ncf", action='store_true', help="Specify all parameters are on command line")

    args = parser.parse_args()

    cfgName = 'apexcmd.yaml'

    if args.noconfigfile:
        cfgName = None

    if args.configfile:
        # user has specified a locaiton for the config file
        cfgName = args.configfile

    cfg = {}
    if cfgName:
        # read config
        with open(cfgName) as file:
            cfg = yaml.full_load(file)

    if args.ip:
        cfg['ip'] = args.ip

    if args.port:
        cfg['port'] = int(args.port)

    if args.secret:
        cfg['secret'] = args.secret

    # now check we have acceptable parameters
    if not cfg.get('ip'):
        print('Must supply an IP address')
        return

    if not cfg.get('port'):
        print('Must supply a Port')
        return

    if not cfg.get('secret'):
        print('Must specify a secret')
        return

    if (not args.rccode) and (not args.profile):
        print('Need to specify something to send')
        return

    #print('Creating socket...')

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:

        parms = (cfg['ip'], cfg['port'] )
        # print(parms)
        sock.connect( parms )

        if args.rccode:
            msg = {}
            msg['secret'] = cfg['secret']
            msg['rccode'] = args.rccode
            js = json.dumps(msg)
            #print(js)
            sock.sendall(bytes(js,'utf-8'))
            print(f"Apex rccode {msg['rccode']} sent")

        if args.profile:
            msg = {}
            msg['secret'] = cfg['secret']
            msg['profile'] = args.profile
            js = json.dumps(msg)
            #print(js)
            sock.sendall(bytes(js,'utf-8'))
            print(f"Apex profile {msg['profile']} sent")


if __name__ == "__main__":
    apexCmdMain()
