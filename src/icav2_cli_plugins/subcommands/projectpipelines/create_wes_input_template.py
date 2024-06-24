#!/usr/bin/env python3

"""
Given a pipeline id or pipeline code, create a wes input template that comprises the following items

* user reference (or name)
* inputs
* engine parameters
"""

# Standard imports
import sys
from tempfile import NamedTemporaryFile
from typing import Optional, List
from urllib.parse import urlparse
from ruamel.yaml import YAML, CommentedMap
from pathlib import Path

# Wrapica import
from wrapica.enums import WorkflowLanguage
from wrapica.project_analysis import AnalysisStorage
from wrapica.utils.cwl_typing_helpers import WorkflowType
from wrapica.project_pipelines import (
    ProjectPipeline,
)
from wrapica.pipelines import (
    get_cwl_obj_from_pipeline_id
)
from wrapica.utils.cwl_helpers import (
    create_template_from_workflow_inputs,
    get_overrides_from_workflow_steps
)
from wrapica.utils.nextflow_helpers import (
    download_nextflow_schema_file_from_pipeline_id,
    generate_input_yaml_from_schema_json,
    generate_samplesheet_yaml_template_from_schema_input,
    download_nextflow_schema_input_json_from_pipeline_id
)

# From utils
from ...utils.errors import InvalidArgumentError
from ...utils.config_helpers import get_project_id
from ...utils.logger import get_logger

# Locals
from .. import Command, DocOptArg

# Get logger
logger = get_logger()


class ProjectPipelinesCreateWESInputTemplate(Command):
    """Usage:
    icav2 projectpipelines create-wes-input-template help
    icav2 projectpipelines create-wes-input-template (--pipeline=<pipeline_id_or_code>)
                                                     (--user-reference=<user_reference>)
                                                     [--analysis-output=<analysis_output_uri_or_path>]
                                                     [--ica-logs=<ica_logs_uri_or_path>]
                                                     [--cache=<cache_uri_or_path>]
                                                     [--analysis-storage=<analysis_storage_id_or_size>]
                                                     [--activation_id=<activation_id>]
                                                     [--user-tag=<user_tag>]...
                                                     [--technical-tag=<technical_tag>]...
                                                     [--reference-tag=<reference_tag>]...
                                                     [--idempotency-key=<idempotency_key>]
                                                     [--output-template-yaml-path=<output_template_yaml_path>]
    icav2 projectpipelines create-wes-input-template (--cli-input-yaml=<path_to_cli_input_yaml>)
                                                     [--pipeline=<pipeline_id_or_code>]
                                                     [--user-reference=<user_reference>]
                                                     [--analysis-output=<analysis_output_uri_or_path>]
                                                     [--ica-logs=<ica_logs_uri_or_path>]
                                                     [--cache=<cache_uri_or_path>]
                                                     [--analysis-storage=<analysis_storage_id_or_size>]
                                                     [--activation_id=<activation_id>]
                                                     [--user-tag=<user_tag>]...
                                                     [--technical-tag=<technical_tag>]...
                                                     [--reference-tag=<reference_tag>]...
                                                     [--output-template-yaml-path=<output_template_yaml_path>]


Description:
    Create a WES input template for a CWL or Nextflow pipeline ready for launching on the ICAv2 platform.

    One can either use the --cli-input-yaml parameter to generate the input template, or specify the options on the commandline.
    The yaml keys for the cli input yaml will match the long form commandline options (except for the tag options which contain a plural).
    An example input yaml might look like this:

    pipeline: my-tabix-workflow
    user_reference: tabix-analysis-test
    analysis_output_uri: icav2://project-id/path/to/output/
    analysis_logs_uri: icav2://project-id/path/to/logs/
    analysis_storage: Small
    user_tags:
      - user_tag1
      - user_tag2
    technical_tags:
         - technical_tag1

    Will generate an output template yaml file that can be used to launch a WES analysis on the ICAv2 platform with the icav2 projectpipelines start-wes command.

    The output template yaml file will contain the following attributes:
      * user_reference (the name of the pipeline analysis run)
      * inputs (the input json dict - we use a JSON dict for both CWL and Nextflow pipelines)
      * engine_parameters
        * Which comprises the following keys:
          * pipeline (the pipeline id or code)
          * analysis_output (Optional, the uri or path to where the final directory out/ is placed)
          * ica_logs (Optional, the uri or path to where the final directory ica_logs/ is placed)
          * cache (Optional, used by nextflow pipelines to upload the samplesheet input file)
          * tags (Optional, a dictionary of lists with the following keys)
            * technical_tags | technicalTags  (Optional array of technical tags to attach to this pipeline analysis)
            * user_tags | userTags (Optional array of user tags to attach to this pipeline analysis)
            * reference_tags | referenceTags (Optional array of reference tags to attach to this pipeline analysis)
          * analysis_storage_id
          * activation_id

    If this is a nextflow pipeline that uses a samplesheet input, the template will provide the samplesheet input as a dict instead of a file.
    When values are populated into this dict and launched via start-wes, the samplesheet input will be uploaded to the cache directory before the pipeline is run.
    Any attributes in the samplesheet input that are icav2 uris will first be presigned before being uploaded to the cache directory.


Options:
    --pipeline=<pipeline_id_or_code>                         Optional, id (or code) of the pipeline you wish to launch
    --user-reference=<user_reference>                        Optional, name of the workflow analysis

    --analysis-output=<analysis_output_uri_or_path>          Optional, the uri or project path to where the final directory out/ is placed.
                                                             Must be specified either here or when launched with launch-wes
    --ica-logs=<ica_logs_uri_or_path>                        Optional, the uri or project path to where the final directory ica_logs/ is placed.
                                                             Must be specified either here or when launched with launch-wes
    --cache=<cache_uri_or_path>                              Optional, used by nextflow pipelines to upload the samplesheet input file
                                                             Must be specified here or with launch-wes when pipeline lanugage is nextflow

    --analysis-storage=<analysis_storage_id_or_size>         Optional, analysis storage id or size, overrides default analysis storage size

    --activation-id=<activation_id>                          Optional, the activation id used by the pipeline analysis
                                                             This can also be inferred at runtime.
                                                             If not specified, this will not be set in the engine parameters

    --user-tag=<user_tag>                                    User tags to attach to the analysis pipeline, specify multiple times for multiple user tags
    --technical-tag=<technical_tag>                          User tags to attach to the analysis pipeline, specify multiple times for multiple technical tags
    --reference-tag=<reference_tag>                          User tags to attach to the analysis pipeline, specify multiple times for multiple reference tags

    --idempotency-key=<idempotency_key>                      Optional, idempotency key for the analysis run, can also be set at runtime with the start-wes command

    --output-template-yaml-path=<output_template_yaml_path>  Optional, output template yaml path, parent directory must exist.
                                                             If not specified or set as '-' then output will be written to stdout

Environment variables:
    ICAV2_BASE_URL           Optional, default set as https://ica.illumina.com/ica/rest
    ICAV2_PROJECT_ID         Optional, taken from "$HOME/.icav2/.session.ica.yaml" if not set
    ICAV2_ACCESS_TOKEN       Optional, taken from "$HOME/.icav2/.session.ica.yaml" if not set

Example:
    icav2 projectpipelines create-wes-input-template --user-reference tabix-analysis-test --pipeline-code tabix-workflow --output-template-yaml-path launch.wes.yaml --analysis-output-path /test_data/v2/tabix/
    """
    pipeline_obj: ProjectPipeline
    user_reference: str

    # Split options analysis-output-uri, analysis-output-path
    # Leave as is since this is only making the template
    analysis_output: Optional[str]

    # Split options ica logs uri
    ica_logs: Optional[str]

    # Cache uri
    cache: Optional[str]

    # Analysis storage
    analysis_storage: Optional[AnalysisStorage]

    # Activation ID - rarely set here
    activation_id: Optional[str]

    # Tags
    user_tags: Optional[List[str]]
    technical_tags: Optional[List[str]]
    reference_tags: Optional[List[str]]

    # Idempotency key - useful for retrying an analysis
    idempotency_key: Optional[str]

    # Output template yaml path
    output_template_yaml_path: Optional[Path]

    def __init__(self, command_argv):
        # CLI Args
        self._docopt_type_args = {
            "pipeline_obj": DocOptArg(
                cli_arg_keys=["--pipeline"],
            ),
            "user_reference": DocOptArg(
                cli_arg_keys=["--user-reference"],
            ),
            "analysis_output": DocOptArg(
                cli_arg_keys=["--analysis-output"],
            ),
            "ica_logs": DocOptArg(
                cli_arg_keys=["--ica-logs"],
            ),
            "cache": DocOptArg(
                cli_arg_keys=["--cache"],
            ),
            "analysis_storage": DocOptArg(
                cli_arg_keys=["--analysis-storage"],
            ),
            "activation_id": DocOptArg(
                cli_arg_keys=["--activation-id"],
            ),
            "user_tags": DocOptArg(
                cli_arg_keys=["--user-tag"],
                yaml_arg_keys=["user_tags"]
            ),
            "technical_tags": DocOptArg(
                cli_arg_keys=["--technical-tag"],
                yaml_arg_keys=["technical_tags"]
            ),
            "reference_tags": DocOptArg(
                cli_arg_keys=["--reference-tag"],
                yaml_arg_keys=["reference_tags"]
            ),
            "idempotency_key": DocOptArg(
                cli_arg_keys=["--idempotency-key"],
            ),
            "output_template_yaml_path": DocOptArg(
                cli_arg_keys=["--output-template-yaml-path"],
            )
        }

        # Initialise args
        self.project_id: Optional[str] = None
        self.workflow_language: Optional[WorkflowLanguage] = None
        self.cwl_obj: Optional[WorkflowType] = None

        super().__init__(command_argv)

    def __call__(self):
        self.write_output_wes_template()

    # def __exit__(self):
    #     os.remove(self.html_doc)
    #

    # def set_html_doc(self):
    #     self.html_doc = Path(NamedTemporaryFile(delete=False, suffix=".html").name)
    #     get_release_markdown_file_doc_as_html(
    #         repo=self.release_repo,
    #         tag_name=self.release_tag,
    #         output_path=self.html_doc
    #     )

    # def get_release_url(self):
    #     url_match_obj = GITHUB_RELEASE_DESCRIPTION_REGEX_MATCH.match(
    #         self.pipeline_description
    #     )
    #     if url_match_obj is None:
    #         return None
    #     return url_match_obj.group(1)

    def get_input_template_as_commented_map(self) -> CommentedMap:
        if self.workflow_language == WorkflowLanguage.CWL:
            self.cwl_obj: WorkflowType
            # Get inputs template from pipeline object
            return create_template_from_workflow_inputs(self.cwl_obj.inputs)
        else:
            # FIXME - provide alternative way if the
            # FIXME - workflow is 'private' and we cannot get the schema from a file
            # Download the schema json file from the pipeline object
            schema_json_file_tmp_obj = NamedTemporaryFile(delete=False, prefix='nextflow_schema', suffix=".json")
            schema_json_file_path = Path(schema_json_file_tmp_obj.name)
            download_nextflow_schema_file_from_pipeline_id(
                pipeline_id=self.pipeline_obj.pipeline.id,
                schema_json_path=schema_json_file_path
            )

            # Generate the input template from the schema json file
            nf_yaml_template = generate_input_yaml_from_schema_json(schema_json_file_path)

            # Update the samplesheet_input attribute to be a dict instead of a file
            if "input" in nf_yaml_template.keys():
                schema_input_json_file_tmp_obj = NamedTemporaryFile(delete=False, prefix='schema_input', suffix=".json")
                schema_input_json_file_path = Path(schema_input_json_file_tmp_obj.name)
                download_nextflow_schema_input_json_from_pipeline_id(
                    pipeline_id=self.pipeline_obj.pipeline.id,
                    schema_input_json_path=schema_input_json_file_path
                )
                # Rename input to samplesheet_input
                _ = nf_yaml_template.pop("input")
                nf_yaml_template["samplesheet_input"] = generate_samplesheet_yaml_template_from_schema_input(
                    schema_input_json_file_path
                )
                nf_yaml_template.yaml_set_comment_before_after_key(
                    key="samplesheet_input",
                    before="Samplesheet input, this is uploaded to the cache directory before the pipeline is run",
                    indent=4
                )

            # Return the nextflow yaml template
            return nf_yaml_template

    def get_cwltool_overrides_as_commented_map(self) -> CommentedMap:
        self.cwl_obj: WorkflowType
        return CommentedMap(get_overrides_from_workflow_steps(self.cwl_obj.steps))

    # def get_release_repo_and_tag_from_release_url(self) -> Tuple[str, str]:
    #     """
    #     Release url is like https://github.com/umccr/cwl-ica/releases/tag/dragen-pon-qc/3.9.3__221223084424
    #     :return:
    #     """
    #     return get_release_repo_and_tag_from_release_url(self.release_url)

    def check_args(self):
        # Get project id
        self.project_id = get_project_id()

        # Get workflow language type
        self.workflow_language = WorkflowLanguage(self.pipeline_obj.pipeline.language)

        if self.workflow_language == WorkflowLanguage.CWL:
            self.cwl_obj = get_cwl_obj_from_pipeline_id(self.pipeline_obj.pipeline.id)

        # Get yaml path
        if self.output_template_yaml_path is None or self.output_template_yaml_path == "-":
            self.output_template_yaml_path: int = sys.stdout.fileno()
        elif not self.output_template_yaml_path.parent.is_dir():
            logger.error(f"Please ensure parent directory of "
                         f"--output-template-yaml-path parameter {self.output_template_yaml_path} is set")
            raise InvalidArgumentError
        elif self.output_template_yaml_path.is_dir():
            logger.error(f"Cannot create file at {self.output_template_yaml_path}, is a directory")
            raise InvalidArgumentError

    def get_engine_parameters_as_commented_map(self):
        # Initialise commented map
        engine_parameters_map = CommentedMap({
            "pipeline": self.pipeline_obj.pipeline.id
        })
        # Add pipeline code as a comment
        engine_parameters_map.yaml_add_eol_comment(
            key="pipeline",
            comment=self.pipeline_obj.pipeline.code
        )

        # Additional keys
        additional_keys = {}

        # Add in the analysis output
        if self.analysis_output is not None:
            if urlparse(self.analysis_output).scheme == "":
                # We have an analysis path, not a uri
                engine_parameters_map.update({
                    "analysis_output": str(Path(self.analysis_output)) + "/"
                })
            else:
                engine_parameters_map.update({
                    "analysis_output": self.analysis_output
                })

        # Add in the ica logs
        if self.ica_logs is not None:
            if urlparse(self.ica_logs).scheme == "":
                # We have an ica logs path, not a uri
                engine_parameters_map.update({
                    "ica_logs": str(Path(self.ica_logs)) + "/"
                })
            else:
                engine_parameters_map.update({
                    "ica_logs": self.ica_logs
                })

        # Add in the cache
        if self.cache is not None:
            if urlparse(self.cache).scheme == "":
                # We have a cache path not a uri
                engine_parameters_map.update({
                    "cache": str(Path(self.cache)) + "/"
                })
            else:
                engine_parameters_map.update({
                    "cache": self.cache
                })

        # Add in the analysis storage
        if self.analysis_storage is not None:
            # We have an analysis storage id
            engine_parameters_map.update({
                "analysis_storage": self.analysis_storage.id
            })
            # Add comment to the analysis storage human friendly size
            engine_parameters_map.yaml_add_eol_comment(
                key="analysis_storage",
                comment=self.analysis_storage.name
            )
        else:
            additional_keys.update(
                {
                    "analysis_storage": "Small  # Size of storage, one of Small, Medium or Large or pipeline default"
                }
            )
        # Add in the activation id
        if self.activation_id is not None:
            engine_parameters_map.update({
                "activation_id": self.activation_id
            })

        # Add in tags
        if self.user_tags is not None:
            engine_parameters_map.update({
                "user_tags": self.user_tags
            })
        else:
            additional_keys.update(
                {
                    "user_tags": "[]  # User Analysis Tags"
                }
            )
        if self.technical_tags is not None:
            engine_parameters_map.update({
                "technical_tags": self.technical_tags
            })
        else:
            additional_keys.update(
                {
                    "technical_tags": "[]  # Technical Analysis Tags"
                }
            )
        if self.reference_tags is not None:
            engine_parameters_map.update({
                "reference_tags": self.reference_tags
            })
        else:
            additional_keys.update(
                {
                    "reference_tags": "[]  # Reference Analysis Tags"
                }
            )

        if self.idempotency_key is not None:
            engine_parameters_map.update({
                "idempotency_key": self.idempotency_key
            })
        else:
            additional_keys.update(
                {
                    "idempotency_key": "''  # Idempotency key for the analysis run"
                }
            )

        if self.workflow_language == WorkflowLanguage.CWL:
            engine_parameters_map.update(
                {
                    "cwltool_overrides": None
                }
            )
            engine_parameters_map.yaml_add_eol_comment(
                key="cwltool_overrides",
                comment="Available overrides keys are: \n      # " + "\n      # ".join(
                    map(
                        lambda x: f"\"{x}\":",
                        self.get_cwltool_overrides_as_commented_map()
                    )
                )
            )

        # Create list of keys to append as comment
        additional_keys_str = "\n".join(
            f"{key}: '' # {value}"
            for key, value in additional_keys.items()
        )

        # Add keys to top of engine parameters as commented out values
        engine_parameters_map = CommentedMap(
            {
                "engine_parameters": engine_parameters_map
            }
        )
        engine_parameters_map.yaml_set_comment_before_after_key(
            "engine_parameters",
            after=additional_keys_str,
            indent=2
        )

        return engine_parameters_map

    def write_output_wes_template(self):
        # Initialise main object
        main_map: CommentedMap = CommentedMap()

        # Initialise map
        main_map.update({
            "user_reference": self.user_reference
        })
        main_map.yaml_set_comment_before_after_key(
            before="Name of analysis",
            key="user_reference"
        )

        # Inputs
        main_map.update({
            "inputs": self.get_input_template_as_commented_map()
        })
        main_map.yaml_set_comment_before_after_key(
            before="Inputs JSON Body",
            key="inputs"
        )

        # Engine parameters map
        main_map.update(self.get_engine_parameters_as_commented_map())
        main_map.yaml_set_comment_before_after_key(
            before="Engine Parameters",
            key="engine_parameters"
        )

        # Write output to file path
        with open(self.output_template_yaml_path, "w") as file_h:
            yaml = YAML()
            yaml.indent = 4
            yaml.block_seq_indent = 2

            yaml.dump(
                main_map, file_h
            )

