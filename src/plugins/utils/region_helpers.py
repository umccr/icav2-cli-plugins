#!/usr/bin/env python

"""
Region helpers (for those in multiple regions)
"""
from typing import OrderedDict, Optional, Union, Dict

from libica.openapi.v2 import ApiClient, ApiException
from libica.openapi.v2.api.region_api import RegionApi
from libica.openapi.v2.model.region import Region
from libica.openapi.v2.model.region_list import RegionList

from utils import is_uuid_format
from utils.config_helpers import get_libicav2_configuration
from utils.logger import get_logger

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
    from utils.bundle_helpers import get_bundle_from_id
    bundle_obj = get_bundle_from_id(bundle_id)
    return bundle_obj.region.id
