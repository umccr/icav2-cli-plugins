#!/usr/bin/env python3

"""
Given a pipeline id or pipeline code, create a wes input template that comprises the following items

* user reference (or name)
* inputs
* engine parameters
"""

# External data
import os
from fileinput import FileInput
from tempfile import NamedTemporaryFile
from typing import Optional, List, Dict, Tuple
from ruamel.yaml import YAML, CommentedMap
from pathlib import Path

# From utils
from ...utils import is_uuid_format, is_uri_format
from ...utils.errors import InvalidArgumentError
from ...utils.config_helpers import get_project_id
from ...utils.gh_helpers import (
    get_release_markdown_file_doc_as_html, get_inputs_template_from_html_doc,
    get_overrides_template_from_html_doc, get_release_repo_and_tag_from_release_url
)
from ...utils.globals import GITHUB_RELEASE_DESCRIPTION_REGEX_MATCH
from ...utils.logger import get_logger
from ...utils.projectdata_helpers import is_folder_id_format
from ...utils.projectpipeline_helpers import (
    get_project_pipeline, get_pipeline_id_from_pipeline_code,
    get_pipeline_description_from_pipeline_id
)

# Locals
from .. import Command

# Get logger
logger = get_logger()


class ProjectPipelinesCreateWESInputTemplate(Command):
    """Usage:
    icav2 projectpipelines create-cwl-wes-input-template help
    icav2 projectpipelines create-cwl-wes-input-template (--pipeline-code=<pipeline_code> | --pipeline-id=<pipeline_id>)
                                                         (--user-reference=<user_reference> | --name=<name>)
                                                         (--output-template-yaml-path=<output_template_yaml_path>)
                                                         [--output-parent-folder-path=<output_parent_folder_path> | --output-parent-folder-id=<output_parent_folder_id>]
                                                         [--analysis-output-uri=<analysis_output_uri> | --analysis-output-path=<analysis_output_path>]
                                                         [--analysis-storage-size=<analysis_storage_size> | --analysis-storage-id=<analysis_storage_id>]
                                                         [--activation_id=<activation_id>]
                                                         [--user-tag=<user_tag>]...
                                                         [--technical-tag=<technical_tag>]...
                                                         [--reference-tag=<reference_tag>]...


Description:
    Create a WES input template for a CWL workflow ready for launch

Options:
    --pipeline-id=<pipeline_id>                              Optional, id of the pipeline you wish to launch
    --pipeline-code=<pipeline_code>                          Optional, name of the pipeline you wish to launch
                                                             Must specify at least one of --pipeline-code and --pipeline-id,
                                                             If both --pipeline-id and --pipeline-code are specified,
                                                             then --pipeline-id takes precedence
    --user-reference=<user_reference>                        Optional, name of the workflow analysis
    --name=<name>                                            Optional, name of the workflow analysis
                                                             If both --user-reference and --name are specified,
                                                             then --user-reference takes precedence
    --output-template-yaml-path=<output_template_yaml_path>  Required, Output template yaml path, parent directory must exist

    --output-parent-folder-id=<output_parent_folder_id>      Optional, the id of the parent folder to write outputs to
    --output-parent-folder-path=<output_parent_folder_path>  Optional, the path to the parent folder to write outputs to (will be created if it doesn't exist)
                                                             If both --output-parent-folder-id AND --output-parent-folder-path are specified,
                                                             then --output-parent-folder-id will take precedence
                                                             If neither parameter is set, output_parent_folder_path will be blank in
                                                             the engineParameters section

    --analysis-output-uri=<analysis_output_uri>              Optional, the uri to where the final directory out/ is placed.
                                                             Can be used as an alternative to --output-parent-folder-* parameters.
                                                             Since one will not have control over the final directory name inside --output-parent-folder-*
                                                             Use icav2://project-name-or-id/path/to/out as a value
                                                             Cannot specify both --analysis-output-uri and --analysis-output-path
                                                             Cannot specify both --output-parent-folder-id/--output-parent-folder-path and --analysis0output-uri/--analysis0output-path
    --analysis-output-path=<analysis_output_path>            Optional, identical to --output-uri but assumes the current project id for your outputs.


    --analysis-storage-id=<analysis_storage_id>              Optional, analysis storage id, overrides default analysis storage size
    --analysis-storage-size=<analysis_storage_size>          Optional, analysis storage size, one of Small, Medium, Large
                                                             If both --analysis-storage-id AND --analysis-storage-size are set
                                                             then --analysis-storage-size will take precendence
                                                             If neither parameter is set, the default parameter will be retrieved
                                                             from the pipeline

    --activation-id=<activation_id>                          Optional, the activation id used by the pipeline analysis
                                                             This can also be inferred at runtime

    --user-tag=<user_tag>                                    User tags to attach to the analysis pipeline, specify multiple times for multiple user tags
    --technical-tag=<technical_tag>                          User tags to attach to the analysis pipeline, specify multiple times for multiple technical tags
    --reference-tag=<reference_tag>                          User tags to attach to the analysis pipeline, specify multiple times for multiple reference tags

Environment variables:
    ICAV2_BASE_URL           Optional, default set as https://ica.illumina.com/ica/rest
    ICAV2_PROJECT_ID         Optional, taken from "$HOME/.icav2/.session.ica.yaml" if not set
    ICAV2_ACCESS_TOKEN       Optional, taken from "$HOME/.icav2/.session.ica.yaml" if not set

Example:
    icav2 projectpipelines create-cwl-wes-input-template --user-reference tabix-analysis-test --pipeline-code tabix-workflow --output-template-yaml-path launch.wes.yaml --output-parent-folder-path /test_data/v2/tabix/
    """

    def __init__(self, command_argv):
        # Initialise args
        self.pipeline_arg: Optional[str] = None
        self.pipeline_id: Optional[str] = None

        self.project_id: Optional[str] = None

        self.pipeline_description: Optional[str] = None
        self.release_url: Optional[str] = None
        self.release_repo: Optional[str] = None
        self.release_tag: Optional[str] = None
        self.html_doc: Optional[Path] = None

        self.user_reference: Optional[str] = None
        self.output_template_yaml_path: Optional[Path] = None

        self.output_parent_folder_arg: Optional[str] = None
        self.output_parent_folder_path: Optional[Path] = None
        self.output_parent_folder_id: Optional[Path] = None

        self.analysis_output_uri_path_arg: Optional[str] = None
        self.analysis_output_uri: Optional[str] = None
        self.analysis_output_path: Optional[str] = None

        self.analysis_storage_arg: Optional[str] = None
        self.analysis_storage_size: Optional[str] = None
        self.analysis_storage_id: Optional[str] = None

        self.analysis_input_template: Optional[Dict] = None
        self.analysis_overrides_template: Optional[List] = None

        self.activation_id: Optional[str] = None

        self.user_tags: Optional[List[str]] = None
        self.technical_tags: Optional[List[str]] = None
        self.reference_tags: Optional[List[str]] = None

        super().__init__(command_argv)

        self.pipeline_obj = self.get_pipeline_obj()

        self.set_input_template()

        self.set_overrides()

    def __call__(self):
        self.write_output_wes_template()

    def __exit__(self):
        os.remove(self.html_doc)

    def set_html_doc(self):
        self.html_doc = Path(NamedTemporaryFile(delete=False, suffix=".html").name)
        get_release_markdown_file_doc_as_html(
            repo=self.release_repo,
            tag_name=self.release_tag,
            output_path=self.html_doc
        )

    def get_release_url(self):
        url_match_obj = GITHUB_RELEASE_DESCRIPTION_REGEX_MATCH.match(
            self.pipeline_description
        )
        if url_match_obj is None:
            return None
        return url_match_obj.group(1)

    def set_input_template(self):
        if self.html_doc is not None:
            self.analysis_input_template = get_inputs_template_from_html_doc(
                 self.html_doc
            )
        else:
            self.analysis_input_template = {}

    def set_overrides(self):
        if self.html_doc is not None:
            self.analysis_overrides_template = get_overrides_template_from_html_doc(
                self.html_doc
            )
        else:
            self.analysis_overrides_template = {}

    def get_release_repo_and_tag_from_release_url(self) -> Tuple[str, str]:
        """
        Release url is like https://github.com/umccr/cwl-ica/releases/tag/dragen-pon-qc/3.9.3__221223084424
        :return:
        """
        return get_release_repo_and_tag_from_release_url(self.release_url)

    def check_args(self):
        # Get project id
        self.project_id = get_project_id()

        # Set inputs from cli
        # Get user reference
        self.set_arg_from_in_input_yaml_and_cli(
            arg_name=["--user-reference", "--name"],
            input_yaml_data={},
            required=True,
            arg_type=str,
            attr_name="user_reference"
        )

        self.set_arg_from_in_input_yaml_and_cli(
            arg_name=["--pipeline-id", "--pipeline-code"],
            input_yaml_data={},
            required=True,
            arg_type=str,
            attr_name="pipeline_arg"
        )

        # Get the output folder path
        # Set output parent folder path
        self.set_arg_from_in_input_yaml_and_cli(
            arg_name=["--output-parent-folder-id", "--output-parent-folder-path"],
            input_yaml_data={},
            required=False,
            arg_type=str,
            attr_name="output_parent_folder_arg",
        )

        # Check output arg
        # Set output uri / path
        self.set_arg_from_in_input_yaml_and_cli(
            arg_name=["--analysis-output-uri", "--analysis-output-path"],
            input_yaml_data={},
            required=False,
            arg_type=str,
            attr_name="analysis_output_uri_path_arg",
        )

        # Checkout analysis storage size
        self.set_arg_from_in_input_yaml_and_cli(
            arg_name=["--analysis-storage-id", "--analysis-storage-size"],
            input_yaml_data={},
            required=False,
            arg_type=str,
            attr_name="analysis_storage_arg",
        )

        # Get pipeline id / code
        if not is_uuid_format(self.pipeline_arg):
            self.pipeline_id = get_pipeline_id_from_pipeline_code(self.project_id, self.pipeline_arg)

        # Get pipeline description
        self.pipeline_description = get_pipeline_description_from_pipeline_id(self.project_id, self.pipeline_id)

        # Set release url
        self.release_url = self.get_release_url()

        # Set release repo and tag
        if self.release_url is not None:
            self.release_repo, self.release_tag = self.get_release_repo_and_tag_from_release_url()
            # New we can set the html documentation
            self.set_html_doc()
            
        # Get yaml path
        self.output_template_yaml_path = Path(self.args.get("--output-template-yaml-path"))
        if not self.output_template_yaml_path.parent.is_dir():
            logger.error(f"Please ensure parent directory of "
                         f"--output-template-yaml-path parameter {self.output_template_yaml_path} is set")
            raise InvalidArgumentError
        if self.output_template_yaml_path.is_dir():
            logger.error(f"Cannot create file at {self.output_template_yaml_path}, is a directory")
            raise InvalidArgumentError

        # Check output uri / output path
        if self.output_parent_folder_arg is not None and self.analysis_output_uri_path_arg is not None:
            logger.error(
                "Please only specify one and only one of the "
                "output_parent_folder and output_uri/output_path parameter combinations"
            )
            raise InvalidArgumentError

        # Check output parent folder arg
        if self.output_parent_folder_arg is not None:
            if is_folder_id_format(self.output_parent_folder_arg):
                self.output_parent_folder_id = self.output_parent_folder_arg
            else:
                self.output_parent_folder_path = Path(self.output_parent_folder_arg)
                if not self.output_parent_folder_path.absolute():
                    logger.error("--output-parent-folder-path parameter should be an absolute path")
                    raise InvalidArgumentError

        if self.analysis_output_uri_path_arg is not None:
            if is_uri_format(self.analysis_output_uri_path_arg):
                self.analysis_output_uri = self.analysis_output_uri_path_arg
            else:
                self.analysis_output_path = Path(self.analysis_output_uri_path_arg)

        # Get analysis storage size
        if self.analysis_storage_arg is not None:
            if is_uuid_format(self.analysis_storage_arg):
                self.analysis_storage_id = self.analysis_storage_arg
            else:
                self.analysis_storage_size = self.analysis_storage_arg

        # Get activation ID
        activation_id_arg = self.args.get("--activation-id", None)

        if activation_id_arg is not None:
            self.activation_id = activation_id_arg

        # Get tags
        self.user_tags = []
        for user_tag in self.args.get("--user-tag"):
            self.user_tags.append(user_tag)
        self.technical_tags = []
        for technical_tag in self.args.get("--technical-tag"):
            self.technical_tags.append(technical_tag)
        self.reference_tags = []
        for reference_tag in self.args.get("--reference-tag"):
            self.reference_tags.append(reference_tag)

    def get_pipeline_obj(self):
        return get_project_pipeline(self.project_id, self.pipeline_id)

    def get_engine_parameters_as_commented_map(self):
        # Initialise commented map
        yaml = YAML()

        engine_parameters_map = yaml.map()

        # Mentions
        add_output_folder_path_comment = True
        add_analysis_storage_size_comment = True
        add_user_tags_comment = True
        add_technical_tags_comment = True
        add_reference_tags_comment = True

        # Add output parent folder path
        if self.output_parent_folder_path is not None:
            engine_parameters_map.update({
                "output_parent_folder_path": str(self.output_parent_folder_path) + "/"
            })
            add_output_folder_path_comment = False
        elif self.output_parent_folder_id is not None:
            engine_parameters_map.update({
                "output_parent_folder_id": self.output_parent_folder_id
            })
            add_output_folder_path_comment = False

        # Add analysis output path
        if self.analysis_output_uri is not None:
            engine_parameters_map.update({
                "analysis_output_uri": self.analysis_output_uri
            })
            add_output_folder_path_comment = False
        elif self.output_parent_folder_id is not None:
            engine_parameters_map.update({
                "analysis_output_path": str(self.analysis_output_path) + "/"
            })
            add_output_folder_path_comment = False

        # Add Analysis Storage Size to engine parameters
        if self.analysis_storage_id is not None:
            engine_parameters_map.update({
                "analysis_storage_id": self.analysis_storage_id
            })
            add_analysis_storage_size_comment = False
        elif self.analysis_storage_size is not None:
            engine_parameters_map.update({
                "analysis_storage_size": self.analysis_storage_size
            })
            add_analysis_storage_size_comment = False

        if self.user_tags is not None:
            engine_parameters_map.update({
                "user_tags": self.user_tags
            })
            add_user_tags_comment = False
        if self.technical_tags is not None:
            engine_parameters_map.update({
                "technical_tags": self.technical_tags
            })
            add_technical_tags_comment = False
        if self.reference_tags is not None:
            engine_parameters_map.update({
                "reference_tags": self.reference_tags
            })
            add_reference_tags_comment = False

        engine_parameters_map.update(
            {
                "cwltool_overrides": {}
            }
        )
        engine_parameters_map.yaml_add_eol_comment(
            key="cwltool_overrides",
            comment="Please comment out '{}' above before using, available overrides keys are: \n      # " + "\n      # ".join(
                map(
                    lambda x: f"\"{x}\":",
                    self.analysis_overrides_template
                )
            )
        )

        # Additional keys
        additional_keys = {}
        if add_analysis_storage_size_comment:
            additional_keys.update(
                {
                    "analysis_storage_size": "Small  # Size of storage, one of Small, Medium or Large or pipeline default"
                }
            )
        if add_output_folder_path_comment:
            additional_keys.update(
                {
                    "output_folder_path": "/path/to/output/dir/  # Where to place the icav2 outputs"
                }
            )
        if add_user_tags_comment:
            additional_keys.update(
                {
                    "user_tags": "[]  # User Analysis Tags"
                }
            )
        if add_technical_tags_comment:
            additional_keys.update(
                {
                    "technical_tags": "[]  # Technical Analysis Tags"
                }
            )
        if add_reference_tags_comment:
            additional_keys.update(
                {
                    "reference_tags": "[]  # Reference Analysis Tags"
                }
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
        yaml_obj = YAML()

        # Initialise map
        user_reference_map: CommentedMap = yaml_obj.map()
        user_reference_map.update({
            "user_reference": self.user_reference
        })
        user_reference_map.yaml_set_comment_before_after_key(
            before="Name of analysis",
            key="user_reference"
        )

        # Inputs
        inputs_map: CommentedMap = yaml_obj.map()
        inputs_map.update({
            "inputs": self.analysis_input_template
        })
        inputs_map.yaml_set_comment_before_after_key(
            before="Inputs JSON Body",
            key="inputs"
        )

        # Engine parameters map
        engine_parameters_map = self.get_engine_parameters_as_commented_map()
        engine_parameters_map.yaml_set_comment_before_after_key(
            before="Engine Parameters",
            key="engine_parameters"
        )

        # Write output to file path
        with open(self.output_template_yaml_path, "w") as file_h:
            with YAML(output=file_h) as yaml_h:
                yaml_h.indent = 4
                yaml_h.block_seq_indent = 2
                yaml_h.explicit_start = False
                yaml_h.dump(user_reference_map)
                yaml_h.dump(inputs_map)
                yaml_h.dump(engine_parameters_map)

        # Merge documents
        with FileInput(self.output_template_yaml_path, inplace=True) as input:
            for line in input:
                if line.rstrip() == "---":
                    pass
                else:
                    print(line.rstrip())
