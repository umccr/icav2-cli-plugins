#!/usr/bin/env python3

"""
Given a zip file containing a Nextflow pipeline,
upload onto the ICAv2 platform
"""

# External imports
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Wrapica imports
from wrapica.project_pipelines import (
    AnalysisStorage,
)
from wrapica.project_pipelines import (
    ProjectPipeline,
    create_nextflow_pipeline_from_zip
)

# Utils
from ...utils.config_helpers import get_project_id
from ...utils.logger import get_logger

# Local imports
from .. import Command, DocOptArg

# Get logger
logger = get_logger()


class ProjectPipelinesCreateNextflowPipelineFromZip(Command):
    """Usage:
    icav2 projectpipelines create-nextflow-pipeline-from-zip help
    icav2 projectpipelines create-nextflow-pipeline-from-zip <zipped_workflow_path>
                                                             [--workflow-description=<workflow_description>]
                                                             [--analysis-storage=<analysis_storage_id_or_size>]
                                                             [--json]

Description:
    Deploy a zipped nextflow workflow as an ICAv2 pipeline.

Options:
    <zipped_workflow_path>                             Path to the zipped nextflow pipeline
    --workflow-description=<workflow_description>      Optional, description of the workflow
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

    zipped_workflow_path: Path
    workflow_description: Optional[str]
    analysis_storage: Optional[AnalysisStorage]
    is_output_json: Optional[bool]

    def __init__(self, command_argv):
        # CLI ARGS
        self._docopt_type_args = {
            "zipped_workflow_path": DocOptArg(
                cli_arg_keys=["zipped_workflow_path"],
            ),
            "analysis_storage": DocOptArg(
                cli_arg_keys=["--analysis-storage"],
            ),
            "is_output_json": DocOptArg(
                cli_arg_keys=["--json"]
            )
        }

        # The project id to deploy to
        self.project_id: Optional[str] = None
        self.pipeline_obj: Optional[ProjectPipeline] = None

        # Set the description as the url from the release page
        self.workflow_description: Optional[str] = None

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
        self.pipeline_obj = create_nextflow_pipeline_from_zip(
            project_id=self.project_id,
            pipeline_code=(
                "__".join(
                    [
                        self.zipped_workflow_path.stem.replace(".", "_"),
                        datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
                    ]
                )
            ),
            zip_path=self.zipped_workflow_path,
            workflow_description=self.workflow_description
        )
        logger.info(
            f"Successfully created pipeline with "
            f"pipeline id '{self.pipeline_obj.pipeline.id}' and "
            f"pipeline code '{self.pipeline_obj.pipeline.code}'"
        )

        if self.is_output_json:
            self.print_to_stdout()

    def check_args(self):
        # Check we can get project id
        self.project_id = get_project_id()

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
