#!/usr/bin/env python3

# External imports
import json
from typing import OrderedDict, Optional, List, Dict
from pathlib import Path

from ruamel.yaml import YAML, CommentedMap, CommentedSeq

# Wrapica
from wrapica.bundle import (
    Bundle, BundleData, BundlePipeline,
    list_data_in_bundle, list_pipelines_in_bundle, filter_bundle_data_to_top_level_only
)
from wrapica.data import convert_data_obj_to_icav2_uri
from wrapica.user import get_user_obj_from_user_id

# Utils
from .logger import get_logger

# Get logger
logger = get_logger()


def read_input_yaml_file(input_yaml: Path) -> OrderedDict:
    """
    Get the contents of the session file (~/.icav2/config.ica.yaml)
    :return:
    """

    logger.debug("Reading in the config file")
    yaml = YAML()

    with open(input_yaml, "r") as file_h:
        data = yaml.load(file_h)

    return data


def print_bundles(bundles_list: List[Bundle], json_output: bool = False):
    """
    Print bundles to stdout
    With the columns:
     * id
     * name
     * creator_id
     * status
     * creation_time_stamp
     * modification_time_stamp
    Args:
        bundles_list:
        json_output:

    Returns:

    """
    # Import pandas
    # (this takes a few seconds which is why we don't do it at the top)
    import pandas as pd
    from tabulate import tabulate

    # Read in data items as a data frame
    bundle_item: Bundle
    bundle_items_df = pd.DataFrame(
        [
            {
                "id": bundle_item.id,
                "name": bundle_item.name,
                "creator_id": bundle_item.owner_id,
                "status": bundle_item.status,
                "creation_time_stamp": bundle_item.time_created,
                "modification_time_stamp": bundle_item.time_modified,
            }
            for bundle_item in bundles_list
        ]
    )

    # Get users
    creator_ids = list(bundle_items_df["creator_id"].unique())
    creator_dict = {
        None: ""
    }

    # Iterate through unique creator ids and collect names
    for creator_id in creator_ids:
        if creator_id is None:
            continue
        # Get user from user ids
        try:
            user = get_user_obj_from_user_id(creator_id)
            # Set value as firstname ' ' lastname
            creator_dict[user.id] = f"{user.firstname} {user.lastname}"
        except ValueError:
            creator_dict[creator_id] = "Unknown"

    bundle_items_df["creator_user"] = bundle_items_df["creator_id"].apply(
        lambda x: creator_dict.get(x, None)
    )

    bundle_items_df_formatted = bundle_items_df[[
        "id",
        "name",
        "status",
        "creator_id",
        "creator_user",
        "creation_time_stamp",
        "modification_time_stamp",
    ]]

    if not json_output:
        print(
            tabulate(bundle_items_df_formatted, headers=bundle_items_df_formatted.columns, showindex=False)
        )
    else:
        json.dumps(
            json.loads(bundle_items_df.to_json(orient="records")),
            indent=4
        )


def bundle_to_dict(
        bundle_obj: Bundle,
        pipeline_objs: Optional[List[BundlePipeline]] = None,
        data_objs: Optional[List[BundleData]] = None,
        include_metadata: Optional[bool] = True
) -> Dict:

    # Get pipelines and data if not provided
    if pipeline_objs is None:
        pipeline_objs = list_pipelines_in_bundle(bundle_obj.id)

    if data_objs is None:
        data_objs = filter_bundle_data_to_top_level_only(list_data_in_bundle(bundle_obj.id))

    bundle_dict = {
        "id": bundle_obj.id,
        "region": bundle_obj.region.id,
        "tenant": bundle_obj.tenant_id,
        "pipelines": sorted(map(lambda pipeline_iter: pipeline_iter.pipeline.id, pipeline_objs)),
        "data": sorted(map(lambda data_iter: data_iter.data.id, data_objs))
    }

    if include_metadata:
        bundle_dict["metadata"] = {
            "name": bundle_obj.name,
            "short_description": bundle_obj.short_description,
            "version": bundle_obj.release_version,
            "version_description": getattr(bundle_obj, "version_comment", None)
        }

    return bundle_dict


def bundle_to_yaml_obj(
        bundle_obj: Bundle,
        include_metadata: Optional[bool] = True
) -> CommentedMap:
    """
    Collect bundle as a yaml object - useful if a user wants to initialise a new bundle with a similar template
    Returns:

    """

    # Collect pipelines and data first (since we need to iterate over them for comments)
    # Get pipelines and data if not provided
    pipeline_objs = list_pipelines_in_bundle(bundle_obj.id)
    data_objs = filter_bundle_data_to_top_level_only(list_data_in_bundle(bundle_obj.id))

    logger.debug("Collecting bundle as a dictionary")
    bundle_commented_map = CommentedMap(
        bundle_to_dict(
            bundle_obj,
            pipeline_objs=pipeline_objs,
            data_objs=data_objs,
            include_metadata=include_metadata
        )
    )
    logger.debug("Finished collecting bundle as a dictionary")

    logger.debug("Converting to yaml and adding in comments")
    # Add name to the end of the id
    bundle_commented_map.yaml_add_eol_comment(
        key="id",
        comment=bundle_obj.name
    )

    # Add region city name to the end of the region id
    bundle_commented_map.yaml_add_eol_comment(
        key="region",
        comment=bundle_obj.region.city_name
    )

    # Add tenant name to the end of the tenant id
    if hasattr(bundle_obj, "tenant_name"):
        bundle_commented_map.yaml_add_eol_comment(
            key="tenant",
            comment=bundle_obj.tenant_name
        )

    # Convert pipelines and data to commented seq
    bundle_commented_map["pipelines"] = CommentedSeq(bundle_commented_map['pipelines'])
    bundle_commented_map["data"] = CommentedSeq(bundle_commented_map['data'])

    # Add pipeline names to the end of the pipeline ids
    for index, pipeline_id_iter in enumerate(bundle_commented_map["pipelines"]):
        pipeline_obj = next(filter(lambda pipeline_iter: pipeline_iter.pipeline.id == pipeline_id_iter, pipeline_objs))
        bundle_commented_map["pipelines"].yaml_add_eol_comment(
            key=index,
            comment=pipeline_obj.pipeline.code
        )

    # Add data names to the end of the data ids
    for index, data_id_iter in enumerate(bundle_commented_map["data"]):
        data_obj = next(filter(lambda data_iter: data_iter.data.id == data_id_iter, data_objs))
        bundle_commented_map["data"].yaml_add_eol_comment(
            key=index,
            comment=convert_data_obj_to_icav2_uri(data_obj.data),
        )

    return bundle_commented_map
