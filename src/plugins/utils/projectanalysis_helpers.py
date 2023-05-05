#!/usr/bin/env python

"""
Helpers for the projectanalysis workflow steps
"""
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import List, Dict

import requests
from libica.openapi.v2.model.analysis import Analysis
from libica.openapi.v2.model.analysis_step_logs import AnalysisStepLogs

from libica.openapi.v2.model.analysis_step_list import AnalysisStepList

from libica.openapi.v2.api.project_analysis_api import ProjectAnalysisApi

from libica.openapi.v2 import ApiClient, ApiException
from libica.openapi.v2.model.analysis_step import AnalysisStep
from utils.config_helpers import get_libicav2_configuration
from utils.logger import get_logger
from utils.projectpipeline_helpers import create_download_url

logger = get_logger()


def get_analysis(project_id: str, analysis_id: str) -> Analysis:
    """
    Get analaysis object
    Args:
        project_id:
        analysis_id:

    Returns:

    """
    with ApiClient(get_libicav2_configuration()) as api_client:
        # Create an instance of the API class
        api_instance = ProjectAnalysisApi(api_client)

        # example passing only required values which don't have defaults set
        try:
            # Retrieve the individual steps of an analysis.
            api_response: Analysis = api_instance.get_analysis(
                project_id,
                analysis_id
            )
        except ApiException as e:
            raise ValueError("Exception when calling ProjectAnalysisApi->get_analysis: %s\n" % e)

    return api_response


def get_workflow_steps(project_id: str, analysis_id: str) -> List[AnalysisStep]:
    # Enter a context with an instance of the API client
    with ApiClient(get_libicav2_configuration()) as api_client:
        # Create an instance of the API class
        api_instance = ProjectAnalysisApi(api_client)

        # example passing only required values which don't have defaults set
        try:
            # Retrieve the individual steps of an analysis.
            api_response: AnalysisStepList = api_instance.get_analysis_steps(
                project_id,
                analysis_id
            )
        except ApiException as e:
            raise ValueError("Exception when calling ProjectAnalysisApi->get_analysis_steps: %s\n" % e)

    return api_response.items


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


def write_analysis_step_logs(step_logs: AnalysisStepLogs, project_id: str, log_name: str, output_path: Path, is_cwltool_log=False):
    # Check if we're getting our log from a stream
    is_stream = False
    log_stream = None
    log_data_id = ""

    non_empty_log_attrs = []
    # Check attributes of log obj
    for attr in dir(step_logs):
        if attr.startswith('_'):
            continue
        if getattr(step_logs, attr) is None:
            continue
        non_empty_log_attrs.append(attr)

    if log_name == "stdout":
        if hasattr(step_logs, "std_out_stream") and step_logs.std_out_stream is not None:
            is_stream = True
            log_stream = step_logs.std_out_stream
        elif hasattr(step_logs, "std_out_data") and step_logs.std_out_data is not None:
            log_data_id: str = step_logs.std_out_data.id
        else:
            logger.error("Could not get either file output or stream of logs")
            logger.error(f"The available attributes were {', '.join(non_empty_log_attrs)}")
            raise AttributeError
    else:
        if hasattr(step_logs, "std_err_stream") and step_logs.std_err_stream is not None:
            is_stream = True
            log_stream = step_logs.std_err_stream
        elif hasattr(step_logs, "std_err_data") and step_logs.std_err_data is not None:
            log_data_id: str = step_logs.std_err_data.id
        else:
            logger.error("Could not get either file output or stream of logs")
            logger.error(f"The available attributes were {', '.join(non_empty_log_attrs)}")
            raise AttributeError
    if is_stream:
        from utils.websocket_helpers import write_websocket_to_file, convert_html_to_text
        if is_cwltool_log:
            temp_html_obj = NamedTemporaryFile()
            write_websocket_to_file(log_stream,
                                    output_file=Path(temp_html_obj.name))
            convert_html_to_text(Path(temp_html_obj.name), output_path)
        else:
            write_websocket_to_file(log_stream,
                                    output_file=output_path)
    else:
        write_icav2_file_contents(project_id, log_data_id, output_path)


def write_icav2_file_contents(project_id: str, data_id, output_path: Path):
    download_url = create_download_url(project_id, data_id)
    r = requests.get(download_url)
    with open(output_path, "wb") as f_h:
        f_h.write(r.content)
