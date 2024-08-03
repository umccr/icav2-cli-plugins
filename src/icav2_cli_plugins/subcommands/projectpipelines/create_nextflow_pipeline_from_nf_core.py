#!/usr/bin/env python3

"""
Create nextflow pipeline from the nfcore pipeline,

This will create a pipeline from the nfcore pipeline

Step 1. Download nfcore pipeline using nf-core-cli i.e
nf-core download ampliseq --revision 2.8.0 --compress zip --outdir ampliseq

Step 2. Update the base.config file to cater for illumina pod like syntax

Step 3. Upload the pipeline to icav2 with a YYYYMMDDHHMMSS tag until we figure out what we're doing
"""

# External imports
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional

# Wrapica imports
from wrapica.project_pipelines import (
    AnalysisStorageType,
    get_analysis_storage_from_analysis_storage_size
)
from wrapica.project_pipelines import (
    ProjectPipeline,
    create_nextflow_pipeline_from_nf_core_zip
)

# Utils
from ...utils.config_helpers import get_project_id
from ...utils.logger import get_logger
from ...utils.nextflow_helpers import download_nf_core_pipeline_to_zip

# Set command
from .. import Command, DocOptArg


# Get logger
logger = get_logger()


class ProjectPipelinesCreateNextflowPipelineFromNfCore(Command):
    """Usage:
    icav2 projectpipelines create-nextflow-pipeline-from-nf-core help
    icav2 projectpipelines create-nextflow-pipeline-from-nf-core <pipeline_name>
                                                                 (--revision=<revision>)
                                                                 [--analysis-storage=<analysis_storage_id_or_size>]
                                                                 [--json]

Description:
    Deploy an nf-core workflow as an ICAv2 Pipeline.

Options:
    <pipeline_name>                                    Required, the pipeline core, use `nf-core list`
                                                       to get the list of pipelines
    --revision=<revision>                              Required, the revision of the pipeline.
    --analysis-storage=<analysis_storage_id_or_size>   Optional, analysis storage id or size [default: Small]
    --json                                             Optional, write pipeline id and code to stdout in json format


Environment variables:
    GITHUB_TOKEN             Optional, will prevent nf-core raising a warning about API throttling
                             Can be set through `export GITHUB_TOKEN="$(gh auth token)"`
    ICAV2_BASE_URL           Optional, default set as https://ica.illumina.com/ica/rest
    ICAV2_PROJECT_ID         Optional, taken from "$HOME/.icav2/.session.ica.yaml" if not set
    ICAV2_ACCESS_TOKEN       Optional, taken from "$HOME/.icav2/.session.ica.yaml" if not set

Requirements:
    Requires 'nf-core' binary to be installed, but this should be installed in the icav2 cli plugins venv

Example:
    icav2 projectpipelines create-nextflow-pipeline-from-nf-core ampliseq --revision 2.8.0 --analysis-storage-size SMALL
    """

    pipeline_name: str
    revision: str
    analysis_storage: Optional[AnalysisStorageType]
    is_output_json: Optional[bool]

    def __init__(self, command_argv):
        # CLI ARGS
        self._docopt_type_args = {
            "pipeline_name": DocOptArg(
                cli_arg_keys=["pipeline_name"],
            ),
            "revision": DocOptArg(
                cli_arg_keys=["--revision"],
            ),
            "analysis_storage": DocOptArg(
                cli_arg_keys=["--analysis-storage"],
            ),
            "is_output_json": DocOptArg(
                cli_arg_keys=["--json"]
            )
        }

        # Additional args
        # From the repo and tag name we can collect the zipped workflow obj and path
        self.zipped_workflow_tmp_dir = TemporaryDirectory()
        self.zipped_workflow_path: Optional[Path] = None

        # The project id to deploy to
        self.project_id: Optional[str] = None
        self.pipeline_obj: Optional[ProjectPipeline] = None

        # Get the input template based on the nextflow object
        self.params_xml_file: Optional[Path] = None

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
        self.pipeline_obj = create_nextflow_pipeline_from_nf_core_zip(
            project_id=self.project_id,
            pipeline_code=(
                "__".join(
                    [
                        self.zipped_workflow_path.stem.replace(".", "_"),
                        self.revision.replace(".", '_'),
                        datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
                    ]
                )
            ),
            pipeline_revision=self.revision,
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

        # Set zip path
        self.zipped_workflow_path = Path(self.zipped_workflow_tmp_dir.name) / (self.pipeline_name + ".zip")

        # Check GitHub release url is valid
        self.download_nf_core_pipeline_to_zip()

        # Get analysis storage ID or go to default
        if self.analysis_storage is None:
            self.analysis_storage = get_analysis_storage_from_analysis_storage_size(AnalysisStorageType.SMALL)

        # Set the description as the GitHub release url
        self.description = f"nf-core pipeline {self.pipeline_name} at revision {self.revision}"

        # Check is json
        self.is_output_json = self.is_output_json if self.is_output_json is not None else False

    def print_to_stdout(self):
        print(
            json.dumps(
                {
                    "pipeline_id": self.pipeline_obj.id,
                    "pipeline_code": self.pipeline_obj.code
                },
                indent=2
            )
        )

    def download_nf_core_pipeline_to_zip(self):
        download_nf_core_pipeline_to_zip(
            pipeline_name=self.pipeline_name,
            pipeline_revision=self.revision,
            output_zip_path=self.zipped_workflow_path
        )
