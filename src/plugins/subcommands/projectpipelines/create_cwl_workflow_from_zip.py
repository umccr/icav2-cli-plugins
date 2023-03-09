#!/usr/bin/env python3

"""
Create CWL Workflow

Given a zip file, upload a workflow to ICAV2

Create technical tags for
    inputs logic and override steps
"""
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Optional, Dict
import math

from utils.errors import InvalidArgumentError
from utils.config_helpers import get_project_id
from utils.cwl_helpers import ZippedCWLWorkflow, generate_plot_png, generate_markdown_doc, \
    generate_standalone_html_through_pandoc
from utils.globals import ICAV2_DEFAULT_ANALYSIS_STORAGE_SIZE, ICAv2AnalysisStorageSize
from utils.logger import get_logger
from utils.projectpipeline_helpers import get_analysis_storage_id_from_analysis_storage_size, create_params_xml

from subcommands import Command

logger = get_logger()


class ProjectDataCreateCWLWorkflow(Command):
    """Usage:
    icav2 projectpipelines create-cwl-workflow-from-zip help
    icav2 projectpipelines create-cwl-workflow-from-zip <zipped_workflow_path>
                                                        [--analysis-storage-id=<analysis_storage_id> | --analysis-storage-size=<analysis_storage_size>]


Description:
    From a zip file, deploy a workflow to icav2

Options:
    <zipped_workflow_path>                             Required, path to zipped up workflow
    --analysis-storage-id=<analysis_storage_id>        Optional, takes precedence over analysis-storage-size
    --analysis-storage-size=<analysis_storage_size>    Optional, default is set to Small

Environment variables:
    ICAV2_BASE_URL           Optional, default set as https://ica.illumina.com/ica/rest
    ICAV2_PROJECT_ID         Optional, taken from "$HOME/.icav2/.session.ica.yaml" if not set
    ICAV2_ACCESS_TOKEN       Optional, taken from "$HOME/.icav2/.session.ica.yaml" if not set

Example:
    icav2 projectpipelines create-cwl-workflow-from-zip tabix_workflow.zip --analysis-storage-size Small
    """

    def __init__(self, command_argv):
        self.zipped_workflow_path: Optional[Path] = None
        self.zipped_workflow_obj: Optional[ZippedCWLWorkflow] = None
        self.project_id: Optional[str] = None
        self.analysis_storage_id: Optional[str] = None

        # For printing
        self.pipeline_id: Optional[str] = None
        self.pipeline_code: Optional[str] = None
        self.is_output_json: Optional[bool] = None

        super().__init__(command_argv)

        # Pack and then get the cwl object
        self.zipped_workflow_obj = self.get_zipped_workflow_obj()

        # Get the input template based on the cwl object
        self.input_template = self.get_input_template_from_cwl_obj()

        # Get the override steps based on the cwl object
        self.override_steps = self.get_override_steps_from_cwl_obj()

        # Set the params xml file
        self.params_xml = Path(NamedTemporaryFile(delete=False, suffix=".xml").name)
        create_params_xml(self.zipped_workflow_obj.cwl_obj.inputs, self.params_xml)

    def __call__(self):
        # Generate workflow plot
        num_cwl_inputs = len(self.zipped_workflow_obj.cwl_obj.inputs)
        png_plot_path = generate_plot_png(
            self.zipped_workflow_obj.cwl_pack,
            round(min(1 / math.log(num_cwl_inputs), 1.0), 3) if num_cwl_inputs > 1 else 1
        )

        # Generate markdown doc
        markdown_path = generate_markdown_doc(
            title=f"{self.zipped_workflow_path.stem} Pipeline",
            description=self.zipped_workflow_obj.cwl_obj.doc,
            label=self.zipped_workflow_obj.cwl_obj.label,
            cwl_inputs=self.zipped_workflow_obj.cwl_obj.inputs,
            cwl_steps=self.zipped_workflow_obj.cwl_obj.steps,
            cwl_outputs=self.zipped_workflow_obj.cwl_obj.outputs,
            workflow_image_page_path=png_plot_path,
            workflow_md5sum=self.zipped_workflow_obj.get_md5sum_from_packed_dict(),
            input_json_template=self.zipped_workflow_obj.get_cwl_inputs_template_dict(),
            overrides_template=self.zipped_workflow_obj.get_override_steps_dict()
        )

        # Generate html file through pandoc
        html_doc = generate_standalone_html_through_pandoc(markdown_path)

        # Create output file from zipped workflow apth
        pipeline_id, pipeline_code = self.zipped_workflow_obj.create_icav2_workflow_from_zip(
            project_id=self.project_id,
            analysis_storage_id=self.analysis_storage_id,
            workflow_description=self.zipped_workflow_obj.cwl_obj.doc,
            params_xml_file=self.params_xml,
            html_documentation_path=html_doc
        )

        logger.info(f"Successfully created pipeline with pipeline id {self.pipeline_id} and pipeline code {self.pipeline_code}")

        if self.is_output_json:
            self.print_to_stdout()

    def __exit__(self):
        os.remove(self.params_xml)

    def print_to_stdout(self):
        print(
            json.dumps({
                "pipeline_id": self.pipeline_id,
                "pipeline_code": self.pipeline_code
            })
        )

    def check_args(self):
        # Check zipped workflow path exists
        self.zipped_workflow_path = Path(self.args.get("<zipped_workflow_path>"))
        if not self.zipped_workflow_path.is_file():
            logger.error(f"Could not access zipped workflow path {self.zipped_workflow_path}")
            raise InvalidArgumentError
        if not self.zipped_workflow_path.name.endswith(".zip"):
            logger.error(f"zipped-workflow-path parameter {self.zipped_workflow_path} does not end with '.zip'")
            raise InvalidArgumentError

        # Check we can get project id
        self.project_id = get_project_id()

        # Get analysis storage ID or go to default
        analysis_storage_id_arg = self.args.get("--analysis-storage-id", None)
        analysis_storage_size_arg = self.args.get("--analysis-storage-size", None)
        if analysis_storage_size_arg is None:
            analysis_storage_size_arg = ICAV2_DEFAULT_ANALYSIS_STORAGE_SIZE

        if analysis_storage_id_arg is not None:
            self.analysis_storage_id = analysis_storage_id_arg
        else:
            self.analysis_storage_id = get_analysis_storage_id_from_analysis_storage_size(
                ICAv2AnalysisStorageSize(analysis_storage_size_arg)
            )

        # Get the --json parameter
        if self.args.get("--json", False):
            self.is_output_json = True
        else:
            self.is_output_json = False

    def get_zipped_workflow_obj(self) -> ZippedCWLWorkflow:
        return ZippedCWLWorkflow(self.zipped_workflow_path)

    def get_input_template_from_cwl_obj(self) -> Dict:
        return self.zipped_workflow_obj.get_cwl_inputs_template_dict()

    def get_override_steps_from_cwl_obj(self):
        return self.zipped_workflow_obj.get_override_steps_dict()

