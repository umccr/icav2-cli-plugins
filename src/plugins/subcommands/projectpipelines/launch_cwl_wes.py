#!/usr/bin/env python3

"""
Launch a workflow through CWL WES
"""
import json
from typing import Optional

from libica.openapi.v2.model.create_cwl_analysis import CreateCwlAnalysis

from ruamel.yaml import YAML

from pathlib import Path

from utils.errors import InvalidArgumentError
from utils.config_helpers import get_project_id
from utils.logger import get_logger
from utils.projectdata_helpers import check_is_directory, create_data_in_project
from utils.projectpipeline_helpers import get_pipeline_id_from_pipeline_code, ICAv2LaunchJson, \
    get_analysis_storage_id_from_analysis_storage_size, recursively_build_open_api_body_from_libica_item, \
    launch_cwl_workflow

from subcommands import Command

logger = get_logger()


class ProjectDataStartCWLWES(Command):
    """Usage:
    icav2 projectpipelines start-cwl-wes help
    icav2 projectpipelines start-cwl-wes (--launch-yaml=<launch_yaml>)
                                         (--pipeline-code=<pipeline_code> | --pipeline-id=<pipeline_id>)
                                         [--output-parent-folder-path=<output_parent_folder_path> | --output-parent-folder-id=<output_parent_folder_id>]
                                         [--analysis-storage-size=<analysis_storage_size> | --analysis-storage-id=<analysis_storage_id>]
                                         [--activation-id=<activation_id>]
                                         [--create-cwl-analysis-json-output-path=<output_path>]

Description:
    Launch an analysis on icav2.
    Please refer to 'icav2 projectpipelines create-wes-input-template' documentation for generating the launch yaml file

    Your launch yaml should contain the following keys:
      * name | user_reference | userReference  (the name of the pipeline analysis run)
      * input | inputs (the CWL input json dict)
      * engine_parameters | engineParameters:
        * Which comprises the following keys:
          * output_parent_folder_id | outputParentFolderId (Optional, can also be specified on cli)
          * output_parent_folder_path | outputParentFolderPath (Optional, can also be specified on cli, will be created if it doesn't exist)
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
                                                             then --pipeline-id takes precedence

    --output-parent-folder-id=<output_parent_folder_id>      Optional, the id of the parent folder to write outputs to
    --output-parent-folder-path=<output_parent_folder_path>  Optional, the path to the parent folder to write outputs to (will be created if it doesn't exist)
                                                             Cannot specify both --output-parent-folder-id AND --output-parent-folder-path

    --analysis-storage-id=<analysis_storage_id>              Optional, analysis storage id, overrides default analysis storage size
    --analysis-storage-size=<analysis_storage_size>          Optional, analysis storage size, one of Small, Medium, Large
                                                             If both --analysis-storage-id AND --analysis-storage-size are specified,
                                                             then --analysis-storage-id takes precedence

    --activation-id=<activation_id>                          Optional, the activation id used by the pipeline analysis

    --create-cwl-analysis-json-output-path=<output_path>     Optional, Path to output a json file that contains the body for a create cwl analysis (https://ica.illumina.com/ica/api/swagger/index.html#/Project%20Analysis/createCwlAnalysis)
                                                             Useful for reproducibility and debugging

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
        self.pipeline_id: Optional[str] = None
        self.project_id: Optional[str] = None
        self.output_parent_folder_id: Optional[str] = None
        self.analysis_storage_id: Optional[str] = None
        self.activation_id: Optional[str] = None
        self.create_cwl_analysis_json_output_path: Optional[Path] = None

        super().__init__(command_argv)

    def __call__(self):
        self.launch_workflow()

    def check_args(self):
        # Assign the args

        # Get launch yaml path
        self.launch_yaml_path = self.args.get("--launch-yaml", None)
        if self.launch_yaml_path is None:
            logger.error("Please specify launch yaml for input")
            raise InvalidArgumentError
        self.input_launch_json: ICAv2LaunchJson = self.read_launch_yaml()

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

        if self.analysis_storage_id is not None:
            self.input_launch_json.update_engine_parameter(
                "analysis_storage_id", self.output_parent_folder_id
            )
        if self.activation_id is not None:
            self.input_launch_json.update_engine_parameter(
                "activation_id", self.output_parent_folder_id
            )

        # Get the project id
        self.project_id = get_project_id()

        # Get the pipeline id
        pipeline_id_arg = self.args.get("--pipeline-id", None)
        pipeline_code_arg = self.args.get("--pipeline-code", None)

        if pipeline_id_arg is not None:
            self.pipeline_id = pipeline_id_arg
        elif pipeline_code_arg is not None:
            self.pipeline_id = get_pipeline_id_from_pipeline_code(
                project_id=self.project_id,
                pipeline_code=pipeline_code_arg
            )
        else:
            logger.error("Must specify one of --pipeline-id or --pipeline-code")
            raise InvalidArgumentError

        # Get the output parent folder id
        output_parent_folder_arg = self.args.get("--output-parent-folder-id", None)
        output_parent_folder_path_arg = self.args.get("--output-parent-folder-path", None)

        if output_parent_folder_arg is not None:
            self.output_parent_folder_id = output_parent_folder_arg
        elif output_parent_folder_path_arg is not None:
            if not output_parent_folder_path_arg.endswith("/"):
                output_parent_folder_path_arg += "/"
            if not check_is_directory(
                project_id=self.project_id,
                folder_path=output_parent_folder_path_arg
            ):
                self.output_parent_folder_id = create_data_in_project(
                    project_id=self.project_id,
                    data_path=output_parent_folder_path_arg
                ).data.id

        if self.output_parent_folder_id is not None:
            self.input_launch_json.update_engine_parameter(
                "output_parent_folder_id", self.output_parent_folder_id
            )

        # Get the analysis storage id
        analysis_storage_id_arg = self.args.get("--analysis-storage-id", None)
        analysis_storage_size_arg = self.args.get("--analysis-storage-size", None)

        if analysis_storage_id_arg is not None:
            self.analysis_storage_id = analysis_storage_id_arg
        elif analysis_storage_size_arg is not None:
            self.analysis_storage_id = get_analysis_storage_id_from_analysis_storage_size(analysis_storage_size_arg)

        if self.analysis_storage_id is not None:
            self.input_launch_json.update_engine_parameter(
                "analysis_storage_id", self.analysis_storage_id
            )

        # Get the activation id
        self.activation_id = self.args.get("--activation-id", None)

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
                create_analysis_h.write(json.dumps(recursively_build_open_api_body_from_libica_item(cwl_analysis), indent=2))
                create_analysis_h.write("\n")

        # Launch workflow
        logger.info("Launching analysis")
        analysis_id, user_reference = launch_cwl_workflow(
            project_id=self.project_id,
            cwl_analysis=cwl_analysis
        )

        logger.info(f"Successfully launched analysis pipeline '{self.pipeline_id}' with analysis id '{analysis_id}' and user reference '{user_reference}'")

    def read_launch_yaml(self) -> ICAv2LaunchJson:
        # Import json object
        yaml_obj = YAML()
        with open(self.launch_yaml_path, "r") as yaml_h:
            return ICAv2LaunchJson.from_dict(yaml_obj.load(yaml_h))
