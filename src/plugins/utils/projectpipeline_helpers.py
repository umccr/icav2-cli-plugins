import json
from json import JSONDecodeError
from pathlib import Path
from typing import Dict, Optional, List, Any, Union, Tuple
from urllib.parse import urlparse

from libica.openapi.v2.model.analysis import Analysis

from libica.openapi.v2.api.project_analysis_api import ProjectAnalysisApi

from libica.openapi.v2.model.create_data import CreateData

from libica.openapi.v2.api.project_data_api import ProjectDataApi

from libica.openapi.v2.model.cwl_analysis_input import CwlAnalysisInput

from libica.openapi.v2.model.create_cwl_analysis import CreateCwlAnalysis

from libica.openapi.v2.model.pipeline import Pipeline

from libica.openapi.v2.api.pipeline_api import PipelineApi

from libica.openapi.v2.model.analysis_input_data_mount import AnalysisInputDataMount
from libica.openapi.v2.model.project_data import ProjectData

from libica.openapi.v2.model.analysis_tag import AnalysisTag

from libica.openapi.v2.model.project_pipeline import ProjectPipeline

from libica.openapi.v2.model.project_pipeline_list import ProjectPipelineList

from libica.openapi.v2.api.project_pipeline_api import ProjectPipelineApi

from libica.openapi.v2 import ApiClient, ApiException
from libica.openapi.v2.api.analysis_storage_api import AnalysisStorageApi
from utils import sanitise_dict_keys
from utils.config_helpers import get_libicav2_configuration
from utils.cwl_typing_helpers import WorkflowInputParameter
from utils.globals import ICAv2AnalysisStorageSize, BLANK_PARAMS_XML_V2_FILE_CONTENTS
from utils.logger import get_logger

from utils.projectdata_helpers import list_data_non_recursively, convert_icav2_uri_to_data_obj
from utils.subprocess_handler import run_subprocess_proc

logger = get_logger()


class ICAv2PipelineAnalysisTags:
    """
    List of tags
    """
    def __init__(self, technical_tags: List, user_tags: List, reference_tags: List):
        """
        List of tags to use in the pipeline
        :param technical_tags:
        :param user_tags:
        :param reference_tags:
        """
        self.technical_tags = technical_tags
        self.user_tags = user_tags
        self.reference_tags = reference_tags

    def __call__(self) -> AnalysisTag:
        return AnalysisTag(
            technical_tags=self.technical_tags,
            user_tags=self.user_tags,
            reference_tags=self.reference_tags
        )

    @classmethod
    def from_dict(cls, tags_dict):
        # Convert camel cases to snake cases
        tags_dict = sanitise_dict_keys(tags_dict)

        return cls(
                    technical_tags=tags_dict.get("technical_tags", []),
                    user_tags=tags_dict.get("user_tags", []),
                    reference_tags=tags_dict.get("reference_tags", [])
        )


class ICAv2EngineParameters:
    """
    The ICAv2 EngineParameters has the following properties
    *
    """
    def __init__(self, output_parent_folder_id: Optional[str], output_parent_folder_path: Optional[str],
                 tags: Dict,
                 analysis_storage_id: Optional[str], analysis_storage_size: Optional[str],
                 activation_id: Optional[str], cwltool_overrides: Dict,
                 # stream_all_files, stream_all_directories
                 ):

        self.output_parent_folder_id: Optional[str] = output_parent_folder_id
        self.output_parent_folder_path: Optional[Path] = output_parent_folder_path
        self.tags: ICAv2PipelineAnalysisTags = ICAv2PipelineAnalysisTags.from_dict(tags)
        self.analysis_storage_id: Optional[str] = analysis_storage_id
        self.analysis_storage_size: Optional[str] = analysis_storage_size
        self.activation_id: Optional[str] = activation_id
        self.cwltool_overrides: Dict = cwltool_overrides
        # self.stream_all_files: Optional[bool] = stream_all_files
        # self.stream_all_directories: Optional[bool] = stream_all_directories

    def update_engine_parameter(self, attribute_name: str, value: Any):
        self.__setattr__(attribute_name, value)

    def populate_empty_engine_parameters(self, project_id: str, pipeline_id: str, input_json: Dict,
                                         mount_list: List[AnalysisInputDataMount]):
        
        if self.analysis_storage_id is None:
            self.analysis_storage_id = get_set_analysis_storage_id_from_pipeline(
                pipeline_id
            )
        if self.activation_id is None:
            self.activation_id = get_activation_id(
                project_id, pipeline_id, input_json,
                mount_list
            )

        if self.output_parent_folder_path is not None and self.output_parent_folder_id is None:
            self.output_parent_folder_path = Path(self.output_parent_folder_path)
            if not self.output_parent_folder_path.is_absolute():
                logger.error("Please ensure engine parameter output_folder_path is an absolute path")
            try:
                self.output_parent_folder_id = get_data_obj_from_project_id_and_path(
                    project_id,
                    str(self.output_parent_folder_path) + "/",
                ).data.id
            except FileNotFoundError:
                self.output_parent_folder_id = create_data_obj_from_project_id_and_path(
                    project_id,
                    str(self.output_parent_folder_path) + "/",
                )

    # from_dict - read in input
    @classmethod
    def from_dict(cls, engine_parameter_dict):
        """
        Create a ICAWorkflowVersion object from a dictionary
        :return:
        """

        # Convert camel cases to snake cases
        engine_parameter_dict = sanitise_dict_keys(engine_parameter_dict)

        return cls(
                    output_parent_folder_id=engine_parameter_dict.get("output_parent_folder_id", None),
                    output_parent_folder_path=engine_parameter_dict.get("output_parent_folder_path", None),
                    tags=engine_parameter_dict.get("tags", {}),
                    analysis_storage_id=engine_parameter_dict.get("analysis_storage_id", None),
                    analysis_storage_size=engine_parameter_dict.get("analysis_storage_size", None),
                    activation_id=engine_parameter_dict.get("activation_id", None),
                    cwltool_overrides=engine_parameter_dict.get("cwltool_overrides", {})
                   )


class ICAv2LaunchJson:
    """
    The ICAv2 Launch Json has the following properties
        * user_reference: str
        * input_json: Dict  (cwl_inputs)
        * engine_parameters: ICAv2EngineParameters
    """

    def __init__(self, user_reference: str, input_json: Dict, engine_parameters: Dict):
        """
        Initialise input
        :param user_reference:
        :param input_json:
        :param engine_parameters:
        """
        # Get parameters
        self.user_reference: str = user_reference
        self.input_json: Dict = input_json
        self.engine_parameters: ICAv2EngineParameters = ICAv2EngineParameters.from_dict(engine_parameters)

        # Other parts we set up later
        self.input_json_deferenced: Optional[Dict] = None
        self.data_ids: Optional[List[str]] = None
        self.mount_paths: Optional[List[AnalysisInputDataMount]] = None

    def update_engine_parameter(self, attribute_name, value):
        self.engine_parameters.update_engine_parameter(attribute_name, value)

    def populate_empty_engine_parameters(self, project_id: str, pipeline_id):
        # Update empty engine parameters
        self.engine_parameters.populate_empty_engine_parameters(
            project_id,
            pipeline_id,
            self.input_json_deferenced,
            self.mount_paths
        )

    def collect_overrides_from_engine_parameters(self):
        # If overrides are in the engine parameters, put them in the input json
        input_json_cwltooloverrides = self.input_json.get("cwltool:overrides", {})
        engine_parameter_cwltooloverrides = self.engine_parameters.cwltool_overrides.copy()
        if engine_parameter_cwltooloverrides is None:
            # Nothing to do here
            return
        # Don't override existing overrides in the input json
        # We do this by first updating the engine parameter cwltooloverrides with the input json overrides
        # Then pulling them back again
        key: str
        value: Any
        for key, value in input_json_cwltooloverrides.items():
            if key in engine_parameter_cwltooloverrides.keys():
                engine_parameter_cwltooloverrides[key].update(value)
            else:
                engine_parameter_cwltooloverrides[key] = value
        # Now we pull them back in again
        for key, value in engine_parameter_cwltooloverrides.items():
            input_json_cwltooloverrides[key] = value
        if len(input_json_cwltooloverrides) == 0:
            # Nothing to set here, just return nothing
            return
        # Otherwise set the value in the cwltool:overrides attribute of the input json
        self.input_json["cwltool:overrides"] = input_json_cwltooloverrides
        # If weve already gone and dereferenced, we set that then too
        if self.input_json_deferenced is not None:
            self.input_json_deferenced["cwltool:overrides"] = input_json_cwltooloverrides

    def deference_input_json(self):
        self.input_json_deferenced, self.mount_paths = convert_icav2_uris_to_data_ids(
            self.input_json
        )
        self.data_ids = list(map(lambda x: x.data_id, self.mount_paths))

    # from_dict - read in input
    @classmethod
    def from_dict(cls, launch_json_dict):
        """
        Create a ICAWorkflowVersion object from a dictionary
        :return:
        """
        # Convert camel cases to snake cases
        launch_json_dict = sanitise_dict_keys(launch_json_dict)

        return cls(
            user_reference=launch_json_dict.get(
                "user_reference",
                launch_json_dict.get(
                    "name",
                    None
                )
            ),
            input_json=launch_json_dict.get(
                "input",
                launch_json_dict.get(
                    "inputs",
                    {}
                )
            ),
            engine_parameters=launch_json_dict.get(
                "engine_parameters", {}
            )
        )

    def create_cwl_analysis_obj(self, pipeline_id: str) -> CreateCwlAnalysis:
        return CreateCwlAnalysis(
            user_reference=self.user_reference,
            pipeline_id=pipeline_id,
            tags=self.engine_parameters.tags(),
            activation_code_detail_id=self.engine_parameters.activation_id,
            analysis_input=CwlAnalysisInput(
                object_type="JSON",
                input_json=json.dumps(self.input_json_deferenced, indent=2),
                mounts=self.mount_paths,
                data_ids=self.data_ids
            ),
            analysis_storage_id=self.engine_parameters.analysis_storage_id,
            output_parent_folder_id=self.engine_parameters.output_parent_folder_id
        )

    def __call__(self, pipeline_id: str) -> CreateCwlAnalysis:
        # Parse object command to send workflow
        return self.create_cwl_analysis_obj(pipeline_id)



def presign_cwl_directory(project_id: str, data_id: str) -> List[
    Union[Dict[str, Union[Union[dict, str], Any]], Dict[str, Union[str, Any]]]]:
    # Data ids
    cwl_item_objs = []

    # List items noncursively
    file_obj_list = list_data_non_recursively(
        project_id=project_id,
        parent_folder_id=data_id
    )

    # Collect file object list
    for file_item_obj in file_obj_list:
        data_type: str = file_item_obj.get("data").get("details").get('data_type')  # One of FILE | FOLDER
        data_id = file_item_obj.get("data").get("id")
        basename = file_item_obj.get("data").get("details").get("name")
        if data_type == "FOLDER":
            cwl_item_objs.append(
                {
                    "class": "Directory",
                    "basename": basename,
                    "listing": presign_cwl_directory(project_id, data_id)
                }
            )
        else:
            cwl_item_objs.append(
                {
                    "class": "File",
                    "basename": basename,
                    "location": create_download_url(project_id, data_id)
                }
            )

    return cwl_item_objs


def create_data_obj_from_project_id_and_path(project_id: str, data_path: str) -> str:
    # Enter a context with an instance of the API client
    with ApiClient(get_libicav2_configuration()) as api_client:
        # Create an instance of the API class
        api_instance = ProjectDataApi(api_client)
        create_data = CreateData(
            name=Path(data_path).name,
            folder_path=str(Path(data_path).parent) + "/",
            data_type="FOLDER" if data_path.endswith("/") else "FILE",
        )  # CreateData | The data to create. (optional)

        # example passing only required values which don't have defaults set
        try:
            # Create data in this project.
            api_response: ProjectData = api_instance.create_data_in_project(project_id, create_data=create_data)
        except ApiException as e:
            raise ValueError("Exception when calling ProjectDataApi->create_data_in_project: %s\n" % e)

    return api_response.data.id


def convert_icav2_uris_to_data_ids(input_obj: Union[str, int, bool, Dict, List]) -> Tuple[
    Union[str, Dict, List], List[Dict]]:
    # Set default mount_list
    input_obj_new_list = []
    mount_list = []

    # Convert basic types
    if isinstance(input_obj, bool) or isinstance(input_obj, int) or isinstance(input_obj, str):
        return input_obj, mount_list

    # Convert dict or list types recursively
    if isinstance(input_obj, List):
        for input_item in input_obj:
            input_obj_new_item, mount_list_new = convert_icav2_uris_to_data_ids(input_item)
            mount_list.extend(mount_list_new)
            input_obj_new_list.append(input_obj_new_item)
        return input_obj_new_list, mount_list
    if isinstance(input_obj, Dict):
        if "class" in input_obj.keys() and input_obj["class"] in ["File", "Directory"]:
            # Resolve location
            if input_obj.get("location", "").startswith("icav2://"):
                # Get relative location path
                input_obj_new: ProjectData = convert_icav2_uri_to_data_obj(input_obj.get("location"))
                data_type: str = input_obj_new.get("data").get("details").get('data_type')  # One of FILE | FOLDER
                owning_project_id: str = input_obj_new.get("data").get("details").get("owning_project_id")
                data_id = input_obj_new.get("data").get("id")
                basename = input_obj_new.get("data").get("details").get("name")

                # Check presign, # FIXME also functionalise this, may need this for cross-tenant data collection later
                presign_list = list(
                    filter(
                        lambda x: x == "presign=true",
                        urlparse(input_obj.get("location")).query.split("&")
                    )
                )
                if len(presign_list) > 0:
                    is_presign = True
                else:
                    is_presign = False

                # Set mount path
                mount_path = str(
                    Path(owning_project_id) /
                    Path(data_id) /
                    Path(basename)
                )

                # Check data types match
                if data_type == "FOLDER" and input_obj["class"] == "File":
                    logger.error("Got mismatch on data type and class for input object")
                    logger.error(f"Class of {input_obj.get('location')} is set to file but found directory id {data_id} instead")
                    raise ValueError
                if data_type == "FILE" and input_obj["class"] == "Directory":
                    logger.error("Got mismatch on data type and class for input object")
                    logger.error(f"Class of {input_obj.get('location')} is set to directory but found file id {data_id} instead")

                # Set file to presigned url
                if data_type == "FILE" and is_presign:
                    input_obj["location"] = create_download_url(owning_project_id, data_id)
                # Set data folder as streamable recursively
                elif data_type == "FOLDER" and is_presign:
                    input_obj["location"] = mount_path
                    input_obj["listing"] = presign_cwl_directory(
                        owning_project_id, data_id
                    )
                else:
                    mount_list.append(
                        AnalysisInputDataMount(
                            data_id=data_id,
                            mount_path=mount_path
                        )
                    )

                    input_obj["location"] = mount_path

            # Get secondary Files
            if not len(input_obj.get("secondaryFiles", [])) == 0:
                old_secondary_files = input_obj.get("secondaryFiles", [])
                input_obj["secondaryFiles"] = []
                for input_item in old_secondary_files:
                    input_obj_new_item, mount_list_new = convert_icav2_uris_to_data_ids(input_item)
                    mount_list.extend(mount_list_new)
                    input_obj["secondaryFiles"].append(input_obj_new_item)

            return input_obj, mount_list
        else:
            input_obj_dict = {}
            for key, value in input_obj.items():
                input_obj_dict[key], mount_list_new = convert_icav2_uris_to_data_ids(value)
                mount_list.extend(mount_list_new)
            return input_obj_dict, mount_list


def create_download_url(project_id: str, data_id: str) -> str:
    """
    Create download URL
    :param project_id:
    :param data_id:
    :return:
    """
    configuration = get_libicav2_configuration()

    curl_command_list = [
        "curl",
        "--fail", "--silent", "--location",
        "--request", "POST",
        "--url", f"{configuration.host}/api/projects/{project_id}/data/{data_id}:createDownloadUrl",
        "--header", "Accept: application/vnd.illumina.v3+json",
        "--header", f"Authorization: Bearer {configuration.access_token}",
        "--data", ""
    ]

    command_returncode, command_stdout, command_stderr = run_subprocess_proc(
        curl_command_list, capture_output=True
    )

    if not command_returncode == 0:
        logger.error(f"Could not create a download url for project id '{project_id}', data id '{data_id}'")
        raise ValueError

    return json.loads(command_stdout).get("url")


def get_data_obj_from_project_id_and_path(project_id: str, data_path: str) -> ProjectData:
    # Enter a context with an instance of the API client
    with ApiClient(get_libicav2_configuration()) as api_client:
        # Create an instance of the API class
        api_instance = ProjectDataApi(api_client)
        file_path = [
            data_path,
        ]  # [str] | The paths of the files to filter on. (optional)
        file_path_match_mode = "FULL_CASE_INSENSITIVE"  # str | How the file paths are filtered:   - STARTS_WITH_CASE_INSENSITIVE: Filters the file path to start with the value of the 'filePath' parameter, regardless of upper/lower casing. This allows e.g. listing all data in a folder and all it's sub-folders (recursively).  - FULL_CASE_INSENSITIVE: Filters the file path to fully match the value of the 'filePath' parameter, regardless of upper/lower casing. Note that this can result in multiple results if e.g. two files exist with the same filename but different casing (abc.txt and ABC.txt). (optional) if omitted the server will use the default value of "STARTS_WITH_CASE_INSENSITIVE"
        data_type = "FOLDER" if data_path.endswith("/") else "FILE"
        parent_folder_path = str(Path(data_path).parent) + "/"
        page_size = 1000  # str | The amount of rows to return. Use in combination with the offset or cursor parameter to get subsequent results. (optional)

        # example passing only required values which don't have defaults set
        try:
            # Retrieve the list of project data.
            api_response = api_instance.get_project_data_list(
                project_id,
                file_path=file_path,
                file_path_match_mode=file_path_match_mode,
                type=data_type,
                parent_folder_path=parent_folder_path,
                page_size=str(page_size)
            )
        except ApiException as e:
            raise ValueError("Exception when calling ProjectDataApi->get_project_data_list: %s\n" % e)

    project_data_list = api_response.items
    if len(project_data_list) == 0:
        raise FileNotFoundError(f"Could not find the file/directory {data_path} in project {project_id}")
    elif len(project_data_list) == 1:
        return project_data_list[0]
    else:
        raise FileNotFoundError(f"Found multiple results for {data_path} in project {project_id}")


def get_data_obj_by_id(project_id: str, data_id: str) -> str:
    # Enter a context with an instance of the API client
    with ApiClient(get_libicav2_configuration()) as api_client:
        # Create an instance of the API class
        api_instance = ProjectDataApi(api_client)

        # example passing only required values which don't have defaults set
        try:
            # Retrieve a project data.
            api_response = api_instance.get_project_data(project_id, data_id)
        except ApiException as e:
            raise ValueError("Exception when calling ProjectDataApi->get_project_data: %s\n" % e)
    return api_response.data


def get_activation_id(project_id: str, pipeline_id: str, input_json: Dict,
                      mount_list: List[AnalysisInputDataMount]) -> str:
    """
    Get the activation id from the activationCodes api endpoint
    :param project_id: 
    :param pipeline_id: 
    :param input_json: 
    :param mount_list: 
    :return:
    """
    # Collect access token
    configuration = get_libicav2_configuration()
    icav2_access_token = configuration.access_token

    # Curl command waiting on https://github.com/umccr-illumina/libica/issues/75 to be resolved
    curl_command_list = [
        "curl",
        "--fail", "--silent", "--location",
        "--request", "POST",
        "--url", f"{configuration.host}/api/activationCodes:findBestMatchingForCwl",
        "--header", "Accept: application/vnd.illumina.v3+json",
        "--header", f"Authorization: Bearer {icav2_access_token}",
        "--header", "Content-Type: application/vnd.illumina.v3+json",
        "--data", json.dumps(
            {

                "projectId": project_id,
                "pipelineId": pipeline_id,
                "analysisInput": {
                    "objectType": "JSON",
                    "inputJson": json.dumps(input_json, indent=2),
                    "dataIds": list(map(lambda x: x.data_id, mount_list)),
                    "mounts": [
                        {
                            "dataId": mount_item.data_id,
                            "mountPath": mount_item.mount_path
                        }
                        for mount_item in mount_list
                    ]
                }
            }
        )
    ]

    command_returncode, command_stdout, command_stderr = run_subprocess_proc(
        curl_command_list, capture_output=True
    )

    if not command_returncode == 0:
        logger.error("Could not collect activation id")
        raise ChildProcessError

    return json.loads(command_stdout).get("id")


def get_set_analysis_storage_id_from_pipeline(pipeline_id: str) -> str:
    # Enter a context with an instance of the API client
    with ApiClient(get_libicav2_configuration()) as api_client:
        # Create an instance of the API class
        api_instance = PipelineApi(api_client)

    # example passing only required values which don't have defaults set
    try:
        # Retrieve a pipeline.
        api_response: Pipeline = api_instance.get_pipeline(pipeline_id)
    except ApiException as e:
        raise ValueError("Exception when calling PipelineApi->get_pipeline: %s\n" % e)

    return api_response.analysis_storage.id


def get_pipeline_id_from_pipeline_code(project_id: str, pipeline_code: str) -> str:
    """
    List project pipelines, return one with matching pipeline code
    :param project_id:
    :param pipeline_code:
    :return:
    """

    # Enter a context with an instance of the API client
    with ApiClient(get_libicav2_configuration()) as api_client:
        # Create an instance of the API class
        api_instance = ProjectPipelineApi(api_client)

    # example passing only required values which don't have defaults set
    try:
        # Retrieve a list of project pipelines.
        api_response: ProjectPipelineList = api_instance.get_project_pipelines(project_id)
    except ApiException as e:
        logger.error("Exception when calling ProjectPipelineApi->get_project_pipelines: %s\n" % e)
        raise ValueError

    project_pipeline_obj: ProjectPipeline
    for project_pipeline_obj in api_response.items:
        if pipeline_code == project_pipeline_obj.pipeline.code:
            return project_pipeline_obj.pipeline.id

    logger.error(f"Could not find pipeline '{pipeline_code}' in project {project_id}")
    raise ValueError


def get_pipeline_description_from_pipeline_id(project_id: str, pipeline_id: str) -> str:
    # Get the project pipeline
    project_pipeline_obj = get_project_pipeline(
        project_id=project_id,
        pipeline_id=pipeline_id
    )

    pipeline_obj: Pipeline = project_pipeline_obj.pipeline

    return pipeline_obj.description


def get_project_pipeline(project_id: str, pipeline_id: str) -> ProjectPipeline:
    """
    Get a project pipeline dict
    :param project_id:
    :param pipeline_id:
    :return:
    """

    # Initialise instance
    with ApiClient(get_libicav2_configuration()) as api_client:
        # Create an instance of the API class
        api_instance = ProjectPipelineApi(api_client)

    # example passing only required values which don't have defaults set
    try:
        # Retrieve a project pipeline.
        api_response = api_instance.get_project_pipeline(project_id, pipeline_id)
    except ApiException as e:
        logger.error("Exception when calling ProjectPipelineApi->get_project_pipeline: %s\n" % e)
        raise ValueError

    return api_response


def get_analysis_storage_id_from_analysis_storage_size(analysis_storage_size: ICAv2AnalysisStorageSize) -> str:
    """
    Get the analysis storage size id
    :param analysis_storage_size:
    :return:
    """
    # Create an instance of the API class
    # Enter a context with an instance of the API client
    with ApiClient(get_libicav2_configuration()) as api_client:
        # Create an instance of the API class
        api_instance = AnalysisStorageApi(api_client)

    # example, this endpoint has no required or optional parameters
    try:
        # Retrieve the list of analysis storage options.
        api_response = api_instance.get_analysis_storage_options()
    except ApiException as e:
        raise ValueError("Exception when calling AnalysisStorageApi->get_analysis_storage_options: %s\n" % e)

    analysis_storage_list = list(
        filter(lambda x: x.name == analysis_storage_size.value,
               api_response.items
               )
    )

    if len(analysis_storage_list) == 0:
        raise ValueError(f"Could not find analysis storage size {analysis_storage_size} in this region")

    return analysis_storage_list[0].id


def recursively_build_open_api_body_from_libica_item(libica_item: Any) -> Union[Dict, Any]:
    if not isinstance(libica_item, object) or isinstance(libica_item, str):
        return libica_item
    open_api_body_dict = {}
    for key, value in libica_item._data_store.items():
        if isinstance(value, List):
            output_value = [
                recursively_build_open_api_body_from_libica_item(value_item)
                for value_item in value
            ]
        elif isinstance(value, object) and hasattr(value, "_data_store"):
            output_value = recursively_build_open_api_body_from_libica_item(value)
        else:
            output_value = value
        open_api_body_dict[libica_item.attribute_map.get(key)] = output_value
    return open_api_body_dict


def launch_cwl_workflow(
        project_id: str,
        cwl_analysis: CreateCwlAnalysis) -> Tuple[str, str]:
    # Enter a context with an instance of the API client
    with ApiClient(get_libicav2_configuration()) as api_client:
        # Create an instance of the API class
        api_instance = ProjectAnalysisApi(api_client)

        # example passing only required values which don't have defaults set
        try:
            # Create and start an analysis for a CWL pipeline.
            api_response: Analysis = api_instance.create_cwl_analysis(
                project_id=project_id,
                create_cwl_analysis=cwl_analysis
            )
        except ApiException as e:
            raise ValueError("Exception when calling ProjectAnalysisApi->create_cwl_analysis: %s\n" % e)

    return api_response.id, api_response.user_reference


def get_cwl_analysis_input_json(project_id: str, analysis_id: str):

    configuration = get_libicav2_configuration()

    curl_command_list = [
        "curl",
        "--fail", "--silent", "--location",
        "--request", "GET",
        "--url", f"{configuration.host}/api/projects/{project_id}/analyses/{analysis_id}/cwl/inputJson",
        "--header", "Accept: application/vnd.illumina.v3+json",
        "--header", f"Authorization: Bearer {configuration.access_token}"
    ]

    command_returncode, command_stdout, command_stderr = run_subprocess_proc(
        curl_command_list, capture_output=True
    )

    if not command_returncode == 0:
        logger.error(f"Could not collect input json for analysis id '{analysis_id}'")
        raise ChildProcessError

    return json.loads(json.loads(command_stdout).get("inputJson"))


def get_cwl_analysis_output_json(project_id: str, analysis_id: str):
    """
    Get the cwl analysis output json
    :param project_id:
    :param analysis_id:
    :return:
    """
    configuration = get_libicav2_configuration()

    curl_command_list = [
        "curl",
        "--fail", "--silent", "--location",
        "--request", "GET",
        "--url", f"{configuration.host}/api/projects/{project_id}/analyses/{analysis_id}/cwl/outputJson",
        "--header", "Accept: application/vnd.illumina.v3+json",
        "--header", f"Authorization: Bearer {configuration.access_token}"
    ]

    command_returncode, command_stdout, command_stderr = run_subprocess_proc(
        curl_command_list, capture_output=True
    )

    if not command_returncode == 0:
        logger.error(f"Could not collect input json for analysis id '{analysis_id}'")
        raise ChildProcessError

    output_json = json.loads(command_stdout).get("outputJson")
    try:
        return json.loads(output_json)
    except JSONDecodeError:
        logger.error(f"Could not decode '{output_json}' as valid json")
        return None


def create_params_xml(inputs: List[WorkflowInputParameter], output_path: Path):
    """
    From the inputs, create a params xml file
    :param inputs:
    :param output_path:
    :return:
    """
    # FIXME - waiting on https://github.com/umccr-illumina/ica_v2/issues/17
    return create_blank_params_xml(output_path)


def create_blank_params_xml(output_file_path: Path):
    """
    Create a params.xml file with no inputs
    :param output_file_path:
    :return:
    """
    with open(output_file_path, "w") as params_h:
        for line in BLANK_PARAMS_XML_V2_FILE_CONTENTS:
            params_h.write(line + "\n")
