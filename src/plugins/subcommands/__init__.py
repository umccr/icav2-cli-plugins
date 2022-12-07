#!/usr/bin/env python

import sys
from argparse import ArgumentError

from docopt import docopt
from utils.logger import get_logger
from utils import version
from utils.docopt_helpers import clean_multi_args

# Collect logger
logger = get_logger()


class Command:
    """
    Super class for the nested subcommand
    """

    def __init__(self, command_argv):
        # Initialise any req vars
        self.args = self.get_args(command_argv)

        # Check help
        self.check_length(command_argv)

        # Check if help has been called
        if self.args["help"]:
            self._help()

        # Confirm 'required' arguments are present and valid
        try:
            self.check_args()
        except ArgumentError:
            self._help(fail=True)

    def get_args(self, command_argv):
        """
        :return:
        """
        # Get arguments from commandline
        docopt_args = docopt(self.__doc__, argv=command_argv, options_first=False)

        # Clean args as required in https://github.com/docopt/docopt/issues/134
        return clean_multi_args(
            args=docopt_args,
            doc=self.__doc__,
            use_dual_options=True
        )

    def _help(self, fail=False):
        """
        Returns self help doc
        :return:
        """
        print(self.__doc__)
        # If fail will exit 1, else exit 0.
        sys.exit(int(fail))

    def check_length(self, command_argv):
        """
        If arg has just one length, append help
        :return:
        """
        if len(command_argv) == 1:
            logger.debug("Got only one arg, appending 'help'")
            self.args["help"] = True

    def check_args(self):
        """
        Defined in the subfunction
        :return:
        """
        raise NotImplementedError

    def __call__(self):
        raise NotImplementedError


class SuperCommand:
    """
    Supercommand super class for subcommands that then call another subcommand
    """

    def __init__(self, command_argv):
        # Get the subcommand arg
        subcommand = command_argv[1]
        self.subcommand_obj = self.get_subcommand_obj(subcommand, command_argv)

    def get_subcommand_obj(self, cmd, command_argv) -> Command:
        raise NotImplementedError

    def _help(self, fail=False):
        """
        Returns self-help doc
        :return:
        """
        print(self.__doc__)
        # If fail will exit 1, else exit 0.
        sys.exit(int(fail))

    def __call__(self):
        self.subcommand_obj()
