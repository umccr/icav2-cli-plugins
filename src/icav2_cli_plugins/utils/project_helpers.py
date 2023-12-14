#!/usr/bin/env python3

"""
List projects
"""
from typing import List

from libica.openapi.v2 import ApiClient, ApiException
from libica.openapi.v2.api.project_api import ProjectApi
from libica.openapi.v2.model.project import Project

from .config_helpers import get_libicav2_configuration
from .globals import LIBICAV2_DEFAULT_PAGE_SIZE
from .logger import get_logger

logger = get_logger()


def list_projects(include_hidden_projects: bool = False) -> List[Project]:
    # Enter a context with an instance of the API client
    with ApiClient(get_libicav2_configuration()) as api_client:
        api_instance = ProjectApi(api_client)

    # Set other parameters
    page_size = LIBICAV2_DEFAULT_PAGE_SIZE
    page_offset = 0

    # Initialise project list
    project_list: List[Project] = []

    # example passing only required values which don't have defaults set
    # and optional values
    while True:
        try:
            # Retrieve a list of projects.
            api_response = api_instance.get_projects(
                include_hidden_projects=include_hidden_projects,
                page_size=str(page_size),
                page_offset=str(page_offset)
            )
        except ApiException as e:
            logger.error("Exception when calling ProjectApi->get_projects: %s\n" % e)
            raise ApiException
        project_list.extend(api_response.items)

        # Check page offset and page size against total item count
        if page_offset + page_size > api_response.total_item_count:
            break
        page_offset += page_size

    return project_list
