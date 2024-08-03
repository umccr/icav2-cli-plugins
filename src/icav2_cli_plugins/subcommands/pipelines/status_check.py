#!/usr/bin/env python3

"""
Check ownership of a pipeline / tenant and user
"""

# Standard imports
from typing import Optional
import sys

# Wrapica imports
from wrapica.enums import PipelineStatus
from wrapica.user import (
    get_user_id_from_configuration, get_tenant_id_for_user
)
from wrapica.pipelines import PipelineType

# Utils
from ...utils.logger import get_logger

# Locals
from .. import Command, DocOptArg

# Get logger
logger = get_logger()


class StatusCheck(Command):
    """Usage:
    icav2 pipelines status-check help
    icav2 pipelines status-check <pipeline_id_or_code>
                                 (--is-editable | --is-linkable)

Description:
    Check the abilities owner of a pipeline.
    Fail with non-zero exit code if --is-editable or --is-linkable
    are set and the pipeline is not editable, or linkable to a bundle by the user respectively

    Use case 1: --is-editable
    For editing/updating a pipeline, a pipeline must be owned by the user in the same tenant context
    The pipeline must also be in draft mode

    Use case 2: --is-linkable
    Linking a pipeline to a bundle, first need to ensure the pipeline is owned by this tenant.
    The pipeline must also be in released mode.

    A pipeline cannot be both editable AND linkable, hence --is-editable and --is-linkable are mutually exclusive arguments.

Options:
    <pipeline_id_or_code>          Required, the id (or code) of the pipeline to update
    --is-editable                  Optional,
                                   Return a non-zero exit-code if not owned by user OR not in DRAFT status
    --is-linkable                  Optional, return a non-zero exit-code if not owned by tenant OR not in RELEASED status

Environment:
    ICAV2_BASE_URL (optional, defaults to ica.illumina.com)
    ICAV2_PROJECT_ID (optional, taken from ~/.session.ica.yaml otherwise)

Example:
    icav2 pipelines status-check 12345678-1234-1234-1234-123456789012 --is-editable
    """

    pipeline_obj: PipelineType
    is_editable: Optional[bool]
    is_linkable: Optional[bool]

    def __init__(self, command_argv):
        # CLI ARGS
        self._docopt_type_args = {
            "pipeline_obj": DocOptArg(
                cli_arg_keys=["<pipeline_id_or_code>"]
            ),
            "is_editable": DocOptArg(
                cli_arg_keys=["--is-editable"],
            ),
            "is_linkable": DocOptArg(
                cli_arg_keys=["--is-linkable"],
            )
        }

        # Initialise parameters
        self.pipeline_status: Optional[PipelineStatus] = None
        self.user_id: Optional[str] = None
        self.tenant_id: Optional[str] = None

        super().__init__(command_argv)

    def __call__(self):
        # Update pipeline
        self.check_pipeline_obj()

    def check_args(self):
        # Get the pipeline as an object
        self.pipeline_status = PipelineStatus(self.pipeline_obj.status)

        # Get the current user and tenant
        self.user_id = get_user_id_from_configuration()
        self.tenant_id = get_tenant_id_for_user()

        # Check tenant
        if not self.pipeline_obj.tenant_id == self.tenant_id:
            logger.error(f"Pipeline '{self.pipeline_obj.id}' is not owned by tenant '{self.tenant_id}'")
            logger.error(f"Pipeline is neither editable nor linkable")
            sys.exit(1)

    def check_pipeline_obj(self):
        if self.is_editable:
            self.check_is_editable()
        elif self.is_linkable:
            self.check_is_linkable()

    def check_is_editable(self):
        # Check pipeline status
        if not self.pipeline_status == PipelineStatus.DRAFT:
            logger.error(f"Pipeline '{self.pipeline_obj.id}' is not in DRAFT status")
            logger.error(f"Cannot edit pipeline in '{self.pipeline_status.value}' status")
            sys.exit(1)

        # Check user
        if not self.pipeline_obj.owner_id == self.user_id:
            logger.error(f"Pipeline '{self.pipeline_obj.id}' is not owned by user '{self.user_id}'")
            sys.exit(1)

        logger.info(f"Pipeline '{self.pipeline_obj.id}' is editable")

    def check_is_linkable(self):
        # Check pipeline status
        if not self.pipeline_status == PipelineStatus.RELEASED:
            logger.error(f"Pipeline '{self.pipeline_obj.id}' is not in RELEASED status")
            logger.error(f"Cannot link pipeline '{self.pipeline_obj.id}' in {self.pipeline_status.value} status")
            sys.exit(1)

        logger.info(f"Pipeline '{self.pipeline_obj.id}' is linkable")
