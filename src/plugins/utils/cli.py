#!/usr/bin/env python3

"""icav2-cli-plugins ::: a suite of additional cli additions to extend the existing icav2 cli

Usage:
    icav2-cli-plugins [options] <command> <subcommand> [<args>...]

Options:
    --debug                             Set the log level to debug

Command:

    help                                Print help and exit
    version                             Print version and exit

    ######################
    Project Analyses                    Collection of subfunctions relating to analyses on project pipeline
    ######################
    projectanalyses

    ##########################
    Project Data
    ##########################
    projectdata                         Collection of subfunctions relating to accessing project data

    ##########################
    Project Pipelines
    ##########################
    projectpipelines                    Collection of subfunctions relating to creating / deploying pipelines

    ######################
    Tenants
    #######################
    tenants                             Collection of tenant handling scripts
"""

from docopt import docopt
from utils import version
import sys
from utils.logger import set_basic_logger

logger = set_basic_logger()


def _dispatch():

    # This variable comprises both the subcommand AND the args
    global_args: dict = docopt(__doc__, sys.argv[1:], version=version, options_first=True)

    # Handle all global args we've set
    if global_args["--debug"]:
        logger.info("Setting logging level to 'DEBUG'")
        logger.setLevel(level="DEBUG")
    else:
        logger.setLevel(level="INFO")

    command_argv = [global_args["<command>"], global_args["<subcommand>"]] + global_args["<args>"]

    cmd = global_args['<command>']

    # Yes, this is just a massive if-else statement
    if cmd == "help":
        # We have a separate help function for each subcommand
        print(__doc__)
        sys.exit(0)
    elif cmd == "version":
        print(version)
        sys.exit(0)

    # Configuration commands
    elif cmd == "projectanalyses":
        from subcommands.projectanalyses import ProjectAnalyses as subcommand
    elif cmd == "projectdata":
        from subcommands.projectdata import ProjectData as subcommand
    elif cmd == "projectpipelines":
        from subcommands.projectpipelines import ProjectPipelines as subcommand
    elif cmd == "tenants":
        from subcommands.tenants import Tenants as subcommand
    # NotImplemented Error
    else:
        print(__doc__)
        print(f"Could not find cmd \"{cmd}\". Please refer to usage above")
        sys.exit(1)

    # Initialise
    subcommand_obj = subcommand(command_argv)
    # Then call
    subcommand_obj()


def main():
    # If only cwl-ica is written, append help s.t help documentation shows
    if len(sys.argv) == 1:
        sys.argv.append('help')
    try:
        _dispatch()
    except KeyboardInterrupt:
        pass
