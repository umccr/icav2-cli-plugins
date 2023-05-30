#!/usr/bin/env python3
import json
from io import StringIO, BytesIO
from typing import OrderedDict, Optional, List, Dict, Union, TextIO
from pathlib import Path

from libica.openapi.v2 import ApiClient, ApiException
from libica.openapi.v2.api.bundle_api import BundleApi
from libica.openapi.v2.api.bundle_pipeline_api import BundlePipelineApi
from libica.openapi.v2.api.data_api import DataApi
from libica.openapi.v2.api.pipeline_api import PipelineApi
from libica.openapi.v2.model.bundle_paged_list import BundlePagedList
from libica.openapi.v2.model.data import Data
from libica.openapi.v2.model.pipeline import Pipeline
from libica.openapi.v2.model.pipeline_list import PipelineList
from libica.openapi.v2.api import bundle_api
from libica.openapi.v2.model.create_bundle import CreateBundle
from libica.openapi.v2.model.bundle import Bundle

from ruamel.yaml import YAML


from utils.config_helpers import get_libicav2_configuration
from utils.logger import get_logger
from utils.projectdata_helpers import convert_icav2_uri_to_data_obj
from utils.region_helpers import get_region_id_from_bundle
from utils.subprocess_handler import run_subprocess_proc
from utils.user_helpers import get_user_from_user_id

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


def get_pipelines_from_input_yaml_list(input_yaml_obj: OrderedDict) -> Optional[List[Pipeline]]:
    """
    Get the pipeline objects from the input yaml list
    Args:
        input_yaml_obj:

    Returns:

    """
    if input_yaml_obj.get("pipelines", None) is None:
        return None
    elif not isinstance(input_yaml_obj.get("pipelines"), List):
        logger.error(f"Expected pipelines key in input yaml to be a list")
        raise TypeError

    pipeline_objs: List[Pipeline] = []

    # Get the pipeline
    for index, pipeline in enumerate(input_yaml_obj.get("pipelines")):
        if pipeline.get("pipeline_id") is not None:
            pipeline_objs.append(get_pipeline_obj_from_pipeline_id(pipeline.get("pipeline_id")))
        elif pipeline.get("pipeline_code") is not None:
            pipeline_objs.append(get_pipeline_obj_from_pipeline_code(pipeline.get("pipeline_code")))
        else:
            logger.error(f"Could not pipeline id or pipeline code for pipeline item number {index}")
            raise ValueError

    return pipeline_objs


def get_pipeline_obj_from_pipeline_id(pipeline_id: str) -> Pipeline:
    """
    Get the pipeline object from the pipeline id
    Args:
        pipeline_id:

    Returns:

    """
    with ApiClient(get_libicav2_configuration()) as api_client:
        # Create an instance of the API class
        api_instance = PipelineApi(api_client)

    # example, this endpoint has no required or optional parameters
    try:
        # Retrieve a list of pipelines.
        api_response: PipelineList = api_instance.get_pipelines()
    except ApiException as e:
        logger.error("Exception when calling PipelineApi->get_pipelines: %s\n" % e)
        raise ApiException

    pipeline_item: Pipeline
    for pipeline_item in api_response.items:
        if pipeline_item.id == pipeline_id:
            return pipeline_item


def get_pipeline_obj_from_pipeline_code(pipeline_code: str) -> Pipeline:
    """
    Get the pipeline object from the pipeline code
    Args:
        pipeline_code:

    Returns:

    """
    with ApiClient(get_libicav2_configuration()) as api_client:
        # Create an instance of the API class
        api_instance = PipelineApi(api_client)

    # example, this endpoint has no required or optional parameters
    try:
        # Retrieve a list of pipelines.
        api_response: PipelineList = api_instance.get_pipelines()
    except ApiException as e:
        logger.error("Exception when calling PipelineApi->get_pipelines: %s\n" % e)
        raise ApiException

    pipeline_item: Pipeline
    for pipeline_item in api_response.items:
        if pipeline_item.code == pipeline_code:
            return pipeline_item


def get_data_objs_from_input_yaml_list(input_yaml_obj: OrderedDict, region_id: str) -> Optional[List[Data]]:
    """
    Get the data objects from the input yaml list
    Args:
        region_id:
        input_yaml_obj:

    Returns:

    """
    if input_yaml_obj.get("data", None) is None:
        return None
    elif not isinstance(input_yaml_obj.get("data"), List):
        logger.error(f"Expected data key in input yaml to be a list")
        raise TypeError

    data_objs: List[Data] = []

    # Get the pipeline
    for index, data in enumerate(input_yaml_obj.get("data")):
        if data.get("data_id") is not None:
            data_objs.append(get_data_obj_from_data_id(data.get("data_id"), region_id))
        elif data.get("data_uri") is not None:
            data_objs.append(get_data_obj_from_data_uri(data.get("data_uri"), region_id))
        else:
            logger.error(f"Could not pipeline id or pipeline code for pipeline item number {index}")
            raise ValueError

    return data_objs


def get_data_obj_from_data_id(data_id: str, region_id: str) -> Data:
    """
    Get data object from data id from the pipelines API
    Data MUST be in the same region as the to-be-created bundle
    Args:
        data_id:
        region_id:

    Returns:

    """
    with ApiClient(get_libicav2_configuration()) as api_client:
        # Create an instance of the API class
        api_instance = DataApi(api_client)

    # Get the data urn
    data_urn = f"urn:ilmn:ica:region:{region_id}:data:{data_id}"

    # example passing only required values which don't have defaults set
    try:
        # Retrieve a data.
        api_response: Data = api_instance.get_data(data_urn)
    except ApiException as e:
        logger.error("Exception when calling DataApi->get_data: %s\n" % e)
        raise ApiException

    return api_response


def get_data_obj_from_data_uri(data_uri: str, region_id) -> Data:
    """
    Get data object from data uri
    Args:
        data_uri:
        region_id:

    Returns:
    """
    data_obj: Data = convert_icav2_uri_to_data_obj(data_uri).data

    if not data_obj.details.region.id == region_id:
        logger.error(f"Cannot add data uri {data_uri} to bundle, it is not in the same region")
        raise ValueError

    return data_obj


def create_bundle(bundle_name, bundle_description, region_id, bundle_release_version) -> Bundle:
    """
    Create a bundle object from a list of data objects, pipeline objects

    Args:
        bundle_name:
        bundle_description:
        region_id:
        bundle_release_version:

    Returns:

    """
    with ApiClient(get_libicav2_configuration()) as api_client:
        # Create an instance of the API class
        api_instance = BundleApi(api_client)

    try:
        # Create a new bundle
        api_response: Bundle = api_instance.create_bundle(
            create_bundle=CreateBundle(
                name=bundle_name,
                short_description=bundle_description,
                bundle_release_version=bundle_release_version,
                region_id=region_id,
                bundle_status="DRAFT",
                categories=[]  # FIXME - will soon allow categories
            )
        )
    except ApiException as e:
        logger.error("Exception when calling BundleApi->create_bundle: %s\n" % e)
        raise ApiException

    return api_response


def add_pipeline_to_bundle(bundle_id: str, pipeline_id: str) -> Optional[bool]:
    """

    Args:
        bundle_id:
        pipeline_id:

    Returns:

    """
    with ApiClient(get_libicav2_configuration()) as api_client:
        # Create an instance of the API class
        api_instance = BundlePipelineApi(api_client)

    # example passing only required values which don't have defaults set
    # Getting invalid accept header
    # try:
    #     # Link a pipeline to a bundle.
    #     api_instance.link_pipeline_to_bundle(bundle_id, pipeline_id)
    #     return True
    # except ApiException as e:
    #     if e.status == 400:
    #         logger.warning(f"Could not link pipeline '{pipeline_id}' to bundle '{bundle_id}'")
    #         logger.warning(e.reason)
    #         logger.warning("This is likely because the pipeline has not been released "
    #                        "(although we currently have no way to confirm nor deny this)")
    #         logger.warning(f"Please run \"icav2 projectpipelines release \"{pipeline_id}\" to release the pipeline")
    #         logger.warning(f"Then run \"icav2 bundles add-pipeline '{bundle_id}' --pipeline-id '{pipeline_id}'\" to add the pipeline to the bundle")
    #         return False
    #     else:
    #         logger.error("Exception when calling BundlePipelineApi->link_pipeline_to_bundle: %s\n" % e)
    #         raise ApiException
    # Use the curl api for now
    curl_returncode, curl_stdout, curl_stderr = run_subprocess_proc(
        [
            "curl",
            "--fail-with-body", "--silent", "--location", "--show-error",
            "--request", "POST",
            "--url",
            f"{get_libicav2_configuration().host}/api/bundles/{bundle_id}/pipelines/{pipeline_id}",
            "--header", "Accept: application/vnd.illumina.v3+json",
            "--header", f"Authorization: Bearer {get_libicav2_configuration().access_token}",
            "--data", ""
        ],
        capture_output=True
    )

    if not curl_returncode == 0:
        if json.loads(curl_stdout).get("status", None) == 409:
            logger.info(f"Pipeline {pipeline_id} already linked to bundle {bundle_id}")
            return False
        logger.error(f"Got the following error while trying to link pipeline {pipeline_id} to bundle {bundle_id}")
        if json.loads(curl_stdout).get("status", None) == 400:
            logger.info(f"Error detail is '{json.loads(curl_stdout).get('detail', None)}'")
        logger.error(curl_stderr)
        raise ChildProcessError

    logger.info(f"Successfully linked pipeline '{pipeline_id}' to '{bundle_id}'")


def add_data_to_bundle(bundle_id: str, data_id: str, data_region_id: Optional[str] = None) -> Optional[bool]:
    """
    Add a data id to a bundle
    Args:
        bundle_id:
        data_id:
        data_region_id:

    Returns:

    """
    if data_region_id is not None and not data_region_id == get_region_id_from_bundle(bundle_id):
        logger.warning(f"Could not link data '{data_id}' to '{bundle_id}'")
        logger.warning(f"Data is not in the same region as the bundle")
        return False

    # with ApiClient(get_libicav2_configuration()) as api_client:
    #     # Create an instance of the API class
    #     api_instance = BundleDataApi(api_client)
    #
    # # example passing only required values which don't have defaults set
    # try:
    #     # Link a pipeline to a bundle.
    #     api_instance.link_data_to_bundle(bundle_id, data_id)
    #     return True
    # except ApiException as e:
    #     logger.error("Exception when calling BundleDataApi->link_data_to_bundle: %s\n" % e)
    #     raise ApiException
    # Use the curl api for now
    curl_returncode, curl_stdout, curl_stderr = run_subprocess_proc(
        [
            "curl",
            "--fail-with-body", "--silent", "--location", "--show-error",
            "--request", "POST",
            "--url",
            f"{get_libicav2_configuration().host}/api/bundles/{bundle_id}/data/{data_id}",
            "--header", "Accept: application/vnd.illumina.v3+json",
            "--header", f"Authorization: Bearer {get_libicav2_configuration().access_token}",
            "--data", ""
        ],
        capture_output=True
    )

    if not curl_returncode == 0:
        if json.loads(curl_stdout).get("status", None) == 409:
            logger.info(f"Data {data_id} already linked to bundle {bundle_id}")
            return False
        logger.error(f"Got the following error while trying to link data {data_id} to bundle {bundle_id}")
        if json.loads(curl_stdout).get("status", None) == 400:
            logger.info(f"Error detail is '{json.loads(curl_stdout).get('detail', None)}'")
        logger.error(curl_stderr)
        raise ChildProcessError

    logger.info(f"Successfully linked data '{data_id}' to '{bundle_id}'")


def release_bundle(bundle_id: str):
    """
    Release a bundle
    Args:
        bundle_id:

    Returns:

    """
    with ApiClient(get_libicav2_configuration()) as api_client:
        # Create an instance of the API class
        api_instance = bundle_api.BundleApi(api_client)

    # example passing only required values which don't have defaults set
    # try:
    #     # release a bundle
    #     api_instance.release_bundle(bundle_id)
    # except ApiException as e:
    #     logger.error("Exception when calling BundleApi->release_bundle: %s\n" % e)
    #     raise ApiException
    curl_returncode, curl_stdout, curl_stderr = run_subprocess_proc(
        [
            "curl",
            "--fail-with-body", "--silent", "--location", "--show-error",
            "--request", "POST",
            "--url",
            f"{get_libicav2_configuration().host}/api/bundles/{bundle_id}:release",
            "--header", "Accept: application/vnd.illumina.v3+json",
            "--header", f"Authorization: Bearer {get_libicav2_configuration().access_token}",
            "--data", ""
        ],
        capture_output=True
    )

    if not curl_returncode == 0:
        logger.error(f"Was not able to release bundle '{bundle_id}'")
        logger.error(f"Stderr: {curl_stderr}")
        logger.error(f"Stdout: {curl_stdout}")
        raise ChildProcessError

    logger.info(f"Successfully released '{bundle_id}'")


def get_bundle_from_id(bundle_id: str) -> Bundle:
    """

    Args:
        bundle_id:

    Returns:

    """
    # Enter a context with an instance of the API client
    with ApiClient(get_libicav2_configuration()) as api_client:
        # Create an instance of the API class
        api_instance = bundle_api.BundleApi(api_client)

    # example passing only required values which don't have defaults set
    try:
        # Retrieve a bundle.
        api_response: Bundle = api_instance.get_bundle(bundle_id)
        return api_response
    except ApiException as e:
        logger.error("Exception when calling BundleApi->get_bundle: %s\n" % e)
        raise ApiException


def get_bundle_from_name(bundle_name: str, region_id: Optional[str] = None) -> Optional[Bundle]:
    """

    Args:
        bundle_name:
        region_id:

    Returns:

    """
    # Enter a context with an instance of the API client
    with ApiClient(get_libicav2_configuration()) as api_client:
        # Create an instance of the API class
        api_instance = bundle_api.BundleApi(api_client)

    # example passing only required values which don't have defaults set
    try:
        # Retrieve a bundle.
        api_response: BundlePagedList = api_instance.get_bundles(search=bundle_name)
    except ApiException as e:
        logger.error("Exception when calling BundleApi->get_bundle: %s\n" % e)
        raise ApiException

    bundle_obj: Bundle
    for bundle_obj in api_response.items:
        if region_id is not None:
            if not bundle_obj.region.id == region_id:
                continue
        if bundle_obj.name == bundle_name:
            return bundle_obj

    return None


def filter_bundles(bundle_name: Optional[str] = None, region_id: Optional[str] = None,
                   status: Optional[str] = None, creator_id: Optional[str] = None) -> Optional[List[Bundle]]:
    """

    Args:
        bundle_name:
        region_id:
        status:
        creator_id:

    Returns:

    """

    # Enter a context with an instance of the API client
    with ApiClient(get_libicav2_configuration()) as api_client:
        # Create an instance of the API class
        api_instance = bundle_api.BundleApi(api_client)

    # example passing only required values which don't have defaults set
    bundle_list = []
    next_page_token = None

    try:
        while True:
            # Retrieve a bundle.
            api_response: BundlePagedList = api_instance.get_bundles(
                page_token="" if next_page_token is None else next_page_token,
                _check_return_type=False
            )
            bundle_list.extend(api_response.items)

            if api_response.next_page_token is not None and not api_response.next_page_token == "":
                next_page_token = api_response.next_page_token
            else:
                break

    except ApiException as e:
        logger.error("Exception when calling BundleApi->get_bundle: %s\n" % e)
        raise ApiException

    # Get each bundle by id
    # Must do this manually due to
    bundle_obj_list = []
    for bundle in bundle_list:
        try:
            bundle_obj_list.append(get_bundle_from_id(bundle.get("id")))
        except TypeError:
            logger.warning(f"Could not convert into bundle obj from id {bundle.get('id')} ")

    bundle: Bundle
    returned_bundle_list: List[Bundle] = []
    for bundle in bundle_obj_list:
        # Check if name matches
        if bundle_name is not None and not bundle.name == bundle_name:
            continue
        # Check region ids match
        if region_id is not None and not bundle.region.id == region_id:
            continue
        # Check bundle status match
        if status is not None and not bundle.status == status:
            continue
        # Check creator id
        if creator_id is not None and not bundle.owner_id == creator_id:
            continue

        returned_bundle_list.append(bundle)

    return returned_bundle_list


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
        user = get_user_from_user_id(creator_id)
        # Set value as firstname ' ' lastname
        creator_dict[user.id] = f"{user.firstname} {user.lastname}"

    bundle_items_df["creator_user"] = bundle_items_df["creator_id"].apply(
        lambda x: creator_dict.get(x, None)
    )

    bundle_items_df_formatted = bundle_items_df[[
        "id",
        "name",
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


def list_data_in_bundles(bundle_id: str) -> List[Dict]:
    """

    Returns:

    """
    page_token=""
    data_items = []

    while True:
        # Use the curl api for now
        curl_returncode, curl_stdout, curl_stderr = run_subprocess_proc(
            [
                "curl",
                "--fail-with-body", "--silent", "--location", "--show-error",
                "--request", "GET",
                "--url",
                f"{get_libicav2_configuration().host}/api/bundles/{bundle_id}/data?pageToken={page_token}",
                "--header", "Accept: application/vnd.illumina.v3+json",
                "--header", f"Authorization: Bearer {get_libicav2_configuration().access_token}",
            ],
            capture_output=True
        )

        if not curl_returncode == 0:
            logger.error(curl_stderr)
            raise ChildProcessError

        curl_stdout_dict = json.loads(curl_stdout)

        data_items.extend(
            map(
                lambda x: {
                 "data_id": x.get("data").get("id"),
                 "data_uri": f"icav2://"
                             f"{x.get('data').get('details').get('owningProjectName')}"
                             f"{x.get('data').get('details').get('path')}"
                },
                curl_stdout_dict.get("items")
            )
        )

        if curl_stdout_dict.get("nextPageToken") == "":
            break
        page_token = curl_stdout_dict.get("nextPageToken")

    return data_items


def list_pipelines_in_bundles(bundle_id: str) -> List[Dict]:
    """

    Returns:

    """
    data_items = []

    # Use the curl api for now
    # No looping for pipelines
    # page_token=""
    curl_returncode, curl_stdout, curl_stderr = run_subprocess_proc(
        [
            "curl",
            "--fail-with-body", "--silent", "--location", "--show-error",
            "--request", "GET",
            "--url",
            f"{get_libicav2_configuration().host}/api/bundles/{bundle_id}/pipelines",
            "--header", "Accept: application/vnd.illumina.v3+json",
            "--header", f"Authorization: Bearer {get_libicav2_configuration().access_token}",
        ],
        capture_output=True
    )

    if not curl_returncode == 0:
        logger.error(curl_stdout)
        logger.error(curl_stderr)
        raise ChildProcessError

    curl_stdout_dict = json.loads(curl_stdout)

    data_items.extend(
        map(
            lambda x: {
             "pipeline_id": x.get("pipeline").get("id"),
             # FIXME get tenantName as query attribute
             "pipeline_code": x.get("pipeline").get("code")
            },
            curl_stdout_dict.get("items")
        )
    )

    return data_items


def get_bundle_dict_object(bundle_id: str) -> Dict:
    curl_returncode, curl_stdout, curl_stderr = run_subprocess_proc(
        [
            "curl",
            "--fail-with-body", "--silent", "--location", "--show-error",
            "--request", "GET",
            "--url", f"{get_libicav2_configuration().host}/api/bundles/{bundle_id}",
            "--header", "Accept: application/vnd.illumina.v3+json",
            "--header", f"Authorization: Bearer {get_libicav2_configuration().access_token}",
        ],
        capture_output=True
    )

    if not curl_returncode == 0:
        logger.error(curl_stdout)
        logger.error(curl_stderr)
        raise ChildProcessError

    return json.loads(curl_stdout)


def get_bundle_region_id(bundle_id):
    return get_bundle_dict_object(bundle_id).get("region").get("id")


def get_bundle_region_city_name(bundle_id):
    return get_bundle_dict_object(bundle_id).get("region").get("cityName")


def get_bundle_name_from_bundle_id(bundle_id):
    return get_bundle_dict_object(bundle_id).get("name")


def get_bundle_description_from_bundle_id(bundle_id):
    return get_bundle_dict_object(bundle_id).get("shortDescription")


def get_bundle_release_version(bundle_id):
    return get_bundle_dict_object(bundle_id).get("releaseVersion")


def get_bundle_tenant_id(bundle_id):
    return get_bundle_dict_object(bundle_id).get("tenantId")


def get_bundle_tenant_name(bundle_id):
    return get_bundle_dict_object(bundle_id).get("tenantName")


def bundle_to_yaml_obj(bundle_id: str, file_h: TextIO):
    """
    Collect bundle as a yaml object - useful if a user wants to initialise a new bundle with a similar template
    Returns:

    """
    yaml = YAML()

    yaml.indent(mapping=2, sequence=4, offset=2)

    return yaml.dump(
        {
            "region": {
                "region_id": get_bundle_region_id(bundle_id),
                "region_city_name": get_bundle_region_city_name(bundle_id)
            },
            "tenant": {
                "tenant_id": get_bundle_tenant_id(bundle_id),
                "tenant_name": get_bundle_tenant_name(bundle_id)
            },
            "bundle_metadata": {
                "bundle_id": bundle_id,
                "bundle_name": get_bundle_name_from_bundle_id(bundle_id),
                "bundle_short_description": get_bundle_description_from_bundle_id(bundle_id),
                "bundle_release_version": get_bundle_release_version(bundle_id)
            },
            "data": list_data_in_bundles(bundle_id),
            "pipeline": list_pipelines_in_bundles(bundle_id)
        },
        file_h
    )


