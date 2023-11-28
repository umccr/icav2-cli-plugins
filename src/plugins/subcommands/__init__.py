#!/usr/bin/env python
import os
import sys
from pathlib import Path
from typing import Union, List, Optional, Tuple, Type

from docopt import docopt

from utils import to_lower_camel_case
from utils.errors import InvalidArgumentError
from utils.logger import get_logger
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
        except InvalidArgumentError:
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

    def _get_arg_in_input_yaml_arg_name(
            self,
            arg_name: str,
            input_yaml_data: dict,
            required: bool,
            arg_type: Union[Type[str] | Type[Path] | Type[List]],
            attr_name: str,
            yaml_key: Optional[str] = None,
            env: Optional[str] =None
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Sub-function of set_arg_from_in_input_yaml_and_cli, handles when we have multiple options for the arg_name
        We want to iterate through CLI first, then YAML, then ENV
        But that's not that easy, so instead we return a dict containing the value and the source
        :param arg_name:
        :param input_yaml_data:
        :param required:
        :param arg_type:
        :param attr_name:
        :param yaml_key:
        :return:
        """
        # This might mean handling str in a subfunction and calling the subfunction over the list.
        arg_value = self.args.get(arg_name, None)
        arg_source = "cli"

        if yaml_key is None:
            yaml_key = attr_name

        if arg_value is None and env is not None:
            arg_value = os.environ.get(env, None)
            arg_source = "env"

        # Yaml keys can be camel case
        yaml_keys = [yaml_key, to_lower_camel_case(yaml_key)]

        # Handle arg_type is string first
        if arg_type in [str, Path]:
            # Check if not in the cli or in env
            if arg_value is not None:
                pass

            # Check if any of the keys
            elif any([yaml_key in input_yaml_data.keys() for yaml_key in yaml_keys]):
                yaml_key = next(
                    filter(
                        lambda key: key in input_yaml_data.keys(),
                        yaml_keys
                    )
                )

                arg_value = input_yaml_data[yaml_key]
                arg_source = "yaml"

            # Check if argument is required
            elif required:
                logger.error(f"Argument '{arg_name}' is required but not found in input yaml or cli")
                raise InvalidArgumentError

            # Handle if arg value is None
            # Don't cast None type object to a string
            if arg_value is None:
                return None, None

            # Cast from string to Path if need be
            if not isinstance(arg_value, arg_type):
                arg_value = arg_type(arg_value)

            # Set attribute
            return arg_value, arg_source

        # FIXME - wrong spot for this
        if arg_type == List:
            # Append if in both
            values_in_yaml_and_cli = []

            if arg_value is not None:
                values_in_yaml_and_cli.extend(arg_value)

            if yaml_key in input_yaml_data.keys():
                values_in_yaml_and_cli.extend(input_yaml_data.get(yaml_key))

            if required and len(values_in_yaml_and_cli) == 0:
                logger.error(f"{arg_name} not specified in the input yaml or on the CLI")
                raise InvalidArgumentError

            self.__setattr__(attr_name, values_in_yaml_and_cli)

    def set_arg_from_in_input_yaml_and_cli(
            self,
            arg_name: Union[str | List],
            input_yaml_data: dict,
            required: bool,
            arg_type: Union[Type[str] | Type[Path] | Type[List]],
            attr_name: Optional[str] = None,
            yaml_key: Optional[Union[str | List]] = None,
            env: Optional[str] = None
    ):
        """
        For a given argument, check that it's been specified in the input yaml or the cli (and return the value of the argument).

        The CLI argument takes precendence over the environment variable, which takes precedence over the input yaml argument.

        We assume that the argument names are identical, swapping '-' for '_' with cli and yaml respectively.

        One may also look for multiple arguments with the first argument in the list taking preference.
        In this case, if the second argument is found on the cli but the first argument is found in the yaml,
        the cli still takes preference

        If the argument is not found in either the input yaml or the cli, then we raise an error.

        We also allow for custom attribute names to map between yaml and cli arguments.

        :param arg_name:
        :param input_yaml_data:
        :param required:
        :param arg_type:
        :param attr_name:
        :param yaml_key:
        :param env:
        :return:
        """
        # If yaml_key, or attr_name is set, use those instead
        if attr_name is None:
            # Convert --arg-name to arg_name
            attr_name = arg_name.lstrip("-").replace("-", "_")

        # Get cli arg value and attribute names for yaml
        if isinstance(arg_name, str):
            arg_value, arg_source = self._get_arg_in_input_yaml_arg_name(
                arg_name=arg_name,
                input_yaml_data=input_yaml_data,
                required=required,
                arg_type=arg_type,
                attr_name=attr_name,
                yaml_key=yaml_key,
                env=env,
            )

        elif isinstance(arg_name, List):
            arg_values_by_source = {}
            arg_value = None
            arg_source = None

            for iter_, arg_name_iter in enumerate(arg_name):
                if isinstance(yaml_key, List):
                    try:
                        yaml_key_val = yaml_key[iter_]
                    except IndexError:
                        logger.error("Must specify a yaml key for each arg_name in the list if yaml_key is a list")
                        raise IndexError
                else:
                    yaml_key_val = yaml_key

                # Get arg value and source for this iter
                arg_value, arg_source = self._get_arg_in_input_yaml_arg_name(
                    arg_name=arg_name_iter,
                    input_yaml_data=input_yaml_data,
                    # May be multiple options, check at the end if required and fail if no value is found
                    required=False,
                    arg_type=arg_type,
                    attr_name=attr_name,
                    yaml_key=yaml_key_val,
                    env=env,
                )

                # Only return the first value for each source
                if arg_source not in arg_values_by_source.keys():
                    arg_values_by_source[arg_source] = arg_value

            for arg_source_iter in ["cli", "env", "yaml"]:
                if arg_source_iter in arg_values_by_source.keys():
                    arg_value = arg_values_by_source[arg_source_iter]
                    break
            else:
                arg_value = None
        else:
            logger.error(f"arg_name type of '{type(arg_name)}' not supported, must be a list or str")
            raise TypeError

        # Set attribute
        # Don't overwrite if attribute already exists though
        if arg_value is None and required:
            logger.error(f"Required {('one of' + ','.join(arg_name)) if isinstance(arg_name, List) else arg_name} in either cli or input yaml but not found")
        if arg_value is not None and getattr(self, attr_name, None) is None:
            self.__setattr__(attr_name, arg_value)

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
