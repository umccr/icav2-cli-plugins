#!/usr/bin/env python3

"""
Check ownership of a pipeline / tenant and user
"""

# External imports
from typing import Optional
import sys

# Utils
from ...utils import is_uuid_format
from ...utils.errors import InvalidArgumentError
from ...utils.logger import get_logger
from ...utils.pipeline_helpers import get_pipeline_id_from_pipeline_code, get_pipeline_from_pipeline_id
from ...utils.user_helpers import get_user_id_from_configuration, get_tenant_id_for_user, get_user_from_user_id

# Locals
from .. import Command

# Get logger
logger = get_logger()


class CheckOwnership(Command):
    """Usage:
    icav2 pipelines check-ownership help
    icav2 pipelines check-ownership <pipeline_id>
                                    [--confirm-user-ownership]
                                    [--confirm-tenant-ownership]

Description:
    Check the owner of a pipeline. Fail with non-zero exit code if --confirm-user-ownership or --confirm-tenant-ownership
    are set and the pipeline is not owned by the user or tenant respectively.

    Use case 1:
    For updating a pipeline, a pipeline must be owned by the user in the same tenant context
    (and a draft but we currently don't have any way to check that).

    Use case 2:
    Linking a pipeline to a bundle, first need to ensure the pipeline is owned by this tenant.

Options:
    <pipeline_id>                  Required, the id (or code) of the pipeline to update
    --confirm-user-ownership       Optional, return a non-zero exit-code if not owned by user (implies --confirm-tenant-ownership)
    --confirm-tenant-ownership     Optional, return a non-zero exit-code if not owned by tenant (tenant ownership required to link a pipeline to a bundle)

Environment:
    ICAV2_BASE_URL (optional, defaults to ica.illumina.com)
    ICAV2_PROJECT_ID (optional, taken from ~/.session.ica.yaml otherwise)

Example:
    icav2 pipelines check-ownership 12345678-1234-1234-1234-123456789012 --confirm-user-ownership
    """

    def __init__(self, command_argv):
        # Initialise parameters
        self.user_id: Optional[str] = None
        self.user_name: Optional[str] = None
        self.tenant_id: Optional[str] = None
        self.pipeline_id: Optional[str] = None
        self.confirm_user_ownership: Optional[bool] = None
        self.confirm_tenant_ownership: Optional[bool] = None

        super().__init__(command_argv)

    def __call__(self):
        # Update pipeline
        self.check_pipeline_obj()

    def get_pipeline_id(self):
        pipeline_id_arg = self.args.get("<pipeline_id>", None)
        if pipeline_id_arg is None:
            logger.error("Please specify a pipeline id or code")
            raise InvalidArgumentError

        # Get pipeline id (if in code format)
        if is_uuid_format(pipeline_id_arg):
            pipeline_id = pipeline_id_arg
        else:
            pipeline_id = get_pipeline_id_from_pipeline_code(pipeline_id_arg)

        return pipeline_id

    def check_args(self):
        # Get the pipeline id
        self.pipeline_id = self.get_pipeline_id()

        # Check parameters
        self.confirm_user_ownership = self.args.get("--confirm-user-ownership", False)
        self.confirm_tenant_ownership = self.args.get("--confirm-tenant-ownership", False)
        if self.confirm_user_ownership:
            self.confirm_tenant_ownership = True

        # Get user / tenant ids
        self.user_id = get_user_id_from_configuration()
        self.user_name = get_user_from_user_id(self.user_id).username
        self.tenant_id = get_tenant_id_for_user()

    def check_pipeline_obj(self):
        pipeline_obj = get_pipeline_from_pipeline_id(self.pipeline_id)

        # Check tenant
        if not pipeline_obj.tenant_id == self.tenant_id and self.confirm_tenant_ownership:
            logger.error(f"Pipeline '{self.pipeline_id}' is not owned by tenant '{self.tenant_id}'")
            sys.exit(1)

        try:
            user_obj = get_user_from_user_id(pipeline_obj.owner_id)
            pipeline_owner_name = user_obj.firstname + " " + user_obj.lastname
        except Exception as e:
            logger.warning(f"Could not get user for owner id {pipeline_obj.owner_id}")
            pipeline_owner_name = "unknown"

        # Check user
        if not pipeline_obj.owner_id == self.user_id and self.confirm_user_ownership:
            logger.error(f"Pipeline '{self.pipeline_id}' is not owned by user '{self.user_name}'")
            logger.error(f"Instead got owner id '{pipeline_obj.owner_id}' / name '{pipeline_owner_name}'")
            sys.exit(1)

        logger.info(f"Pipeline is owned by '{pipeline_obj.owner_id}' / '{pipeline_owner_name}'")
