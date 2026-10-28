#!/usr/bin/env python3

"""
Get the details of a job (such as a data copy / transfer job)
"""

# External imports
import json
import sys
from typing import Optional

# Utils
from ...utils import to_jsonable_dict
from ...utils.logger import get_logger

# locals
from .. import Command, DocOptArg

# Get logger
logger = get_logger()


class JobsGet(Command):
    """Usage:
    icav2 jobs get help
    icav2 jobs get <job_id>
                   [--yaml]

Description:
    Get the details of a job.

    Jobs are background tasks such as data copy or data transfer operations.
    The job id is returned by commands such as 'icav2 projectdata cp' or 'icav2 projectdata mv'.

Options:
    <job_id>                Required, the id of the job
    --yaml                  Optional, print the output in yaml format (default is json)

Environment:
    ICAV2_ACCESS_TOKEN (optional, set as ~/.icav2/.session.ica.yaml if not set)
    ICAV2_BASE_URL (optional, defaults to https://ica.illumina.com/ica/rest)

Example:
    icav2 jobs get abcd1234-5678-90ab-cdef-1234567890ab
    """

    job_id: str
    is_yaml: Optional[bool]

    def __init__(self, command_argv):
        # CLI ARGS
        self._docopt_type_args = {
            "job_id": DocOptArg(
                cli_arg_keys=["job_id"],
            ),
            "is_yaml": DocOptArg(
                cli_arg_keys=["--yaml"],
            ),
        }

        # Collect args from doc strings
        super().__init__(command_argv)

    def check_args(self):
        # Nothing to validate beyond the required job id (handled by docopt)
        pass

    def __call__(self):
        # Lazy import of wrapica
        from wrapica.job import get_job

        job_obj = get_job(self.job_id)

        # Convert the pydantic model to a serialisable dict
        job_dict = to_jsonable_dict(job_obj)

        if self.is_yaml:
            from ruamel.yaml import YAML
            yaml = YAML()
            yaml.default_flow_style = False
            yaml.dump(job_dict, sys.stdout)
        else:
            print(json.dumps(job_dict, indent=4))
