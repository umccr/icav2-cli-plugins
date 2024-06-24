#!/usr/bin/env python3

"""
Create CWL Workflow

Given a zip file, upload a workflow to ICAV2

Create technical tags for
    inputs logic and override steps
"""

# External data
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Wrapica imports
from wrapica.project_pipelines import (
    AnalysisStorage,
    create_cwl_workflow_from_zip
)

# Get utils
from ...utils.errors import InvalidArgumentError
from ...utils.config_helpers import get_project_id
from ...utils.cwl_helpers import (
    ZippedCWLWorkflow
)
from ...utils.logger import get_logger

# Local
from .. import Command, DocOptArg

# Get logger
logger = get_logger()


class ProjectPipelinesCreateCWLWorkflow(Command):
    """Usage:
    icav2 projectpipelines create-cwl-workflow-from-zip help
    icav2 projectpipelines create-cwl-workflow-from-zip <zipped_workflow_path>
                                                        [--analysis-storage=<analysis_storage_id_or_size>]
                                                        [--json]

Description:
    From a zip file, deploy a workflow to icav2

Options:
    <zipped_workflow_path>                             Required, path to zipped up workflow
    --analysis-storage=<analysis_storage_id_or_size>   Optional, the analysis storage id or size [default: Small]

Environment variables:
    ICAV2_BASE_URL           Optional, default set as https://ica.illumina.com/ica/rest
    ICAV2_PROJECT_ID         Optional, taken from "$HOME/.icav2/.session.ica.yaml" if not set
    ICAV2_ACCESS_TOKEN       Optional, taken from "$HOME/.icav2/.session.ica.yaml" if not set

Example:
    icav2 projectpipelines create-cwl-workflow-from-zip tabix_workflow.zip --analysis-storage-size Small
    """

    zipped_workflow_path: Path
    analysis_storage_obj: AnalysisStorage
    is_json: bool

    def __init__(self, command_argv):
        # Set args
        self._docopt_type_args = {
            "zipped_workflow_path": DocOptArg(
                cli_arg_keys=["<zipped_workflow_path>"],
            ),
            "analysis_storage_obj": DocOptArg(
                cli_arg_keys=["--analysis-storage"],
            ),
            "is_json": DocOptArg(
                cli_arg_keys=["--json"],
            )
        }

        # Set the command argv
        self.zipped_workflow_obj: Optional[ZippedCWLWorkflow] = None
        self.project_id: Optional[str] = None

        # For printing
        self.pipeline_id: Optional[str] = None
        self.pipeline_code: Optional[str] = None

        super().__init__(command_argv)

    def __call__(self):
        # Create the pipeline from zip
        self.zipped_workflow_obj = create_cwl_workflow_from_zip(
            project_id=self.project_id,
            pipeline_code=self.pipeline_code,
            zip_path=self.zipped_workflow_path,
            analysis_storage=self.analysis_storage_obj,
        )
        logger.info(
            f"Successfully created pipeline "
            f"with pipeline id {self.pipeline_id} and "
            f"pipeline code {self.pipeline_code}"
        )

        # # Generate workflow plot
        # num_cwl_inputs = len(self.zipped_workflow_obj.cwl_obj.inputs)
        # png_plot_path = generate_plot_png(
        #     self.zipped_workflow_obj.cwl_pack,
        #     round(min(1 / math.log(num_cwl_inputs), 1.0), 3) if num_cwl_inputs > 1 else 1
        # )
        #
        # # Generate markdown doc
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
        #
        # # Generate html file through pandoc
        # html_doc = generate_standalone_html_through_pandoc(markdown_path)

        if self.is_json:
            self.print_to_stdout()

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
        # Check pypandoc binary
        try:
            import pandoc
        except ImportError:
            logger.error(
                "Could not find pandoc module, "
                "please re-run the installation script with --install-pandoc parameter"
            )
            raise ImportError

        # Check zipped workflow path exists
        if not self.zipped_workflow_path.is_file():
            logger.error(f"Could not access zipped workflow path {self.zipped_workflow_path}")
            raise InvalidArgumentError
        # And that it ends in a .zip suffix
        if not self.zipped_workflow_path.name.endswith(".zip"):
            logger.error(f"zipped-workflow-path parameter {self.zipped_workflow_path} does not end with '.zip'")
            raise InvalidArgumentError

        # Check we can get project id
        self.project_id = get_project_id()

        # Set pipeline code and workflow description
        self.pipeline_code = "__".join([
            self.zipped_workflow_path.stem,
            datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        ])
