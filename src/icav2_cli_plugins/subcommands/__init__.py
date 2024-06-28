#!/usr/bin/env python

# External imports
import logging
from datetime import datetime
from os import environ
import sys
from copy import deepcopy
from pathlib import Path
from typing import Union, List, Optional, Type, Dict, get_type_hints, Tuple, get_origin
from docopt import docopt
from ruamel.yaml import YAML
import pandas as pd
from enum import Enum
from inspect import isclass

# Import wrapica
from wrapica.bundle import Bundle, coerce_bundle_id_or_name_to_bundle_obj
from wrapica.data import coerce_data_id_path_or_icav2_uri_to_data_obj, Data
from wrapica.enums import AnalysisStorageSize
from wrapica.pipelines import (
    PipelineType,
    coerce_pipeline_id_or_code_to_pipeline_obj
)
from wrapica.project_data import (
    coerce_data_id_icav2_uri_or_path_to_project_data_obj, ProjectData
)
from wrapica.project import (
    Project,
    coerce_project_id_or_name_to_project_obj,
    get_project_id
)
from wrapica.project_analysis import (
    AnalysisStorageType, AnalysisType,
    coerce_analysis_id_or_user_reference_to_analysis_obj
)
from wrapica.project_pipelines import (
    coerce_analysis_storage_id_or_size_to_analysis_storage, ProjectPipeline,
    coerce_pipeline_id_or_code_to_project_pipeline_obj
)
from wrapica.region import (
    Region,
    coerce_region_id_or_city_name_to_region_obj
)
from wrapica.user import (
    User, coerce_user_id_or_name_to_user_obj
)

# Get utils
from ..utils import is_uuid_format
from ..utils.errors import InvalidArgumentError
from ..utils.logger import get_logger
from ..utils.docopt_helpers import clean_multi_args
from ..utils.typing_helpers import (
    is_optional_type, is_multi_type, split_multi_type,
    is_list_type, strip_optional_type, strip_list_type, is_union, strip_union_type
)

# Collect logger
logger = get_logger()


class DocOptArg:
    """
    Every Command will have a pair of attributes for each argument

    i.e a pipeline_arg, and the pipeline id
    self.pipeline_arg:  Optional[DocOptArg] = None
    self.pipeline:  Optional[str] = None

    The pipeline_arg will be used to assign the pipeline id

    The docopt arg must have an _arg suffix but otherwise match the attribute

    By default, cli args will take precedence over yaml args, which will take precedence over env args.

    If the append_args flag is set, then the cli args will be appended to the yaml args, which will be appended to the env args
    Otherwise, cli args will overwrite yaml args, which will overwrite env args etc
    This can only be set to true if the arg type is a list
    """

    def __init__(
            self,
            cli_arg_keys: Union[str, List[str]] = None,
            yaml_arg_keys: Union[str, List[str]] = None,
            env_arg_keys: Union[str, List[str]] = None,
            # arg_type: Type = str,  # One of bool, int, str, datetime, Path, List or Dict
            append_args: bool = False,
            # required: bool = False,
            config: Dict = None,
    ):
        # Initialise inputs
        # self.arg_type: Type = arg_type  # One of str, Path, List
        self.arg_type: Type = Optional[str]  # One of str, Path, List, set by get_arg_type
        self.is_list: bool = False
        self.append_args = append_args
        self.arg_value: Optional[Union[List, str]] = None
        self.required: Optional[bool] = False
        self.config: Optional[Dict] = config

        # Check at least one is set
        if (
                (cli_arg_keys is None) and
                (yaml_arg_keys is None) and
                (env_arg_keys is None)
        ):
            logger.error("Could not find any arguments to assign")
            raise InvalidArgumentError

        # FIXME - put check in later step
        # # Check if append args is set but the arg type is not a list
        # if append_args and not issubclass(arg_type, List):
        #     logger.error("Only set append_args if the arg type is a list")
        #     raise InvalidArgumentError

        # Coerce keys to lists
        if cli_arg_keys is None:
            cli_arg_keys = []
        if yaml_arg_keys is None:
            yaml_arg_keys = cli_arg_keys
        if env_arg_keys is None:
            env_arg_keys = []
        self.cli_arg_keys: Optional[Union[str, List]] = list(
            map(
                lambda cli_arg_key_iter: cli_arg_key_iter.strip("<>").replace("--", "").replace("-", "_"),
                (
                    cli_arg_keys if isinstance(cli_arg_keys, List) else [cli_arg_keys]
                )
            )
        )
        self.yaml_arg_keys: Optional[Union[str, List]] = (
            yaml_arg_keys if isinstance(yaml_arg_keys, List) else [yaml_arg_keys]
        )
        self.env_arg_keys: Optional[Union[str, List]] = (
            env_arg_keys if isinstance(env_arg_keys, List) else [env_arg_keys]
        )

    def coerce_magical_value(self, key: str, value: str):
        """
        Magicals
        For project, pipeline, data, region, user, bundle or analysis-storage-size,
        Coerce into a project id, pipeline id, project data object, region id, user id, bundle or analysis storage id
        Respectively
        :param key:
        :param value:
        :return:
        """
        # The class attribute typing hint should match this accordingly for these 'magicals'
        if key in ["project", "projects", "project_id_or_name"]:
            if not isclass(self.arg_type) or not issubclass(self.arg_type, Project):
                logger.warning("Got a project id or name but the arg type is not a project")
        if isclass(self.arg_type) and issubclass(self.arg_type, Project):
            value: Project = coerce_project_id_or_name_to_project_obj(value)

        if key in ["pipeline", "pipelines", "pipeline_id_or_code"]:
            if (
                    (not self.arg_type == PipelineType) and
                    not (isclass(self.arg_type) and issubclass(self.arg_type, ProjectPipeline))
            ):
                logger.warning("Got a pipeline id or code but the arg type is not a pipeline")

        if self.arg_type == PipelineType or (isclass(self.arg_type) and issubclass(self.arg_type, ProjectPipeline)):
            # Set value as the pipeline id
            if self.arg_type == PipelineType:
                value: PipelineType = coerce_pipeline_id_or_code_to_pipeline_obj(value)
            elif isclass(self.arg_type) and issubclass(self.arg_type, ProjectPipeline):
                # Suppress logging
                og_log_level = logger.level
                try:
                    logger.setLevel(logging.CRITICAL + 1)
                    value: ProjectPipeline = coerce_pipeline_id_or_code_to_project_pipeline_obj(value)
                except ValueError:
                    # Set logging back to original level
                    logger.setLevel(og_log_level)
                    logger.error(
                        f"Tried to get the pipeline object for {value} but failed because could not get the project id")
                    logger.error("Could not get the project id from either the env var OR the icav2 session file")
                    raise InvalidArgumentError
                finally:
                    # Suppress logging
                    logger.setLevel(og_log_level)

        if key in ["data", "data_id_or_uri"]:
            # Check arg type
            if (
                    not isclass(self.arg_type) or
                    not (issubclass(self.arg_type, Data) or issubclass(self.arg_type, ProjectData)) or
                    not (isinstance(value, str) and value.startswith("/"))
            ):
                logger.warning("Got a data id or uri but the arg type is not a data object")

        if isclass(self.arg_type) and (issubclass(self.arg_type, Data) or issubclass(self.arg_type, ProjectData)):
            # Set value as the project data object
            if (
                    self.config is not None and
                    isinstance(self.config, dict) and
                    "create_data_if_not_found" in self.config.keys() and
                    self.config["create_data_if_not_found"]
            ):
                create_data_if_not_found = True
            else:
                create_data_if_not_found = False
            # Suppress logging
            og_log_level = logger.level
            try:
                logger.setLevel(logging.CRITICAL + 1)
                if issubclass(self.arg_type, ProjectData):
                    value: ProjectData = coerce_data_id_icav2_uri_or_path_to_project_data_obj(
                        value,
                        create_data_if_not_found=create_data_if_not_found
                    )
                else:  # issubclass(self.arg_type, Data):
                    value: Data = coerce_data_id_path_or_icav2_uri_to_data_obj(
                        value,
                        create_data_if_not_found=create_data_if_not_found
                    )
            except ValueError:
                # Set logging back to original level
                logger.setLevel(og_log_level)
                logger.error(
                    f"Tried to get the data object for {value} but failed because could not get the project id")
                logger.error("Could not get the project id from either the env var OR the icav2 session file")
                raise InvalidArgumentError
            finally:
                # Suppress logging
                logger.setLevel(og_log_level)

        if key in ["region", "region_id_or_city_name"]:
            if not isclass(self.arg_type) or not issubclass(self.arg_type, Region):
                logger.warning("Got a region id or city name but the arg type is not of type 'Region'")

        if isclass(self.arg_type) and issubclass(self.arg_type, Region):
            value: Region = coerce_region_id_or_city_name_to_region_obj(value)

        if key in ["creator", "creator_id_or_name", "user", "user_id_or_name"]:
            if not isclass(self.arg_type) or not issubclass(self.arg_type, User):
                logger.warning("Got a user id or name but the arg type is not a user")
        if isclass(self.arg_type) and issubclass(self.arg_type, User):
            value: User = coerce_user_id_or_name_to_user_obj(value)

        if key in ["bundle", "bundle_id_or_name"]:
            if not isclass(self.arg_type) or not issubclass(self.arg_type, Bundle):
                logger.warning("Got a bundle id or name but the arg type is not an Bundle type")
        if isclass(self.arg_type) and issubclass(self.arg_type, Bundle):
            value: Bundle = coerce_bundle_id_or_name_to_bundle_obj(
                value
            )

        if key in ["analysis_id_or_user_reference"]:
            if (
                    not self.arg_type == AnalysisType and
                    not (isclass(self.arg_type) and not issubclass(self.arg_type, AnalysisType))
            ):
                logger.warning("Got an analysis id or user reference but the arg type is not an Analysis type")
        if (
                self.arg_type == AnalysisType or
                (isclass(self.arg_type) and issubclass(self.arg_type, AnalysisType))
        ):
            value: AnalysisType = coerce_analysis_id_or_user_reference_to_analysis_obj(
                project_id=get_project_id(),
                analysis_id_or_user_reference=value
            )

        if key in ["analysis_storage", "analysis_storage_id_or_size"]:
            if (
                    not self.arg_type == AnalysisStorageType or
                    (isclass(self.arg_type) and not issubclass(self.arg_type, AnalysisStorageType)) or
                    (not isinstance(value, str) or (value not in AnalysisStorageSize or not is_uuid_format(value)))
            ):
                logger.warning("Got a analysis storage id or size but the arg type is not an AnalysisStorage type")
        if (
                self.arg_type == AnalysisStorageType or
                (isclass(self.arg_type) and issubclass(self.arg_type, AnalysisStorageType))
        ):
            value: AnalysisStorageType = coerce_analysis_storage_id_or_size_to_analysis_storage(
                AnalysisStorageSize(value)
                if value in AnalysisStorageSize
                else value
            )

        return value

    def _assign_arg_value(self, arg_key, arg_value):
        # First check we have a non-null arg value
        if arg_value is None:
            return
        if isinstance(arg_value, List) and len(arg_value) == 0:
            # Empty arg set
            return
        # Check if value is a list
        if arg_value is not None and isinstance(arg_value, List):
            if not self.is_list:
                logger.error(f"Argument '{arg_key}' is a list but the arg type is not a list")
                raise InvalidArgumentError
            external_arg_values = list(
                map(
                    lambda value_iter: self.coerce_magical_value(arg_key, value_iter),
                    arg_value
                )
            )
        elif arg_value is not None and isinstance(arg_value, str):
            external_arg_values = self.coerce_magical_value(arg_key, arg_value)
        elif arg_value is not None and isinstance(arg_value, bool):
            external_arg_values = arg_value
        else:
            logger.error("Not sure how we got here, value is not a list, str, or bool")
            raise InvalidArgumentError

        if self.arg_value is not None and self.append_args:
            # For arguments that are lists, we can extend / append
            if isinstance(external_arg_values, List):
                self.arg_value.extend(external_arg_values)
            else:
                # Add the one item to the list
                self.arg_value.append(external_arg_values)
        else:
            self.arg_value = external_arg_values

    def set_arg_from_cli(self, args_dict):
        for cli_arg_key, cli_arg_value in deepcopy(args_dict).items():
            # Positional keys
            if cli_arg_key.startswith("<") and cli_arg_key.endswith(">"):
                key_stripped = cli_arg_key.strip("<>")
            elif cli_arg_key.startswith("--"):
                key_stripped = cli_arg_key.lstrip("--").replace("-", "_")
            else:
                key_stripped = cli_arg_key

            # Check key is not in cli key
            if key_stripped not in self.cli_arg_keys:
                continue

            self._assign_arg_value(key_stripped, cli_arg_value)

    def set_arg_from_yaml_dict(self, yaml_dict):
        for yaml_arg_key, yaml_arg_value in deepcopy(yaml_dict).items():
            # Check key is not in cli key
            if yaml_arg_key not in self.yaml_arg_keys:
                continue

            self._assign_arg_value(yaml_arg_key, yaml_arg_value)

    def set_arg_from_env(self):
        for env_key in self.env_arg_keys:
            if environ.get(env_key, None) is not None:
                self._assign_arg_value(env_key, environ.get(env_key))

    def find_arg_values(self, cli_args: Dict, yaml_args: Dict):
        # In order of precedence (lowest to highest), set the arg value
        if self.env_arg_keys is not None:
            self.set_arg_from_env()
        if self.yaml_arg_keys is not None:
            self.set_arg_from_yaml_dict(yaml_args)
        if self.cli_arg_keys is not None:
            self.set_arg_from_cli(cli_args)

        # Check if our arg is set (if we have required set to true)
        if self.arg_value is None and self.required:
            logger.error(f"Could not find required arg value for {self.cli_arg_keys} in cli, yaml, or env")
            raise InvalidArgumentError

    def coerce_arg_type(self):
        if self.arg_type == int:
            if self.arg_value is not None and not isinstance(self.arg_value, int):
                if self.is_list:
                    self.arg_value = list(map(int, self.arg_value))
                else:
                    self.arg_value = int(self.arg_value)
        if self.arg_type == str:
            if self.arg_value is not None and not isinstance(self.arg_value, str):
                if self.is_list:
                    self.arg_value = list(map(str, self.arg_value))
                else:
                    self.arg_value = str(self.arg_value)
        if self.arg_type == Path:
            if self.arg_value is not None and not isinstance(self.arg_value, Path):
                if self.is_list:
                    self.arg_value = list(map(Path, self.arg_value))
                else:
                    self.arg_value = Path(self.arg_value)
        if self.arg_type == datetime:
            if self.arg_value is not None and not isinstance(self.arg_value, datetime):
                if self.is_list:
                    self.arg_value = map(pd.to_datetime, self.arg_value)
                else:
                    self.arg_value = pd.to_datetime(self.arg_value)
        if isclass(self.arg_type) and issubclass(self.arg_type, Enum):
            if self.arg_value is not None and not isinstance(self.arg_value, self.arg_type):
                if self.is_list:
                    self.arg_value = list(map(self.arg_type, self.arg_value))
                else:
                    self.arg_value = self.arg_type[self.arg_value]

    def assign_arg_value_to_class_attribute(self, command_obj: 'Command', attribute: str):
        """
        Assign the arg to the attribute
        :param command_obj:
        :param attribute:
        :return:
        """
        # Check if the arg is a list
        setattr(command_obj, attribute, self.arg_value)

    def get_arg_type(self, command_obj: 'Command', attribute: str):
        # Get the type of the attribute
        arg_hints = get_type_hints(command_obj)[attribute]

        # Required Type Hint that's not a list
        # i.e str, int, bool, Path, datetime, Enum, Bundle etc.
        if get_origin(arg_hints) is None:
            self.arg_type = arg_hints
            return

        # Check if optionals
        if is_optional_type(arg_hints):
            self.required = False
            arg_hints = strip_optional_type(arg_hints)
        else:
            self.required = True

        # Check if the arg type is a list
        if is_list_type(arg_hints):
            self.is_list = True
            arg_hints = strip_list_type(arg_hints)

        # Check if in the types list
        try:
            # If we can't assign this input as a union, let's just continue
            _ = Union[arg_hints]
        except TypeError:
            pass
        else:
            if Union[arg_hints] in [PipelineType, AnalysisType, AnalysisStorageType]:
                self.arg_type = Union[arg_hints]
                return

        # Check if the arg type is a multi type
        if is_union(arg_hints):
           arg_hints = strip_union_type(arg_hints)

        # Split multi type
        if is_multi_type(arg_hints):
            arg_hints = split_multi_type(arg_hints)

        # Check we have no sublists
        if isinstance(arg_hints, Tuple):
            for tuple_iter in arg_hints:
                if is_list_type(tuple_iter):
                    logger.error("Cannot have a list of lists or union of list | <type>")
                    raise InvalidArgumentError

        # Assign arg type
        self.arg_type = arg_hints

    def set_default_value(self, command_obj: 'Command', attribute: str):
        if hasattr(command_obj, attribute):
            self.arg_value = getattr(command_obj, attribute)


class Command:
    """
    Super class for the nested subcommand
    """

    def __init__(self, command_argv):
        # Initialise any req vars
        self.cli_args = self._get_args(command_argv)
        print(self.cli_args)
        if self.cli_args.get("--cli-input-yaml", None) is not None:
            self.yaml_args = self._get_yaml_args(Path(self.cli_args["--cli-input-yaml"]))
        else:
            self.yaml_args = {}

        # Check help
        self.check_length(command_argv)

        # Check if help has been called
        if self.cli_args["help"]:
            self._help()

        # Confirm 'required' arguments are present and valid
        try:
            self._assign_args()
            self.check_args()
        except InvalidArgumentError:
            self._help(fail=True)

    def _get_args(self, command_argv):
        """
        :return:
        """
        # Get arguments from commandline
        return docopt(self.__doc__, argv=command_argv, options_first=False)

        # # Clean args as required in https://github.com/docopt/docopt/issues/134
        # return clean_multi_args(
        #     args=docopt_args,
        #     doc=self.__doc__,
        #     use_dual_options=True
        # )

    def _get_yaml_args(self, yaml_file: Optional[Path]):
        """
        Collect the yaml args from the input yaml file
        :param yaml_file:
        :return:
        """
        yaml = YAML()

        if not yaml_file.is_file():
            logger.error(f"Could not get the input yaml file at {yaml_file}, no such file or directory")
            raise InvalidArgumentError

        # Read the yaml file
        with open(yaml_file, "r") as yaml_file:
            yaml_args = yaml.load(yaml_file)

        return yaml_args

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
            self.cli_args["help"] = True

    def check_args(self):
        """
        Defined in the subfunction
        :return:
        """
        # While assign_args and
        raise NotImplementedError

    def _assign_args(self):
        """
        Iterate through each attribute, if the attribute is of type DocOptArg,
        we perform the following:
        1. Make sure that there is an equivalent attribute without the _arg suffix
        2. Collect the value from the CLI, YAML, and ENV
        3. Assign the value to the attribute
        :return:
        """
        if not hasattr(self, "_docopt_type_args"):
            logger.warning("Subclass does not have the attribute _docopt_type_args")

        for docopt_arg_key_name, docopt_arg_obj in getattr(self, "_docopt_type_args").items():
            # Collect the attribute
            if isinstance(docopt_arg_obj, DocOptArg):
                # Check we have a corresponding attribute
                # if not hasattr(self, docopt_arg_key_name):
                #     logger.error(f"Could not find attribute '{docopt_arg_key_name}'")
                #     raise AttributeError
                docopt_arg_obj.set_default_value(self, docopt_arg_key_name)
                docopt_arg_obj.get_arg_type(self, docopt_arg_key_name)
                docopt_arg_obj.find_arg_values(self.cli_args, self.yaml_args)

                # Assign the value to the attribute
                docopt_arg_obj.coerce_arg_type()
                docopt_arg_obj.assign_arg_value_to_class_attribute(self, docopt_arg_key_name)

    #
    # def _get_arg_in_input_yaml_arg_name(
    #         self,
    #         arg_name: str,
    #         input_yaml_data: dict,
    #         required: bool,
    #         arg_type: Union[Type[str] | Type[Path] | Type[List]],
    #         attr_name: str,
    #         yaml_key: Optional[str] = None,
    #         env: Optional[str] = None
    # ) -> Tuple[Optional[str], Optional[str]]:
    #     """
    #     Sub-function of set_arg_from_in_input_yaml_and_cli, handles when we have multiple options for the arg_name
    #     We want to iterate through CLI first, then YAML, then ENV
    #     But that's not that easy, so instead we return a dict containing the value and the source
    #     :param arg_name:
    #     :param input_yaml_data:
    #     :param required:
    #     :param arg_type:
    #     :param attr_name:
    #     :param yaml_key:
    #     :return:
    #     """
    #     # This might mean handling str in a subfunction and calling the subfunction over the list.
    #     # FIXME - if we implement the auto-cli-assignment above
    #     # FIXME - we can first check if this is already assigned (and not none)
    #     arg_value = self.args.get(arg_name, None)
    #     arg_source = "cli"
    #
    #     if yaml_key is None:
    #         yaml_key = attr_name
    #
    #     if arg_value is None and env is not None:
    #         arg_value = os.environ.get(env, None)
    #         arg_source = "env"
    #
    #     # Yaml keys can be camel case
    #     yaml_keys = [yaml_key, to_lower_camel_case(yaml_key)]
    #
    #     # Handle arg_type is string first
    #     if arg_type in [str, Path]:
    #         # Check if not in the cli or in env
    #         if arg_value is not None:
    #             pass
    #
    #         # Check if any of the keys
    #         elif any([yaml_key in input_yaml_data.keys() for yaml_key in yaml_keys]):
    #             yaml_key = next(
    #                 filter(
    #                     lambda key: key in input_yaml_data.keys(),
    #                     yaml_keys
    #                 )
    #             )
    #
    #             arg_value = input_yaml_data[yaml_key]
    #             arg_source = "yaml"
    #
    #         # Check if argument is required
    #         elif required:
    #             logger.error(f"Argument '{arg_name}' is required but not found in input yaml or cli")
    #             raise InvalidArgumentError
    #
    #         # Handle if arg value is None
    #         # Don't cast None type object to a string
    #         if arg_value is None:
    #             return None, None
    #
    #         # Cast from string to Path if need be
    #         if not isinstance(arg_value, arg_type):
    #             arg_value = arg_type(arg_value)
    #
    #         # Set attribute
    #         return arg_value, arg_source
    #
    #     # FIXME - wrong spot for this
    #     if arg_type == List:
    #         # Append if in both
    #         values_in_yaml_and_cli = []
    #
    #         if arg_value is not None:
    #             values_in_yaml_and_cli.extend(arg_value)
    #
    #         if yaml_key in input_yaml_data.keys():
    #             values_in_yaml_and_cli.extend(input_yaml_data.get(yaml_key))
    #
    #         if required and len(values_in_yaml_and_cli) == 0:
    #             logger.error(f"{arg_name} not specified in the input yaml or on the CLI")
    #             raise InvalidArgumentError
    #
    #         self.__setattr__(attr_name, values_in_yaml_and_cli)
    #
    # def set_arg_from_in_input_yaml_and_cli(
    #         self,
    #         arg_name: Union[str | List],
    #         input_yaml_data: dict,
    #         required: bool,
    #         arg_type: Union[Type[str] | Type[Path] | Type[List]],
    #         attr_name: Optional[str] = None,
    #         yaml_key: Optional[Union[str | List]] = None,
    #         env: Optional[str] = None
    # ):
    #     """
    #     For a given argument, check that it's been specified in the input yaml or the cli (and return the value of the argument).
    #
    #     The CLI argument takes precendence over the environment variable, which takes precedence over the input yaml argument.
    #
    #     We assume that the argument names are identical, swapping '-' for '_' with cli and yaml respectively.
    #
    #     One may also look for multiple arguments with the first argument in the list taking preference.
    #     In this case, if the second argument is found on the cli but the first argument is found in the yaml,
    #     the cli still takes preference
    #
    #     If the argument is not found in either the input yaml or the cli, then we raise an error.
    #
    #     We also allow for custom attribute names to map between yaml and cli arguments.
    #
    #     :param arg_name:
    #     :param input_yaml_data:
    #     :param required:
    #     :param arg_type:
    #     :param attr_name:
    #     :param yaml_key:
    #     :param env:
    #     :return:
    #     """
    #     # If yaml_key, or attr_name is set, use those instead
    #     if attr_name is None:
    #         # Convert --arg-name to arg_name
    #         attr_name = arg_name.lstrip("-").replace("-", "_")
    #
    #     # Get cli arg value and attribute names for yaml
    #     if isinstance(arg_name, str):
    #         arg_value, arg_source = self._get_arg_in_input_yaml_arg_name(
    #             arg_name=arg_name,
    #             input_yaml_data=input_yaml_data,
    #             required=required,
    #             arg_type=arg_type,
    #             attr_name=attr_name,
    #             yaml_key=yaml_key,
    #             env=env,
    #         )
    #
    #     elif isinstance(arg_name, List):
    #         arg_values_by_source = {}
    #         arg_value = None
    #         arg_source = None
    #
    #         for iter_, arg_name_iter in enumerate(arg_name):
    #             if isinstance(yaml_key, List):
    #                 try:
    #                     yaml_key_val = yaml_key[iter_]
    #                 except IndexError:
    #                     logger.error("Must specify a yaml key for each arg_name in the list if yaml_key is a list")
    #                     raise IndexError
    #             else:
    #                 yaml_key_val = yaml_key
    #
    #             # Get arg value and source for this iter
    #             arg_value, arg_source = self._get_arg_in_input_yaml_arg_name(
    #                 arg_name=arg_name_iter,
    #                 input_yaml_data=input_yaml_data,
    #                 # May be multiple options, check at the end if required and fail if no value is found
    #                 required=False,
    #                 arg_type=arg_type,
    #                 attr_name=attr_name,
    #                 yaml_key=yaml_key_val,
    #                 env=env,
    #             )
    #
    #             # Only return the first value for each source
    #             if arg_source not in arg_values_by_source.keys():
    #                 arg_values_by_source[arg_source] = arg_value
    #
    #         for arg_source_iter in ["cli", "env", "yaml"]:
    #             if arg_source_iter in arg_values_by_source.keys():
    #                 arg_value = arg_values_by_source[arg_source_iter]
    #                 break
    #         else:
    #             arg_value = None
    #     else:
    #         logger.error(f"arg_name type of '{type(arg_name)}' not supported, must be a list or str")
    #         raise TypeError
    #
    #     # Set attribute
    #     # Don't overwrite if attribute already exists though
    #     if arg_value is None and required:
    #         logger.error(
    #             f"Required {('one of' + ','.join(arg_name)) if isinstance(arg_name, List) else arg_name} in either cli or input yaml but not found")
    #     if arg_value is not None and getattr(self, attr_name, None) is None:
    #         self.__setattr__(attr_name, arg_value)

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
