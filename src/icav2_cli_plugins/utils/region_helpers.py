#!/usr/bin/env python

"""
Region helpers (for those in multiple regions)
"""

# External imports
from typing import OrderedDict, Optional, Union, Dict

# Libica imports
from libica.openapi.v2 import ApiClient, ApiException
from libica.openapi.v2.api.project_api import ProjectApi
from libica.openapi.v2.api.region_api import RegionApi
from libica.openapi.v2.model.project import Project
from libica.openapi.v2.model.region import Region
from libica.openapi.v2.model.region_list import RegionList

# Local imports
from . import is_uuid_format
from .config_helpers import get_libicav2_configuration
from .logger import get_logger

# Get logger
logger = get_logger()


def get_region_id_from_input_yaml_list(input_yaml_obj: OrderedDict) -> Optional[str]:
    if input_yaml_obj.get("region", None) is None:
        return None
    region: Optional[Union[str | Dict]] = input_yaml_obj.get("region")

    if not isinstance(region, str) and not isinstance(region, Dict):
        logger.error("Expected region attribute to be either a string or a dict")
        raise AssertionError

    if isinstance(region, str):
        if is_uuid_format(region):
            return region
        return get_region_id_from_city_name(region)
    else:
        if "region_city_name" in region.keys():
            return get_region_id_from_city_name(region.get("region_city_name"))
        else:
            return region.get("region_id")


def get_region_id_from_city_name(city_name: str) -> str:
    """
    Get region ID from the city name
    Returns:

    """
    # Enter a context with an instance of the API client
    with ApiClient(get_libicav2_configuration()) as api_client:
        # Create an instance of the API class
        api_instance = RegionApi(api_client)

    # example, this endpoint has no required or optional parameters
    try:
        # Retrieve a list of regions. Only the regions the user has access to through his/her entitlements are returned.
        api_response: RegionList = api_instance.get_regions()
    except ApiException as e:
        logger.error("Exception when calling RegionApi->get_regions: %s\n" % e)
        raise ApiException

    region_obj: Region
    for region_obj in api_response.items:
        if region_obj.city_name == city_name:
            return region_obj.id


def get_default_region_id() -> str:
    """
    Get the default region id
    Returns:
    """
    # Enter a context with an instance of the API client
    with ApiClient(get_libicav2_configuration()) as api_client:
        # Create an instance of the API class
        api_instance = RegionApi(api_client)

    # example, this endpoint has no required or optional parameters
    try:
        # Retrieve a list of regions. Only the regions the user has access to through his/her entitlements are returned.
        api_response: RegionList = api_instance.get_regions()
    except ApiException as e:
        logger.error("Exception when calling RegionApi->get_regions: %s\n" % e)
        raise ApiException

    if len(api_response.items) > 1:
        logger.warning("Multiple regions, available to user, please specify region to use in future")
        logger.warning(f"Going with the first region ({api_response.items[0].city_name})")
    return api_response.items[0].id


def get_region_id_from_bundle(bundle_id: str) -> str:
    from .bundle_helpers import get_bundle_from_id
    bundle_obj = get_bundle_from_id(bundle_id)
    return bundle_obj.region.id


def get_project_region_id_from_project_id(project_id: str) -> str:
    # Enter a context with an instance of the API client
    with ApiClient(get_libicav2_configuration()) as api_client:
        # Create an instance of the API class
        api_instance = ProjectApi(api_client)

    # example passing only required values which don't have defaults set
    try:
        # Retrieve a project.
        api_response: Project = api_instance.get_project(project_id)
    except ApiException as e:
        logger.warning("Exception when calling ProjectApi->get_project: %s\n" % e)

    return api_response.region.id
