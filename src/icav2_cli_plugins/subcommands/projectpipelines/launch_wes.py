#!/usr/bin/env python3

"""
Launch a workflow through CWL WES
"""

# External data
import json
from collections import OrderedDict
from tempfile import NamedTemporaryFile
from typing import Optional, List, Union, Dict
from ruamel.yaml import YAML
from pathlib import Path

# Wrapica
from wrapica.data import get_project_data_obj_from_data_id
from wrapica.enums import WorkflowLanguage
from wrapica.project_analysis import Analysis
from wrapica.project_pipelines import (
    ProjectPipeline,
    AnalysisStorage,
    ICAv2CwlAnalysisJsonInput,
    ICAv2CWLPipelineAnalysis,
    ICAv2PipelineAnalysisTags,
    coerce_analysis_storage_id_or_size_to_analysis_storage, coerce_pipeline_id_or_code_to_project_pipeline_obj,
    get_default_analysis_storage_obj_from_project_pipeline,
    ICAv2NextflowAnalysisInput
)
from wrapica.project_data import ProjectData, coerce_data_id_icav2_uri_or_path_to_project_data_obj, \
    convert_project_data_obj_to_icav2_uri, write_icav2_file_contents
from wrapica.utils.nextflow_helpers import generate_samplesheet_file_from_input_dict, \
    download_nextflow_schema_input_json_from_pipeline_id

# Get utils
from ...utils.errors import InvalidArgumentError
from ...utils.config_helpers import get_project_id
from ...utils.logger import get_logger

# Locals
from .. import Command, DocOptArg

# Set logger
logger = get_logger()


class ProjectPipelinesStartWES(Command):
    """Usage:
    icav2 projectpipelines start-wes help
    icav2 projectpipelines start-wes (--launch-yaml=<launch_yaml>)
                                     [--user-reference=<user_reference>]
                                     [--pipeline=<pipeline_id_or_code>]
                                     [--analysis-output=<analysis_output_uri_or_path>]
                                     [--ica-logs=<ica_logs_uri_or_path>]
                                     [--analysis-storage=<analysis_storage_size_or_path>]
                                     [--activation-id=<activation_id>]
                                     [--user-tag=<user_tag>]...
                                     [--reference-tag=<reference_tag>]...
                                     [--technical-tag=<technical_tag>]...
                                     [--idempotency-key=<idempotency_key>]
                                     [--create-analysis-json-output-path=<output_path>]
                                     [--json]

Description:
    Launch an analysis on icav2.
    Please refer to 'icav2 projectpipelines create-wes-input-template' documentation for generating the launch yaml file

    Your launch yaml must contain the following keys:
      * user_reference (the name of the pipeline analysis run - can also be specified on the cli)
      * inputs (the CWL or Nextflow input json dict)
      * engine_parameters:
        * Which comprises the following keys:
          * pipeline ( Optional, pipeline id or code can also be specified on the cli)
          * analysis_output ( Optional, analysis output can also be specified on the cli)
          * ica_logs ( Optional, can also be specified on cli) :construction: ICAv2 doesn't support this with analysis_output also present.
          * user_tags (Optional, a dictionary or array of user tags to attach to this analysis)
          * technical_tags (Optional, a dictionary or array of technical tags to attach to this analysis)
          * reference_tags (Optional array of reference tags to attach to this analysis)
          * analysis_storage (Optional, can also be specified on cli or will use pipeline default)
          * activation_id (Optional, can also be specified on cli or will be generated by this command)
          * cwltool_overrides (Optional, used to override keys in the analysis, can also be specified in input as "cwltool:overrides")
          * stream_all_files (Optional, CWL Only, convert all files in the inputs to presigned url - coming soon)  :construction:
          * stream_all_directories (Optional, CWL Only convert all directories in the inputs to presigned urls - coming soon) :construction:

    When specifying files or directories in your inputs key in the launch yaml, you can set the location attribute to the following URI syntax:
      * icav2://project_id/data_path or
      * icav2://project_name/data_path

    These will then be mounted into your analysis at runtime.

Options:
    --launch-yaml=<launch_yaml>                              Required, input json similar to v1

    --user-reference=<user_reference>                        Optional, user reference for the analysis
                                                             Must either specify user reference on the CLI or in the launch yaml

    --pipeline=<pipeline_id_or_code>                         Optional, pipeline id or code of the pipeline you wish to launch
                                                             Must either specify pipeline on the CLI or in the launch yaml

    --analysis-output=<analysis_output_uri>                  Optional, the uri or path to where the analysis directory out/ is placed.
                                                             Use icav2://project-name-or-id/path/to/out/ or a regular path
                                                             Must either specify analysis output on the CLI or in the launch yaml
    --ica-logs=<ica_logs_path_or_uri>                        Optional, the uri to where the directory ica_logs/ is placed.
                                                             Use icav2://project-name-or-id/path/to/logs/ as a value
                                                             Must either specify ica logs on the CLI or in the launch yaml
    --cache=<cache>                                          Optional, the uri or path to where the analysis cache is placed.
                                                             For nextflow pipelines this directory is used to place the samplesheet_input.csv
                                                             Use icav2://project-name-or-id/path/to/cache/ or a regular path
                                                             Must either specify cache on the CLI or in the launch yaml

    --analysis-storage=<analysis_storage_id_or_size>         Optional, analysis storage id or size, overrides default analysis storage size
                                                             If not specified on the CLI or in the launch yaml, then the pipeline default is used

    --activation-id=<activation_id>                          Optional, the activation id used by the pipeline analysis.
                                                             If not specified on the CLI or in the launch yaml, then this is retrieved
                                                             from the /api/activationCodes/findBestMatchingFor<WorkflowLanguage> endpiont

    --user-tag=<user_tag>                                    Optional, user tags to attach to this analysis, can be specified multiple times
                                                             If user tags already exist in the launch yaml, then these will be appeneded
    --technical-tag=<technical_tag>                          Optional, technical tags to attach to this analysis, can be specified multiple times
                                                             If technical tags already exist in the launch yaml, then these will be appeneded
    --reference-tag=<reference_tag>                          Optional, reference tags to attach to this analysis, can be specified multiple times
                                                             If reference tags already exist in the launch yaml, then these will be appeneded

    --idempotency-key=<idempotency_key>                      Optional, idempotency key for the analysis run

    --create-analysis-json-output-path=<output_path>         Optional, Path to output a json file that contains the body for
                                                             a create analysis (https://ica.illumina.com/ica/api/swagger/index.html#/Project%20Analysis/createCwlAnalysis)
                                                             Useful for reproducibility and debugging
    --json                                                   Optional, Write json to stdout, useful for debugging

Environment:
    ICAV2_BASE_URL (optional, defaults to ica.illumina.com)
    ICAV2_PROJECT_ID (optional, taken from ~/.session.ica.yaml otherwise)

Example:
    icav2 projectpipelines start-cwl-wes --launch-yaml /path/to/input.yaml
    """

    launch_yaml_path: Path
    pipeline_obj: Optional[ProjectPipeline]
    analysis_output_obj: Optional[ProjectData]
    ica_logs_obj: Optional[ProjectData]
    cache_obj: Optional[ProjectData]
    analysis_storage_obj: Optional[AnalysisStorage]
    activation_id: Optional[str]
    user_tags: Optional[List[str]]
    technical_tags: Optional[List[str]]
    reference_tags: Optional[List[str]]
    create_analysis_json_output_path: Optional[Path]
    is_json: Optional[bool]

    def __init__(self, command_argv):
        self._docopt_type_args = {
            "launch_yaml_path": DocOptArg(
                cli_arg_keys=["--launch-yaml"],
            ),
            "pipeline_obj": DocOptArg(
                cli_arg_keys=["--pipeline"],
            ),
            "analysis_output_obj": DocOptArg(
                cli_arg_keys=["--analysis-output"],
                config={
                    "create_data_if_not_found": True
                }
            ),
            "ica_logs_obj": DocOptArg(
                cli_arg_keys=["--ica-logs"],
                config={
                    "create_data_if_not_found": True
                }
            ),
            "cache_obj": DocOptArg(
                cli_arg_keys=["--cache"],
                config={
                    "create_data_if_not_found": True
                }
            ),
            "analysis_storage_obj": DocOptArg(
                cli_arg_keys=["--analysis-storage"],
            ),
            "activation_id": DocOptArg(
                cli_arg_keys=["--activation-id"],
            ),
            "user_tags": DocOptArg(
                cli_arg_keys=["--user-tag"],
            ),
            "technical_tags": DocOptArg(
                cli_arg_keys=["--technical-tag"],
            ),
            "reference_tags": DocOptArg(
                cli_arg_keys=["--reference-tag"],
            ),
            "create_analysis_json_output_path": DocOptArg(
                cli_arg_keys=["--create-analysis-json-output-path"],
            ),
            "is_json": DocOptArg(
                cli_arg_keys=["--json"],
            ),
        }
        # Initialise parameters
        self.project_id: Optional[str] = None
        self.user_reference: Optional[str] = None
        self.workflow_language: Optional[WorkflowLanguage] = None

        self.analysis_input_obj: Optional[ICAv2CwlAnalysisJsonInput] = None
        self.analysis_obj: Optional[ICAv2CWLPipelineAnalysis] = None
        self.analysis_id: Optional[str] = None

        super().__init__(command_argv)

    def __call__(self):
        self.launch_workflow()

    def check_args(self):
        # Get the project id
        self.project_id = get_project_id()

        # Read launch yaml
        if not self.launch_yaml_path.is_file():
            logger.error("Could not get file {self.launch_yaml}")
            raise InvalidArgumentError

        # Import yaml object
        yaml_obj = YAML()
        with open(self.launch_yaml_path, "r") as yaml_h:
            launch_yaml_dict: OrderedDict = yaml_obj.load(yaml_h)

        # Get the pipeline object
        if self.pipeline_obj is None:
            # Get the pipeline object from the launch yaml engine parameters
            pipeline_yaml: str | None = launch_yaml_dict.get("engine_parameters", {}).get("pipeline", None)
            if pipeline_yaml is None:
                logger.error("Pipeline not specified on cli or in the launch yaml")
                raise InvalidArgumentError

            self.pipeline_obj = coerce_pipeline_id_or_code_to_project_pipeline_obj(
                pipeline_yaml
            )

        # Get pipeline workflow type
        self.workflow_language = WorkflowLanguage(self.pipeline_obj.pipeline.language)

        # Set the user reference
        if self.user_reference is None:
            # Get the user reference from the launch yaml
            user_reference_yaml: str | None = launch_yaml_dict.get("user_reference", None)
            if user_reference_yaml is None:
                logger.error("User reference not specified on the cli or in the launch yaml")
                raise InvalidArgumentError
            self.user_reference = user_reference_yaml

        # Get the analysis output
        if self.analysis_output_obj is None:
            # Get the pipeline object from the launch yaml engine parameters
            analysis_output_yaml: str | None = launch_yaml_dict.get("engine_parameters", {}).get("analysis_output", None)
            if analysis_output_yaml is None:
                logger.error("Analysis Output not specified on cli or in the launch yaml")
                raise InvalidArgumentError

            self.analysis_output_obj = coerce_data_id_icav2_uri_or_path_to_project_data_obj(
                analysis_output_yaml,
                create_data_if_not_found=True
            )

        # Get the ica logs
        if self.ica_logs_obj is None:
            # Get the pipeline object from the launch yaml engine parameters
            ica_logs_yaml: str | None = launch_yaml_dict.get("engine_parameters", {}).get("ica_logs", None)
            if ica_logs_yaml is None:
                logger.error("ICA Logs not specified on cli or in the launch yaml")
                raise InvalidArgumentError

            self.ica_logs_obj = coerce_data_id_icav2_uri_or_path_to_project_data_obj(
                ica_logs_yaml,
                create_data_if_not_found=True
            )

        if self.cache_obj is None and self.workflow_language == WorkflowLanguage.NEXTFLOW:
            # Get the pipeline object from the launch yaml engine parameters
            cache_yaml: str | None = launch_yaml_dict.get("engine_parameters", {}).get("cache", None)
            if cache_yaml is None:
                logger.error("Cache not specified on cli or in the launch yaml")
                raise InvalidArgumentError

            self.cache_obj = coerce_data_id_icav2_uri_or_path_to_project_data_obj(
                cache_yaml,
                create_data_if_not_found=True
            )

        # Get the analysis storage
        if self.analysis_storage_obj is None:
            analysis_storage_yaml: str | None = launch_yaml_dict.get("engine_parameters", {}).get("analysis_storage", None)
            if analysis_storage_yaml is None:
                self.analysis_storage_obj = get_default_analysis_storage_obj_from_project_pipeline(
                    project_id=self.project_id,
                    pipeline_id=self.pipeline_obj.pipeline.id
                )
            else:
                self.analysis_storage_obj = coerce_analysis_storage_id_or_size_to_analysis_storage(
                    analysis_storage_yaml
                )

        # Check if activation ID is set?
        if self.activation_id is None:

            activation_id_yaml: str | None = launch_yaml_dict.get("engine_parameters", {}).get("activation_id", None)
            if activation_id_yaml is None:
                self.activation_id = activation_id_yaml

        # Check if user tags are set in the launch yaml
        if self.user_tags is None:
            self.user_tags = []
        user_tags_yaml: List[Union[str, Dict]] | None = launch_yaml_dict.get("engine_parameters", {}).get("user_tags", None)
        if user_tags_yaml is not None:
            self.user_tags.extend(user_tags_yaml)

        # Check if technical tags are set in the launch yaml
        if self.technical_tags is None:
            self.technical_tags = []
        technical_tags_yaml: List[Union[str, Dict]] | None = launch_yaml_dict.get("engine_parameters", {}).get("technical_tags", None)
        if technical_tags_yaml is not None:
            self.technical_tags.extend(technical_tags_yaml)

        # Check if technical tags are set in the launch yaml
        if self.reference_tags is None:
            self.reference_tags = []
        reference_tags_yaml: List[Union[str, Dict]] | None = launch_yaml_dict.get("engine_parameters", {}).get("reference_tags", None)
        if reference_tags_yaml is not None:
            self.reference_tags.extend(reference_tags_yaml)

        # Check if create analysis json output path is set and if parent exists
        if self.create_analysis_json_output_path is not None:
            if not self.create_analysis_json_output_path.parent.is_dir():
                logger.error("Please ensure the parent directory of the --create-analysis-json-output-path parameter exists")
                raise InvalidArgumentError

        # Collect Dict
        inputs_dict: Dict | None = launch_yaml_dict.get("inputs", None)
        if inputs_dict is None:
            logger.error("Could not get the inputs dict from the launch yaml")
            raise InvalidArgumentError

        # Generate input launch json
        if self.workflow_language == WorkflowLanguage.CWL:
            # Initialise the analysis
            from wrapica.project_pipelines import ICAv2CWLPipelineAnalysis as ICAv2PipelineAnalysis
            # Check if the cwltool_overrides are set in the launch yaml - if so extend them into the inputs dict
            if "cwltool_overrides" in launch_yaml_dict.get("engine_parameters", {}):
                inputs_dict.update(
                    {
                        "cwltool:overrides": launch_yaml_dict.get("engine_parameters", {}).get("cwltool_overrides")
                    }
                )

            self.analysis_input_obj: ICAv2CwlAnalysisJsonInput = ICAv2CwlAnalysisJsonInput(
                inputs_dict
            )
        else:  # Nextflow
            # Initialise the analysis
            from wrapica.project_pipelines import ICAv2NextflowPipelineAnalysis as ICAv2PipelineAnalysis
            if "samplesheet_input" in inputs_dict.keys():
                # First we need to update samplesheet_input to input
                samplesheet_tmp_obj = NamedTemporaryFile(prefix="samplesheet_input_", suffix=".csv")
                samplesheet_tmp_path = Path(samplesheet_tmp_obj.name)

                schema_input_json_file_tmp_obj = NamedTemporaryFile(delete=False, prefix='schema_input', suffix=".json")
                schema_input_json_file_path = Path(schema_input_json_file_tmp_obj.name)

                # Download the schema input json
                download_nextflow_schema_input_json_from_pipeline_id(
                    pipeline_id=self.pipeline_obj.pipeline.id,
                    schema_input_json_path=schema_input_json_file_path
                )

                # Generate the samplesheet file
                generate_samplesheet_file_from_input_dict(
                    samplesheet_dict=inputs_dict["samplesheet_input"],
                    schema_input_path=schema_input_json_file_path,
                    samplesheet_path=samplesheet_tmp_path
                )

                # Upload the samplesheet file to icav2
                samplesheet_input_file_id = write_icav2_file_contents(
                    project_id=self.cache_obj.project_id,
                    data_path=Path(self.cache_obj.data.details.path) / "samplesheet_input.csv",
                    file_stream_or_path=samplesheet_tmp_path
                )

                # Now pop the samplesheet_input and instead set 'input' as a file id, set to the samplesheet file
                _ = inputs_dict.pop("samplesheet_input")
                # Coerce file id into icav2 uri
                inputs_dict["input"] = convert_project_data_obj_to_icav2_uri(
                    get_project_data_obj_from_data_id(
                        samplesheet_input_file_id
                    )
                )

            self.analysis_input_obj: ICAv2NextflowAnalysisInput = ICAv2NextflowAnalysisInput(
                inputs_dict,
                project_id=self.project_id,
                pipeline_id=self.pipeline_obj.pipeline.id
            )

        # Initialise the analysis
        self.analysis_obj = ICAv2PipelineAnalysis(
            user_reference=self.user_reference,
            project_id=self.project_id,
            pipeline_id=self.pipeline_obj.pipeline.id,
            analysis_input=self.analysis_input_obj.create_analysis_input(),
            analysis_output_uri=convert_project_data_obj_to_icav2_uri(self.analysis_output_obj),
            ica_logs_uri=convert_project_data_obj_to_icav2_uri(self.ica_logs_obj),
            tags=ICAv2PipelineAnalysisTags(
                user_tags=self.user_tags,
                technical_tags=self.technical_tags,
                reference_tags=self.reference_tags
            )
        )
        #
        # # Update the engine parameter
        # self.analysis_obj.engine_parameters.update_engine_parameter(
        #     "pipeline_id", self.pipeline_id
        # )
        #
        # # Get the analysis storage arg
        # if self.analysis_storage_arg is not None:
        #     self.analysis_storage_id = coerce_analysis_storage_id_or_size_to_analysis_storage(self.analysis_storage_arg)
        # if self.analysis_storage_id is not None:
        #     self.analysis_obj.engine_parameters.update_engine_parameter(
        #         "analysis_storage_id", self.analysis_storage_id
        #     )
        #
        # # Check activation id
        # if self.activation_id is not None:
        #     self.analysis_obj.engine_parameters.update_engine_parameter(
        #         "activation_id", self.activation_id
        #     )
        #
        # # Get the --json parameter
        # if self.args.get("--json", False):
        #     self.is_output_json = True
        # else:
        #     self.is_output_json = False

    def launch_workflow(self):
        logger.info("Launching analysis")
        analysis_launch_obj: Analysis = self.analysis_obj()
        self.analysis_id = analysis_launch_obj.id
        if self.create_analysis_json_output_path is not None:
            logger.info(f"Dumping launch analysis payload to {self.create_analysis_json_output_path}")
            self.analysis_obj.save_analysis(self.create_analysis_json_output_path)

        logger.info(
            f"Successfully launched analysis pipeline '{self.pipeline_obj.pipeline.id}' "
            f"with analysis id '{self.analysis_id}' and user reference '{analysis_launch_obj.user_reference}'")

        if self.is_json:
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