#!/usr/bin/env python3
# Impacket - Collection of Python classes for working with network protocols.
#
# SECUREAUTH LABS. Copyright (C) 2021 SecureAuth Corporation. All rights reserved.
#
# This software is provided under a slightly modified version
# of the Apache Software License. See the accompanying LICENSE file
# for more information.
#
# Description:
#   Merge two tickets together and save in one ccache file.
#
# Authors:
#   Liam Wright (@ElJayRight)

import argparse
import sys
from impacket import version
from impacket.krb5.ccache import CCache
from impacket.examples import logger
import logging

def parse_args():
    parser = argparse.ArgumentParser(add_help=True, description='Merge two tickets together and save in one ccache file.')

    parser.add_argument('tickets', nargs='+', action='store', help='List of tickets to be merged')
    parser.add_argument('-o', '--output', action='store', help='Name of ticket output file.')
    parser.add_argument('-debug', action='store_true', help='Turn DEBUG output ON')
    parser.add_argument('-ts', action='store_true', help='Adds timestamp to every logging output')



    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    args = parser.parse_args()

    if len(args.tickets) < 2:
        parser.error("Please specify atleast two tickets.")
    if not args.output:
        parser.error("No output file was given.")
    return args

#copy paste from describeTicket.py
def init_logger(args):
    # Init the example's logger theme and debug level
    logger.init(args.ts)
    if args.debug is True:
        logging.getLogger().setLevel(logging.DEBUG)
        # Print the Library's installation path
        logging.debug(version.getInstallationPath())
    else:
        logging.getLogger().setLevel(logging.INFO)
        logging.getLogger('impacket.smbserver').setLevel(logging.ERROR)

def check_info(tickets):
    creds = [ticket.credentials[0] for ticket in tickets]

    spns = [cred['server'].prettyPrint().split(b'@')[0].decode('utf-8') for cred in creds]

    usernames = [cred['client'].prettyPrint().split(b'@')[0].decode('utf-8') for cred in creds]
    domains = [cred['client'].prettyPrint().decode('utf-8') for cred in creds]
    services = [spn.split("/")[0] for spn in spns]
    machines = [spn.split("/")[1] for spn in spns]


    if len(set(usernames)) != 1:
        logging.error("Usernames are not the same.")
        for file_id,username in enumerate(usernames):
            logging.debug("Username %s: %s" % (file_id+1, username))
        return False
    
    if len(set(spns)) != len(tickets):
        logging.error("Multiple SPNs are the same.")
        for file_id,spn in enumerate(spns):
            logging.debug("SPN %s: %s" %(file_id+1, spn))
        return False
    
    if len(set(machines)) != 1:
        logging.error("Multiple Hosts are different")
        for file_id,host in enumerate(machines):
            logging.debug("Host for ticket %s: %s" %(file_id+1, host))
        return False
    
    logging.info("%-30s: %s" % ("User Name", usernames[0]))
    logging.info("%-30s: %s" % ("Hostname", machines[0]))
    for id,service in enumerate(services):
        logging.info("%-30s: %s" % (f"Service Of Ticket {id+1}", service))
    length = 31 + len(domains[0])
    return length
    
def write_new_ticket(tickets, output_file,length):
    master_ticket = tickets[0]
    other_tickets = tickets[1:]
    with open(master_ticket, 'rb') as main_ticket_data:
        data = main_ticket_data.read()

    for ticket in other_tickets:
        with open(ticket, 'rb') as ticket_data:
            _ = ticket_data.read(length)
            data += ticket_data.read()
    
    with open(output_file, 'wb') as output:
        output.write(data)
    return True
    

def main():
    print(version.BANNER)
    args = parse_args()
    init_logger(args)
    ccaches = [CCache.loadFile(ticket) for ticket in args.tickets]
    logging.debug("Number of tickets: %s", (len(ccaches)))
    length = check_info(ccaches)
    if not length:
        sys.exit(1)

    logging.info("Writing to output file: %s", (args.output))
    write_new_ticket(args.tickets, args.output, length)
    logging.info("Done!")
    return

if __name__ == '__main__':
    main()