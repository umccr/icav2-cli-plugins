#!/usr/bin/env python3

"""
Create CWL Workflow

Given a zip file, upload a workflow to ICAV2

Create technical tags for
    inputs logic and override steps
"""
import json
import os
import shutil
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory
from typing import Optional

from utils.errors import InvalidArgumentError
from utils.config_helpers import get_project_id
from utils.cwl_helpers import ZippedCWLWorkflow
from utils.gh_helpers import download_zipped_workflow_from_github_release, get_release_repo_and_tag_from_release_url
from utils.globals import ICAV2_DEFAULT_ANALYSIS_STORAGE_SIZE, ICAv2AnalysisStorageSize
from utils.logger import get_logger
from utils.projectpipeline_helpers import \
    get_analysis_storage_id_from_analysis_storage_size, create_params_xml, \
    redirect_stdout
import requests

from urllib.parse import unquote

from subcommands import Command

logger = get_logger()


class ProjectPipelinesCreateCWLWorkflowFromGitHubRelease(Command):
    """Usage:
    icav2 projectpipelines create-cwl-workflow-from-github-release help
    icav2 projectpipelines create-cwl-workflow-from-github-release <github_release_url>
                                                                   [--analysis-storage-id=<analysis_storage_id> | --analysis-storage-size=<analysis_storage_size>]
                                                                   [--json]

Description:
    From a GitHub release, deploy a workflow to ICAv2

Options:
    <github_release_url>                               Required, path to GitHub release url
    --analysis-storage-id=<analysis_storage_id>        Optional, takes precedence over analysis-storage-size
    --analysis-storage-size=<analysis_storage_size>    Optional, default is set to Small
    --json                                             Optional, write pipeline id and code to stdout in json format

Environment variables:
    ICAV2_BASE_URL           Optional, default set as https://ica.illumina.com/ica/rest
    ICAV2_PROJECT_ID         Optional, taken from "$HOME/.icav2/.session.ica.yaml" if not set
    ICAV2_ACCESS_TOKEN       Optional, taken from "$HOME/.icav2/.session.ica.yaml" if not set

Requirements:
    Requires 'gh' binary to be installed

Example:
    icav2 projectpipelines create-cwl-workflow-from-github-release https://github.com/umccr/cwl-ica/releases/tag/dragen-pon-qc/3.9.3__221221152834 --analysis-storage-size Small
    """

    def __init__(self, command_argv):
        # The GitHub release url is the path to the url
        self.github_release_url: Optional[str] = None
        # URL split by repo and tag name
        self.github_repo: Optional[str] = None
        self.github_tag_name: Optional[str] = None
        # From the repo and tag name we can collect the zipped workflow obj and path
        self.zipped_workflow_tmp_dir = TemporaryDirectory()
        self.zipped_workflow_path: Optional[Path] = None
        self.zipped_workflow_obj: Optional[ZippedCWLWorkflow] = None

        # The project id to deploy to
        self.project_id: Optional[str] = None
        self.analysis_storage_id: Optional[str] = None

        # Get the input template based on the cwl object
        self.params_xml_file: Optional[Path] = None  #

        # Set the description as the url from the release page
        self.description: Optional[str] = None

        # For printing
        self.pipeline_id: Optional[str] = None
        self.pipeline_code: Optional[str] = None
        self.is_output_json: Optional[bool] = None

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

        # Create blank params XML
        self.create_params_xml()

        # Create output file from zipped workflow apth
        self.pipeline_id, self.pipeline_code = self.zipped_workflow_obj.create_icav2_workflow_from_zip(
            project_id=self.project_id,
            analysis_storage_id=self.analysis_storage_id,
            workflow_description=self.description,
            params_xml_file=self.params_xml_file,
            html_documentation_path=None
        )

        logger.info(f"Successfully created pipeline with pipeline id '{self.pipeline_id}' and pipeline code '{self.pipeline_code}'")

        if self.is_output_json:
            self.print_to_stdout()

    def __exit__(self):
        # Delete tmp file
        shutil.rmtree(self.zipped_workflow_tmp_dir.name)
        os.remove(self.params_xml_file)

    def print_to_stdout(self):
        print(
            json.dumps(
                {
                    "pipeline_id": self.pipeline_id,
                    "pipeline_code": self.pipeline_code
                },
                indent=2
            )
        )

    def check_args(self):
        # Check the url exists
        github_release_url_arg = unquote(self.args.get("<github_release_url>"))

        with redirect_stdout():
            url_obj = requests.get(github_release_url_arg)
        if not url_obj.status_code == 200:
            logger.error(f"Got status code {url_obj.status_code}, reason {url_obj.reason}")
            raise InvalidArgumentError

        # Set release url
        self.github_release_url = github_release_url_arg

        # Check we can get project id
        self.project_id = get_project_id()

        # Split GitHub release url into repo and tag
        self.github_repo, self.github_tag_name = get_release_repo_and_tag_from_release_url(self.github_release_url)

        # Get workflow object
        self.set_zipped_workflow_obj_from_github_release_url()
        self.set_zipped_workflow_obj()

        # Set params xml as tmp file
        self.set_params_xml_file()

        # Get analysis storage ID or go to default
        analysis_storage_id_arg = self.args.get("--analysis-storage-id", None)
        analysis_storage_size_arg = self.args.get("--analysis-storage-size", None)
        if analysis_storage_size_arg is None:
            analysis_storage_size_arg = ICAV2_DEFAULT_ANALYSIS_STORAGE_SIZE

        if analysis_storage_id_arg is not None:
            self.analysis_storage_id = analysis_storage_id_arg
        else:
            with redirect_stdout():
                self.analysis_storage_id = get_analysis_storage_id_from_analysis_storage_size(
                    ICAv2AnalysisStorageSize(analysis_storage_size_arg)
                )

        # Set the description as the GitHub release url
        self.description = f"GitHub Release URL: {self.github_release_url}"

        # Get the --json parameter
        if self.args.get("--json", False):
            self.is_output_json = True
        else:
            self.is_output_json = False

    def set_zipped_workflow_obj(self):
        self.zipped_workflow_obj: ZippedCWLWorkflow = ZippedCWLWorkflow(self.zipped_workflow_path)

    def set_params_xml_file(self):
        self.params_xml_file = Path(NamedTemporaryFile(delete=False, suffix=".xml").name)

    def set_zipped_workflow_obj_from_github_release_url(self):
        self.zipped_workflow_path = Path(self.zipped_workflow_tmp_dir.name) / (self.github_tag_name + ".zip").replace("/", "__")
        download_zipped_workflow_from_github_release(self.github_repo, self.github_tag_name, self.zipped_workflow_path)

    def create_params_xml(self):
        create_params_xml(self.zipped_workflow_obj.cwl_obj.inputs, self.params_xml_file)
