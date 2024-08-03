#!/usr/bin/env python

"""
Helpers for the projectanalysis workflow steps
"""

# External imports
from datetime import datetime, timezone
from typing import List, Dict

# Wrapica imports
from wrapica.project_analysis import AnalysisStep

# Local imports
from .logger import get_logger

# Get logger
logger = get_logger()


def filter_analysis_steps(workflow_steps: List[AnalysisStep], show_technical_steps=False) -> List[Dict]:
    # Filter steps
    workflow_steps_filtered: List[Dict] = []
    for workflow_step in workflow_steps:
        # Skip technical steps if required
        if workflow_step.technical and not show_technical_steps:
            continue

        workflow_step_dict = {
            "name": workflow_step.name.split("#", 1)[-1],
            "status": workflow_step.status
        }

        for date_item in ["queue_date", "start_date", "end_date"]:
            if hasattr(workflow_step, date_item) and getattr(workflow_step, date_item) is not None:
                date_obj: datetime = getattr(workflow_step, date_item)
                workflow_step_dict[date_item] = date_obj.strftime("%Y-%m-%dT%H:%M:%SZ")

        workflow_steps_filtered.append(
            workflow_step_dict
        )

    return workflow_steps_filtered


def sort_analysis_steps(workflow_steps):
    """
    Sort analysis steps by queue date
    :param workflow_steps:
    :return:
    """

    return sorted(
        workflow_steps,
        key=lambda workflow_step_iter: (
            workflow_step_iter.queue_date
            if (
                    hasattr(workflow_step_iter, 'queue_date') and
                    workflow_step_iter.queue_date is not None
            )
            else datetime.now(timezone.utc)
        )
    )
