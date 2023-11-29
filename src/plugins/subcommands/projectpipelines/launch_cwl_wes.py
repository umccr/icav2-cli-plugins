#!/usr/bin/env python3

"""
Launch a workflow through CWL WES
"""
import json
from collections import OrderedDict
from typing import Optional, List

from libica.openapi.v2.model.analysis_output_mapping import AnalysisOutputMapping
from libica.openapi.v2.model.create_cwl_analysis import CreateCwlAnalysis

from ruamel.yaml import YAML

from pathlib import Path

from utils import is_uuid_format, is_uri_format
from utils.errors import InvalidArgumentError
from utils.config_helpers import get_project_id
from utils.globals import ICAv2AnalysisStorageSize
from utils.logger import get_logger
from utils.projectdata_helpers import check_is_directory, create_data_in_project, is_folder_id_format, \
    get_data_obj_from_project_id_and_path, unpack_icav2_uri
from utils.projectpipeline_helpers import get_pipeline_id_from_pipeline_code, ICAv2LaunchJson, \
    get_analysis_storage_id_from_analysis_storage_size, recursively_build_open_api_body_from_libica_item, \
    launch_cwl_workflow

from subcommands import Command

logger = get_logger()


class ProjectPipelinesStartCWLWES(Command):
    """Usage:
    icav2 projectpipelines start-cwl-wes help
    icav2 projectpipelines start-cwl-wes (--launch-yaml=<launch_yaml>)
                                         [--pipeline-code=<pipeline_code> | --pipeline-id=<pipeline_id>]
                                         [--output-parent-folder-path=<output_parent_folder_path> | --output-parent-folder-id=<output_parent_folder_id>]
                                         [--analysis-output-uri=<analysis_output_uri> | --analysis-output-path=<analysis_output_path>]
                                         [--analysis-storage-size=<analysis_storage_size> | --analysis-storage-id=<analysis_storage_id>]
                                         [--activation-id=<activation_id>]
                                         [--create-cwl-analysis-json-output-path=<output_path>]
                                         [--json]

Description:
    Launch an analysis on icav2.
    Please refer to 'icav2 projectpipelines create-wes-input-template' documentation for generating the launch yaml file

    Your launch yaml should contain the following keys:
      * name | user_reference | userReference  (the name of the pipeline analysis run)
      * input | inputs (the CWL input json dict)
      * engine_parameters | engineParameters:
        * Which comprises the following keys:
          * pipeline_id | pipelineId (Optional, can also be specified on cli)
          * pipeline_code | pipelineCode (Optional, can also be specified on cli)
          * output_parent_folder_id | outputParentFolderId (Optional, can also be specified on cli)
          * output_parent_folder_path | outputParentFolderPath (Optional, can also be specified on cli, will be created if it doesn't exist)
          * analysis_output_uri | analysisOutputUri (Optional, can also be specified on cli)
          * analysis_output_path | analysisOutputPath (Optional, can also be specified on cli, assumes the current project id for your outputs)
          * tags (Optional, a dictionary of lists with the following keys)
            * technical_tags | technicalTags  (Optional array of technical tags to attach to this pipeline analysis)
            * user_tags | userTags (Optional array of user tags to attach to this pipeline analysis)
            * reference_tags | referenceTags (Optional array of reference tags to attach to this pipeline analysis)
          * analysis_storage_id | analysisStorageId (Optional, can also be specified on cli or inferred by cwl-ica)
          * analysis_storage_size | analysisStorageSize (Optional, can also be specified on cli or inferred by cwl-ica)
          * activation_id | activationId (Optional, can also be specified on cli or inferred by cwl-ica)
          * cwltool_overrides | cwltoolOverrides (Optional, can also be specified in input as "cwltool:overrides")
          * stream_all_files | streamAllFiles (Optional, convert all files in the inputs to presigned url)  :construction:
          * stream_all_directories | streamAllDirectories (Optional, convert all directories in the inputs to presigned urls) :construction:

    When specifying files or directories in your launch yaml, you can set the location attribute to the following URI syntax:
      * icav2://project_id/data_path or
      * icav2://project_name/data_path
    These will then be mounted into your analysis at runtime.

Options:
    --launch-yaml=<launch_yaml>                              Required, input json similar to v1

    --pipeline-id=<pipeline_id>                              Optional, id of the pipeline you wish to launch
    --pipeline-code=<pipeline_code>                          Optional, name of the pipeline you wish to launch
                                                             Must specify at least one of --pipeline-id or --pipeline-code
                                                             If both --pipeline-id and --pipeline-code are specified,
                                                             then --pipeline-id takes precedence.

                                                             Both pipeline id and pipeline code can be specified inside the launch yaml

    --output-parent-folder-id=<output_parent_folder_id>      Optional, the id of the parent folder to write outputs to
    --output-parent-folder-path=<output_parent_folder_path>  Optional, the path to the parent folder to write outputs to (will be created if it doesn't exist)
                                                             Cannot specify both --output-parent-folder-id AND --output-parent-folder-path
                                                             Cannot specify both --output-parent-folder-id/--output-parent-folder-path and --analysis-output-uri/--analysis-output-path

    --analysis-output-uri=<analysis_output_uri>              Optional, the uri to where the final directory out/ is placed.
                                                             Can be used as an alternative to --output-parent-folder-* parameters.
                                                             Since one will not have control over the final directory name inside --output-parent-folder-*
                                                             Use icav2://project-name-or-id/path/to/out as a value
                                                             Cannot specify both --analysis-output-uri and --analysis-output-path
                                                             Cannot specify both --output-parent-folder-id/--output-parent-folder-path and --analysis-output-uri/--analysis-output-path
    --analysis-output-path=<analysis_output_path>                              Optional, identical to --analysis-output-uri but assumes the current project id for your outputs.

    --analysis-storage-id=<analysis_storage_id>              Optional, analysis storage id, overrides default analysis storage size
    --analysis-storage-size=<analysis_storage_size>          Optional, analysis storage size, one of Small, Medium, Large
                                                             If both --analysis-storage-id AND --analysis-storage-size are specified,
                                                             then --analysis-storage-id takes precedence

    --activation-id=<activation_id>                          Optional, the activation id used by the pipeline analysis

    --create-cwl-analysis-json-output-path=<output_path>     Optional, Path to output a json file that contains the body for a create cwl analysis (https://ica.illumina.com/ica/api/swagger/index.html#/Project%20Analysis/createCwlAnalysis)
                                                             Useful for reproducibility and debugging
    --json                                                   Optional, Write json to stdout, useful for debugging

Environment:
    ICAV2_BASE_URL (optional, defaults to ica.illumina.com)
    ICAV2_PROJECT_ID (optional, taken from ~/.session.ica.yaml otherwise)

Example:
    icav2 projectpipelines start-cwl-wes --launch-yaml /path/to/input.yaml --pipeline-code bclconvert_with_qc_pipeline__4_0_3
    """

    def __init__(self, command_argv):
        # Initialise parameters
        self.launch_yaml_path: Optional[Path] = None
        self.input_launch_json: Optional[ICAv2LaunchJson] = None
        self.pipeline_arg: Optional[str] = None
        self.pipeline_id: Optional[str] = None
        self.project_id: Optional[str] = None
        self.output_parent_folder_arg: Optional[str] = None
        self.output_parent_folder_id: Optional[Path] = None
        self.analysis_output_uri_path_arg: Optional[str] = None
        self.analysis_output: Optional[List[AnalysisOutputMapping]] = None
        self.analysis_storage_id: Optional[str] = None
        self.analysis_storage_arg: Optional[str] = None
        self.activation_id: Optional[str] = None
        self.create_cwl_analysis_json_output_path: Optional[Path] = None

        self.is_output_json: Optional[bool] = None

        self.analysis_id: Optional[str] = None
        self.user_reference: Optional[str] = None

        super().__init__(command_argv)

    def __call__(self):
        self.launch_workflow()

    def check_args(self):
        # Get the project id
        self.project_id = get_project_id()

        # Get launch yaml path
        self.launch_yaml_path = self.args.get("--launch-yaml", None)
        if self.launch_yaml_path is None:
            logger.error("Please specify launch yaml for input")
            raise InvalidArgumentError

        # Import yaml object
        yaml_obj = YAML()
        with open(self.launch_yaml_path, "r") as yaml_h:
            launch_yaml_dict: OrderedDict = yaml_obj.load(yaml_h)

        # Generate input launch json
        self.input_launch_json: ICAv2LaunchJson = ICAv2LaunchJson.from_dict(launch_yaml_dict)

        # Engine parameters - both engine_parameters and engineParameters is accepted
        input_yaml_engine_parameters_dict = launch_yaml_dict.get("engine_parameters", None)
        if input_yaml_engine_parameters_dict is None:
            input_yaml_engine_parameters_dict = launch_yaml_dict.get("engineParameters", {})

        # Check output path for launch body
        create_cwl_analysis_json_output_path_arg = self.args.get("--create-cwl-analysis-json-output-path", None)
        if create_cwl_analysis_json_output_path_arg is not None:
            self.create_cwl_analysis_json_output_path = Path(create_cwl_analysis_json_output_path_arg)
            if not self.create_cwl_analysis_json_output_path.parent.is_dir():
                logger.error("Please ensure the parent directory of the --create-cwl-analysis-json-output-path parameter exists")
                raise InvalidArgumentError
            if self.create_cwl_analysis_json_output_path.is_dir():
                logger.error(f"Cannot create file at {self.create_cwl_analysis_json_output_path} for --create-cwl-analysis-json-output-path parameter, is a directory")
                raise IsADirectoryError

        # Assign the args

        # Set pipeline id arg
        self.set_arg_from_in_input_yaml_and_cli(
            arg_name=["--pipeline-id", "--pipeline-code"],
            input_yaml_data=input_yaml_engine_parameters_dict,
            required=True,
            arg_type=str,
            attr_name="pipeline_arg",
            yaml_key=["pipeline_id", "pipeline_code"]
        )

        # Set output parent folder path
        self.set_arg_from_in_input_yaml_and_cli(
            arg_name=["--output-parent-folder-id", "--output-parent-folder-path"],
            input_yaml_data=input_yaml_engine_parameters_dict,
            required=False,
            arg_type=str,
            attr_name="output_parent_folder_arg",
            yaml_key=["output_parent_folder_id", "output_parent_folder_path"]
        )

        # Set output uri / path
        self.set_arg_from_in_input_yaml_and_cli(
            arg_name=["--analysis-output-uri", "--analysis-output-path"],
            input_yaml_data=input_yaml_engine_parameters_dict,
            required=False,
            arg_type=str,
            attr_name="analysis_output_uri_path_arg",
            yaml_key=["analysis_output_uri", "analysis_output_path"]
        )

        # Set name
        self.set_arg_from_in_input_yaml_and_cli(
            arg_name=["--analysis-storage-id", "--analysis-storage-size"],
            input_yaml_data=input_yaml_engine_parameters_dict,
            required=False,
            arg_type=str,
            attr_name="analysis_storage_arg",
            yaml_key=["analysis_storage_id", "analysis_storage_size"]
        )

        # Set parameters via either cli or launch json
        self.set_arg_from_in_input_yaml_and_cli(
            arg_name="--activation-id",
            input_yaml_data=input_yaml_engine_parameters_dict,
            required=False,
            arg_type=str
        )

        # Set parameters via either cli or launch json
        self.set_arg_from_in_input_yaml_and_cli(
            arg_name="--create-cwl-analysis-json-output-path",
            input_yaml_data=input_yaml_engine_parameters_dict,
            required=False,
            arg_type=Path
        )

        # Set parameters via either cli or launch json
        self.set_arg_from_in_input_yaml_and_cli(
            arg_name="--json",
            input_yaml_data=input_yaml_engine_parameters_dict,
            required=False,
            arg_type=str,
            attr_name="is_output_json"
        )

        # Now update engine parameters if they exist
        if self.analysis_storage_id is not None:
            self.input_launch_json.update_engine_parameter(
                "analysis_storage_id", self.analysis_storage_id
            )

        # Get the activation id
        if self.activation_id is not None:
            self.input_launch_json.update_engine_parameter(
                "activation_id", self.activation_id
            )

        # Check one of pipeline id or pipeline code is specified
        if self.pipeline_arg is None:
            logger.error("Must specify one of --pipeline-id or --pipeline-code, or place them in the launch yaml engine parameter")
            raise InvalidArgumentError

        # Set the pipeline arg as the pipeline id first, or convert pipeline code to pipeline id
        if is_uuid_format(self.pipeline_arg):
            self.pipeline_id = self.pipeline_arg
        else:
            self.pipeline_id = get_pipeline_id_from_pipeline_code(self.project_id, self.pipeline_arg)

        # Update the engine parameter
        self.input_launch_json.update_engine_parameter(
            "pipeline_id", self.pipeline_id
        )

        # Check output uri / output path
        if self.output_parent_folder_arg is not None and self.analysis_output_uri_path_arg is not None:
            logger.error(
                "Please only specify one and only one of the output_parent_folder and analysis_output_uri/analysis_output_path parameter combinations")
            raise InvalidArgumentError

        # Get the output parent folder id
        if self.output_parent_folder_arg is not None:
            if is_folder_id_format(self.output_parent_folder_arg):
                self.output_parent_folder_id = self.output_parent_folder_arg
            else:  # Assume it's a path
                if not self.output_parent_folder_arg.endswith("/"):
                    self.output_parent_folder_arg += "/"

                # Update placeholders before checking if the path exists
                self.output_parent_folder_arg = (
                    self.input_launch_json.engine_parameters.populate_placeholders_in_output_path(
                        self.output_parent_folder_arg
                    )
                )

                # Create directory if it doesn't exist
                if not check_is_directory(
                        project_id=self.project_id,
                        folder_path=str(self.output_parent_folder_arg)
                ):
                    self.output_parent_folder_id = create_data_in_project(
                        project_id=self.project_id,
                        data_path=str(self.output_parent_folder_arg)
                    ).data.id
                else:
                    self.output_parent_folder_id = get_data_obj_from_project_id_and_path(
                        self.project_id,
                        str(self.output_parent_folder_arg)
                    ).data.id

        # Update the engine parameter
        if self.output_parent_folder_id is not None:
            self.input_launch_json.update_engine_parameter(
                "output_parent_folder_id", self.output_parent_folder_id
            )

        # Handle the output uri path arg
        if self.analysis_output_uri_path_arg is not None:
            if is_uri_format(self.analysis_output_uri_path_arg):
                analysis_output_project_id, analysis_output_project_path = unpack_icav2_uri(self.analysis_output_uri_path_arg)
                # Update placeholders before checking if the path exists
                analysis_output_project_path = (
                    self.input_launch_json.engine_parameters.populate_placeholders_in_output_path(
                        analysis_output_project_path
                    )
                )
                self.analysis_output = [
                    AnalysisOutputMapping(
                        source_path="out/",
                        type="FOLDER",
                        target_project_id=analysis_output_project_id,
                        target_path=str(Path(analysis_output_project_path)) + "/"
                    )
                ]
            else:
                self.analysis_output = [
                    AnalysisOutputMapping(
                        source_path="out/",
                        type="FOLDER",
                        target_project_id=self.project_id,
                        target_path=str(Path(self.analysis_output_uri_path_arg)) + "/"
                    )
                ]

        # Update the engine parameter
        if self.analysis_output is not None:
            self.input_launch_json.update_engine_parameter(
                "analysis_output", self.analysis_output
            )

        # Get the analysis storage arg
        if self.analysis_storage_arg is not None:
            if is_uuid_format(self.analysis_storage_arg):
                self.analysis_storage_id = self.analysis_storage_arg
            else:
                self.analysis_storage_id = get_analysis_storage_id_from_analysis_storage_size(
                    ICAv2AnalysisStorageSize(self.analysis_storage_arg)
                )
        if self.analysis_storage_id is not None:
            self.input_launch_json.update_engine_parameter(
                "analysis_storage_id", self.analysis_storage_id
            )

        # Check activation id
        if self.activation_id is not None:
            self.input_launch_json.update_engine_parameter(
                "activation_id", self.activation_id
            )

        # Get the --json parameter
        if self.args.get("--json", False):
            self.is_output_json = True
        else:
            self.is_output_json = False

    def launch_workflow(self):
        # Update engine parameters
        self.input_launch_json.collect_overrides_from_engine_parameters()

        # Deference input json
        logger.info("Dereferencing input json and collecting mount paths")
        self.input_launch_json.deference_input_json()

        # Collect empty engine parameters
        logger.info("Populating empty engine parameters (if any)")
        self.input_launch_json.populate_empty_engine_parameters(
            self.project_id,
            self.pipeline_id
        )

        # Collect analysis
        logger.info("Creating CWL Analysis object")
        cwl_analysis: CreateCwlAnalysis = self.input_launch_json(
            self.pipeline_id
        )

        if self.create_cwl_analysis_json_output_path is not None:
            logger.info(f"Dumping launch analysis payload to {self.create_cwl_analysis_json_output_path}")
            with open(self.create_cwl_analysis_json_output_path, "w") as create_analysis_h:
                create_analysis_h.write(
                    json.dumps(
                        recursively_build_open_api_body_from_libica_item(cwl_analysis),
                        indent=2
                    )
                )
                create_analysis_h.write("\n")

        # Launch workflow
        logger.info("Launching analysis")
        self.analysis_id, self.user_reference = launch_cwl_workflow(
            project_id=self.project_id,
            cwl_analysis=cwl_analysis
        )

        logger.info(f"Successfully launched analysis pipeline '{self.pipeline_id}' with analysis id '{self.analysis_id}' and user reference '{self.user_reference}'")

        if self.is_output_json:
            self.print_to_stdout()

    def print_to_stdout(self):
        print(
            json.dumps(
                {
                    "analysis_id": self.analysis_id,
                    "user_reference": self.user_reference
                },
                indent=2
            )
        )

    def read_launch_yaml(self) -> ICAv2LaunchJson:
        # Import json object
        yaml_obj = YAML()
        with open(self.launch_yaml_path, "r") as yaml_h:
            return ICAv2LaunchJson.from_dict(yaml_obj.load(yaml_h))
