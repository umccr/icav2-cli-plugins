#!/usr/bin/env python

"""
Region helpers (for those in multiple regions)
"""

# External imports
from typing import OrderedDict, Optional, Union, Dict

# Wrapica imports
from wrapica.region import (
    get_region_obj_from_city_name
)

# Local imports
from . import is_uuid_format
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
        return get_region_obj_from_city_name(region).id
    else:
        if "region_city_name" in region.keys():
            return get_region_obj_from_city_name(region.get("region_city_name")).id
        else:
            return region.get("region_id")

