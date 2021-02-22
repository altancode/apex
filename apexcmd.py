##
## imports
##

import argparse
import socket
import select
import json
import logging

##
## Code
##

def apexCmdMain():
    """"Send a NetCmd to Apex"""

    parser = argparse.ArgumentParser()
    parser.add_argument("--showserialports", "-ssp", action='store_true', help="List available serial ports")
    parser.add_argument("--rccode", "-rcc", help="Specify remote control code to perform")
    parser.add_argument("--profile", "-pf", help="Specify profile to activate")
    parser.add_argument("--port", "-p", help="Specify port")
    parser.add_argument("--ip", "-ip", help="Specify IP address")
    parser.add_argument("--secret", "-s", help="Specify secret")

    args = parser.parse_args()

    if not args.ip:
        print('Must supply an IP address')
        return

    if not args.port:
        print('Must supply a Port')
        return

    if not args.secret:
        print('Must specify a secret')
        return

    print('Creating socket...')

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:

        print('Calling connect')
        parms = (args.ip, int(args.port) )
        print(parms)
        sock.connect( parms )

        if args.rccode:
            msg = {}
            msg['secret'] = args.secret
            msg['rccode'] = args.rccode
            js = json.dumps(msg)
            print(js)
            sock.sendall(bytes(js,'utf-8'))

        if args.profile:
            msg = {}
            msg['secret'] = args.secret
            msg['profile'] = args.profile
            js = json.dumps(msg)
            print(js)
            sock.sendall(bytes(js,'utf-8'))


if __name__ == "__main__":
    apexCmdMain()
