#!/usr/bin/env python3

"""
Create CWL Workflow

Given a zip file, upload a workflow to ICAV2

Create technical tags for
    inputs logic and override steps
"""

# External imports
import json
import os
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional
import requests

# Wrapica imports
from wrapica.project_pipelines import (
    AnalysisStorageType,
    create_cwl_workflow_from_zip,
    get_analysis_storage_from_analysis_storage_size
)
from wrapica.project_pipelines import ProjectPipeline

# Utils
from ...utils.errors import InvalidArgumentError
from ...utils.config_helpers import get_project_id
from ...utils.gh_helpers import (
    download_zipped_workflow_from_github_release,
    get_release_repo_and_tag_from_release_url
)
from ...utils.logger import get_logger

# Local imports
from .. import Command, DocOptArg


# Get logger
logger = get_logger()


class ProjectPipelinesCreateCWLWorkflowFromGitHubRelease(Command):
    """Usage:
    icav2 projectpipelines create-cwl-pipeline-from-github-release help
    icav2 projectpipelines create-cwl-pipeline-from-github-release <github_release_url>
                                                                   [--analysis-storage=<analysis_storage_id_or_size>]
                                                                   [--json]

Description:
    From a GitHub release, deploy a workflow to ICAv2

Options:
    <github_release_url>                               Required, path to GitHub release url
    --analysis-storage=<analysis_storage_id_or_size>   Optional, analysis storage id or size [default: Small]
    --json                                             Optional, write pipeline id and code to stdout in json format

Environment variables:
    ICAV2_BASE_URL           Optional, default set as https://ica.illumina.com/ica/rest
    ICAV2_PROJECT_ID         Optional, taken from "$HOME/.icav2/.session.ica.yaml" if not set
    ICAV2_ACCESS_TOKEN       Optional, taken from "$HOME/.icav2/.session.ica.yaml" if not set

Requirements:
    Requires 'gh' binary to be installed

Example:
    icav2 projectpipelines create-cwl-pipeline-from-github-release https://github.com/umccr/cwl-ica/releases/tag/dragen-pon-qc/3.9.3__221221152834 --analysis-storage-size Small
    """

    github_release_url: Optional[str]
    analysis_storage_obj: Optional[AnalysisStorageType]
    is_output_json: Optional[bool]

    def __init__(self, command_argv):
        # CLI ARGS
        self._docopt_type_args = {
            "github_release_url": DocOptArg(
                cli_arg_keys=["github_release_url"],
            ),
            "analysis_storage_obj": DocOptArg(
                cli_arg_keys=["--analysis-storage"],
            ),
            "is_output_json": DocOptArg(
                cli_arg_keys=["--json"]
            )
        }

        # Additional args
        # URL split by repo and tag name
        self.github_repo: Optional[str] = None
        self.github_tag_name: Optional[str] = None
        self.github_tag_name_clean: Optional[str] = None  # 'bclconvert-interop-qc%2F1.3.1--1.21__20240627011541' to 'bclconvert-interop-qc/1.3.1--1.21__20240627011541'

        # From the repo and tag name we can collect the zipped workflow obj and path
        self.zipped_workflow_tmp_dir = TemporaryDirectory()
        self.zipped_workflow_path: Optional[Path] = None

        # The project id to deploy to
        self.project_id: Optional[str] = None
        self.pipeline_obj: Optional[ProjectPipeline] = None

        # Get the input template based on the cwl object
        self.params_xml_file: Optional[Path] = None  #

        # Set the description as the url from the release page
        self.description: Optional[str] = None

        super().__init__(command_argv)

    def __call__(self):
        # Generate workflow plot
        # num_cwl_inputs = len(self.zipped_workflow_obj.cwl_obj.inputs)
        # png_plot_path = generate_plot_png(
        #     self.zipped_workflow_obj.cwl_pack,
        #     round(min(1 / math.log(num_cwl_inputs), 1.0), 3) if num_cwl_inputs > 1 else 1
        # )

        # No need to generate the markdown doc, we can't access it via the API anyway
        # Generate markdown doc
        # markdown_path = generate_markdown_doc(
        #     title=f"{self.zipped_workflow_path.stem} Pipeline",
        #     description=self.zipped_workflow_obj.cwl_obj.doc,
        #     label=self.zipped_workflow_obj.cwl_obj.label,
        #     cwl_inputs=self.zipped_workflow_obj.cwl_obj.inputs,
        #     cwl_steps=self.zipped_workflow_obj.cwl_obj.steps,
        #     cwl_outputs=self.zipped_workflow_obj.cwl_obj.outputs,
        #     workflow_image_page_path=png_plot_path,
        #     workflow_md5sum=self.zipped_workflow_obj.get_md5sum_from_packed_dict(),
        #     input_json_template=self.zipped_workflow_obj.get_cwl_inputs_template_dict(),
        #     overrides_template=self.zipped_workflow_obj.get_override_steps_dict()
        # )

        # Also don't need to generate any of the documentation
        # Generate html file through pandoc
        # html_doc = generate_standalone_html_through_pandoc(markdown_path)

        # Create output file from zipped workflow apth
        self.pipeline_obj = create_cwl_workflow_from_zip(
            project_id=self.project_id,
            pipeline_code=self.zipped_workflow_path.stem.replace(".", "_"),
            zip_path=self.zipped_workflow_path,
            workflow_description=self.description
        )
        logger.info(
            f"Successfully created pipeline with "
            f"pipeline id '{self.pipeline_obj.pipeline.id}' and "
            f"pipeline code '{self.pipeline_obj.pipeline.code}'"
        )

        if self.is_output_json:
            self.print_to_stdout()

    def __exit__(self):
        # Delete tmp file
        shutil.rmtree(self.zipped_workflow_tmp_dir.name)
        os.remove(self.params_xml_file)

    def check_args(self):
        # Check we can get project id
        self.project_id = get_project_id()

        # Check GitHub release url is valid
        url_obj = requests.get(self.github_release_url)
        if not url_obj.status_code == 200:
            logger.error(f"Got status code {url_obj.status_code}, reason {url_obj.reason}")
            raise InvalidArgumentError

        # Split GitHub release url into repo and tag
        self.github_repo, self.github_tag_name = get_release_repo_and_tag_from_release_url(self.github_release_url)
        self.github_tag_name_clean = self.github_tag_name.replace("/", "__")

        # Get workflow object
        self.set_zipped_workflow_obj_from_github_release_url()

        # Get analysis storage ID or go to default
        if self.analysis_storage_obj is None:
            self.analysis_storage_obj = get_analysis_storage_from_analysis_storage_size(AnalysisStorageType.SMALL)

        # Set the description as the GitHub release url
        self.description = f"GitHub Release URL: {self.github_release_url}"

        # Check is json
        self.is_output_json = self.is_output_json if self.is_output_json is not None else False

    def set_zipped_workflow_obj_from_github_release_url(self):
        self.zipped_workflow_path = Path(self.zipped_workflow_tmp_dir.name) / (self.github_tag_name_clean + ".zip")
        download_zipped_workflow_from_github_release(self.github_repo, self.github_tag_name, self.zipped_workflow_path)

    def print_to_stdout(self):
        print(
            json.dumps(
                {
                    "pipeline_id": self.pipeline_obj.pipeline.id,
                    "pipeline_code": self.pipeline_obj.pipeline.code
                },
                indent=2
            )
        )
