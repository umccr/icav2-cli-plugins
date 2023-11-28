#!/usr/bin/env python3

"""
CWL Handlers
"""
import hashlib
import os
import re
import subprocess
from copy import deepcopy
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Union, Tuple
import json
import sys

from zipfile import ZipFile

from mdutils import MdUtils

from ruamel import yaml
from utils.config_helpers import get_libicav2_configuration
from utils.cwl_typing_helpers import InputEnumSchemaType, InputRecordSchemaType, InputArraySchemaType
from utils.logger import get_logger

from utils.subprocess_handler import run_subprocess_proc

from cwl_utils.parser import load_document_by_uri, \
    Workflow, \
    WorkflowStep, \
    CommandLineTool

from cwl_utils.parser.latest import \
    WorkflowInputParameter, \
    WorkflowOutputParameter, \
    shortname, \
    RecordSchema

from cwl_utils.pack import pack

from urllib.parse import urlparse

from tempfile import TemporaryDirectory, NamedTemporaryFile

logger = get_logger()


class CWLSchema:
    """
    Missing component of cwlutils
    """

    def __init__(self, cwl_obj, file_path):
        self.cwl_obj: RecordSchema = cwl_obj
        self.cwl_file_path: Path = file_path

        # Confirm type is record
        if not self.cwl_obj.type.get("type") == "record":
            logger.error("Expected record type")

    def get_input_from_str_type(self, workflow_input: Dict) -> Union[Dict, str, List]:
        if workflow_input.get("type").endswith("[]"):
            new_workflow_input = deepcopy(workflow_input)
            new_workflow_input["type"] = re.sub(r"\[]$", "", workflow_input.get("type"))
            return [
                self.get_input_from_str_type(new_workflow_input)
            ]
        if workflow_input.get("type").rstrip("?") == "Directory":
            return {
                "class": "Directory",
                "location": "icav2://project_id/path/to/dir/"
            }
        elif workflow_input.get("type").rstrip("?") == "File":
            return {
                "class": "File",
                "location": "icav2://project_id/path/to/file"
            }
        elif workflow_input.get("type").rstrip("?") == "boolean":
            return workflow_input.get("default") if workflow_input.get("default") is not None else False
        elif workflow_input.get("type").rstrip("?") == "int":
            return workflow_input.get("default") if workflow_input.get("default") is not None else "string"
        elif workflow_input.get("type").rstrip("?") == "string":
            return workflow_input.get("default") if workflow_input.get("default") is not None else "string"

    def get_input_from_array_type(self, workflow_input: Dict) -> Union[Dict, str, List]:
        """
        Likely first element of type is null
        :param workflow_input:
        :return:
        """
        workflow_input_new = deepcopy(workflow_input)
        if workflow_input.get("type")[0] == "null":
            workflow_input_new["type"] = workflow_input.get("type")[1]
        else:
            workflow_input_new["type"] = workflow_input.get("type")[0]

        if isinstance(workflow_input_new.get("type"), Dict):
            return self.get_input_from_dict_type(workflow_input_new)
        elif isinstance(workflow_input_new.get("type"), List):
            return self.get_input_from_array_type(workflow_input_new)
        elif isinstance(workflow_input_new.get("type"), str):
            return self.get_input_from_str_type(workflow_input_new)
        else:
            logger.error(f"Unsure what to do with type {type(workflow_input_new.get('type'))}")
            raise NotImplementedError

    def get_input_from_record_type(self, workflow_input: Dict) -> Union[Dict]:
        """
        Very similar to schema base command
        :param workflow_input:
        :return:
        """
        workflow_inputs = {}
        for field_key, field_dict in workflow_input.get("fields").items():
            if isinstance(field_dict.get("type"), Dict):
                workflow_inputs.update(
                    {
                        field_key: self.get_input_from_dict_type(field_dict)
                    }
                )
            elif isinstance(field_dict.get("type"), List):
                workflow_inputs.update(
                    {
                        field_key: self.get_input_from_array_type(field_dict)
                    }
                )
            elif isinstance(field_dict.get("type"), str):
                workflow_inputs.update(
                    {
                        field_key: self.get_input_from_str_type(field_dict)
                    }
                )
            else:
                logger.warning(f"Don't know what to do with type {type(field_dict.get('type'))} for key {field_key}")
        return workflow_inputs

    def get_input_from_dict_type(self, workflow_input: Dict) -> Union[Dict, List]:
        """
        Dict type
        :param workflow_input:
        :return:
        """
        if "type" in workflow_input.get("type").keys() and workflow_input.get("type").get("type") == "record":
            return self.get_input_from_record_type(workflow_input.get("type"))
        if "type" in workflow_input.get("type").keys() and workflow_input.get("type").get("type") == "array":
            if isinstance(workflow_input.get("type").get("items"), str):
                return [
                    self.get_input_from_str_type(
                        {
                            "type": workflow_input.get("type").get("items")
                        }
                    )
                ]
            elif isinstance(workflow_input.get("type").get("items"), Dict):
                # We have an import
                return self.get_input_from_dict_type(
                    {
                        "type": workflow_input.get("type").get("items")
                    }
                )
        if "$import" in workflow_input.get("type").keys():
            schema_path = self.cwl_file_path.parent.joinpath(
                workflow_input.get("type").get("$import").split("#", 1)[0]
            ).resolve()
            return CWLSchema.load_schema_from_uri(schema_path.as_uri()).get_inputs_template()

    def get_inputs_template(self) -> Dict:
        """
        Return get inputs from dict
        :return:
        """
        workflow_inputs = {}
        for field_key, field_dict in self.cwl_obj.type.get("fields").items():
            if isinstance(field_dict.get("type"), Dict):
                workflow_inputs.update(
                    {
                        field_key: self.get_input_from_dict_type(field_dict)
                    }
                )
            elif isinstance(field_dict.get("type"), List):
                workflow_inputs.update(
                    {
                        field_key: self.get_input_from_array_type(field_dict)
                    }
                )
            elif isinstance(field_dict.get("type"), str):
                workflow_inputs.update(
                    {
                        field_key: self.get_input_from_str_type(field_dict)
                    }
                )
            else:
                logger.warning(f"Don't know what to do with type {type(field_dict.get('type'))} for key {field_key}")
        return workflow_inputs

    @classmethod
    def load_schema_from_uri(cls, uri_input):
        file_path: Path = Path(urlparse(uri_input).path)

        yaml_handler = yaml.YAML()

        with open(file_path, "r") as schema_h:
            schema_obj = yaml_handler.load(schema_h)

        return cls(RecordSchema(schema_obj), file_path)


class ZippedCWLWorkflow:
    """
    Used for cwl files
    """

    def __init__(self, zipped_cwl_file_path: Path):
        """
        Initialise a zip workflow by
        * Extracting
        * Packing into a zipped json
        * Imported as a CWL object
        :param zipped_cwl_file_path:
        """
        self.zipped_cwl_file_path: Path = zipped_cwl_file_path

        # Check zipped cwl file path exists
        if not self.zipped_cwl_file_path.is_file():
            logger.error(f"Could not initialise ZippedCWLWorkflow class, "
                         f"input parameter zipped cwl file path value '{self.zipped_cwl_file_path}' did not exist")
            raise FileNotFoundError

        # Unzip
        self.unzipped_temp_dir: TemporaryDirectory = TemporaryDirectory()
        with ZipFile(self.zipped_cwl_file_path, 'r') as zip_ref:
            zip_ref.extractall(self.unzipped_temp_dir.name)

        workflow_file_list = list(
            filter(
                lambda filename: filename is not None,
                map(
                    lambda x: Path(self.unzipped_temp_dir.name) / Path(x.filename) if not x.filename.endswith("/") else None,
                    zip_ref.filelist
                )
            )
        )

        self.cwl_file_path = list(filter(lambda x: x.name == "workflow.cwl", workflow_file_list))[0]
        self.cwl_tool_files = list(filter(lambda x: x.name not in ["workflow.cwl", "params.xml"], workflow_file_list))

        self.cwl_obj: Optional[Workflow] = load_document_by_uri(self.cwl_file_path)
        self.cwl_inputs: Optional[List[WorkflowInputParameter]] = self.cwl_obj.inputs
        
        # Using cwltool --pack for now. See https://github.com/common-workflow-language/cwl-utils/issues/220
        # og_sys_stderr = sys.stderr
        # try:
        #    # https://www.codeforests.com/2020/11/05/python-suppress-stdout-and-stderr/
        #    devnull = open(os.devnull, "w")
        #    sys.stderr = devnull
        #    self.cwl_pack: Optional[Dict] = pack(str(self.cwl_file_path))
        # finally:
        #     sys.stderr = og_sys_stderr
        # self.cwl_pack: Optional[Dict] = pack(str(self.cwl_file_path))
        cwltool_pack_returncode, cwltool_pack_stdout, cwltool_pack_stderr = run_subprocess_proc(
            [
                "cwltool", "--pack", str(self.cwl_file_path)
            ],
            capture_output=True
        )

        if not cwltool_pack_returncode == 0:
            logger.error(f"Could not pack file {str(self.cwl_file_path)}")
            raise ChildProcessError

        self.cwl_pack = json.loads(cwltool_pack_stdout)

    def get_cwl_obj(self) -> Workflow:
        return self.cwl_obj

    def get_cwl_inputs_template_dict(self) -> Dict:
        return create_template_from_workflow_inputs(self.cwl_obj.inputs)

    def get_override_steps_dict(self) -> List:
        return get_workflow_overrides_steps_dict(
            workflow_steps=self.cwl_obj.steps,
            calling_relative_workflow_file_path=Path(shortname(self.cwl_obj.id)),
            calling_workflow_id=shortname(self.cwl_obj.id),
            original_relative_directory=self.cwl_file_path.parent
        )

    def get_md5sum_from_packed_dict(self) -> str:
        return hashlib.md5(json.dumps(self.cwl_pack, indent=4).encode()).hexdigest()

    # FIXME - this should be its own function outside of this class
    def create_icav2_workflow_from_zip(self, project_id: str, analysis_storage_id: str,
                                       workflow_description: str,
                                       params_xml_file: Path,
                                       html_documentation_path: Optional[Path],
                                       ) -> Tuple[str, str]:

        configuration = get_libicav2_configuration()

        workflow_code = self.zipped_cwl_file_path.stem.replace(".", "_")
        
        curl_command_list = [
            "curl",
            # "--fail", "--silent", "--location",
            "--request", "POST",
            "--header", "Accept: application/vnd.illumina.v3+json",
            "--header", f"Authorization: Bearer {configuration.access_token}",
            "--header", "Content-Type: multipart/form-data",
            "--url", f"{configuration.host}/api/projects/{project_id}/pipelines:createCwlPipeline",
            "--form", f"code={workflow_code}",
            "--form", f"description={workflow_description}",
            "--form", f"workflowCwlFile=@{self.cwl_file_path};filename=workflow.cwl",
            "--form", f"parametersXmlFile=@{params_xml_file};filename=params.xml;type=text/xml",
            "--form", f"analysisStorageId={analysis_storage_id}"
        ]

        if html_documentation_path is not None:
            curl_command_list.extend(
                [
                    "--form", f"htmlDocumentation=@{html_documentation_path};type=text/html"
                ]
            )

        for tool_file in self.cwl_tool_files:
            curl_command_list.extend([
                "--form",
                f"toolCwlFiles=@{tool_file};filename={tool_file.relative_to(Path(self.unzipped_temp_dir.name) / Path(self.zipped_cwl_file_path.stem))}"
            ])

        command_returncode, command_stdout, command_stderr = run_subprocess_proc(curl_command_list, capture_output=True)

        if not command_returncode == 0:
            logger.error(f"Got returncode {command_returncode} for creation of icav2 cli workflow")
            logger.error(f"Stdout was {command_stdout}, stderr was {command_stderr}")
            raise ValueError

        pipeline_id = json.loads(command_stdout).get("pipeline").get("id")

        return pipeline_id, workflow_code


def get_workflow_input_type(workflow_input: WorkflowInputParameter):
    if isinstance(workflow_input.type, str):
        return get_workflow_input_type_from_str_type(workflow_input)
    elif isinstance(workflow_input.type, InputEnumSchemaType):
        return get_workflow_input_type_from_enum_schema(workflow_input)
    elif isinstance(workflow_input.type, InputArraySchemaType):
        return get_workflow_input_type_from_array_schema(workflow_input)
    elif isinstance(workflow_input.type, InputRecordSchemaType):
        return get_workflow_input_type_from_record_schema(workflow_input)
    elif isinstance(workflow_input.type, List):
        return get_workflow_input_type_from_array_type(workflow_input)
    else:
        logger.warning(f"Don't know what to do here with {type(workflow_input.type)}")


def get_workflow_input_type_from_enum_schema(workflow_input: WorkflowInputParameter):
    """
    Workflow input type is a enum type
    :param workflow_input:
    :return:
    """
    workflow_type: InputEnumSchemaType = workflow_input.type
    return shortname(workflow_type.symbols[0])


def get_workflow_input_type_from_array_schema(workflow_input: WorkflowInputParameter):
    """
    Workflow input type is an array schema
    items attribute may be a file uri
    :param workflow_input:
    :return:
    """
    return [
        CWLSchema.load_schema_from_uri(workflow_input.type.items).get_inputs_template()
    ]


def get_workflow_input_type_from_record_schema(workflow_input: WorkflowInputParameter):
    raise NotImplementedError


def get_workflow_input_type_from_str_type(workflow_input: WorkflowInputParameter):
    """
    Workflow input type is a string type
    :param workflow_input:
    :return: A list with the following attributes
      {

      }
    """
    if workflow_input.type.startswith("file://"):
        # This is a schema!
        return CWLSchema.load_schema_from_uri(workflow_input.type).get_inputs_template()
    if workflow_input.type == "Directory":
        return {
            "class": "Directory",
            "location": "icav2://project_id/path/to/dir/"
        }
    elif workflow_input.type == "File":
        return {
            "class": "File",
            "location": "icav2://project_id/path/to/file"
        }
    elif workflow_input.type == "boolean":
        return workflow_input.default if workflow_input.default is not None else False
    elif workflow_input.type == "int":
        return workflow_input.default if workflow_input.default is not None else "string"
    elif workflow_input.type == "string":
        return workflow_input.default if workflow_input.default is not None else "string"
    else:
        logger.warning(f"Don't know what to do here with {workflow_input.type}")


def get_workflow_input_type_from_array_type(workflow_input: WorkflowInputParameter):
    """
    Workflow input is type list -
    likely that the first input is 'null'
    :param workflow_input:
    :return:
    """
    if not workflow_input.type[0] == "null":
        logger.error("Unsure what to do with input of type list where first element is not null")
        raise ValueError
    workflow_input_new = deepcopy(workflow_input)
    workflow_input_new.type = workflow_input.type[1]
    return get_workflow_input_type(workflow_input_new)


def create_template_from_workflow_inputs(workflow_inputs: List[WorkflowInputParameter]):
    """
    List inputs by template
    :param workflow_inputs:
    :param inputs:
    :return:
    """
    input_type_dict = {}

    for workflow_input in workflow_inputs:
        input_type_dict.update(
            {
                shortname(workflow_input.id): get_workflow_input_type(workflow_input)
            }
        )

    return input_type_dict


def get_workflow_overrides_steps_dict(workflow_steps: List[WorkflowStep],
                                      calling_relative_workflow_file_path: Path,
                                      calling_workflow_id: str,
                                      original_relative_directory: Path) -> List:

    """
    Get a list of steps that can be overridden
    :param workflow_steps:
    :param calling_relative_workflow_file_path:
    :param calling_workflow_id:
    :param original_relative_directory:
    :return:
    """

    from os.path import relpath

    override_steps = []

    for workflow_step in workflow_steps:
        # Get the run path
        run_path = original_relative_directory.joinpath(
            relpath(urlparse(workflow_step.run).path, original_relative_directory)
        ).resolve()

        # Get the short name
        step_name = shortname(workflow_step.id)

        # Get the full name to call
        step_id = f"{calling_relative_workflow_file_path}#{calling_workflow_id}/{step_name}"

        # Load step
        run_cwl_obj = load_document_by_uri(run_path)

        # Just create the step ID
        if isinstance(run_cwl_obj, CommandLineTool):
            override_steps.append(
                step_id
            )

        if isinstance(run_cwl_obj, Workflow):
            override_steps.extend(
                get_workflow_overrides_steps_dict(
                    workflow_steps=run_cwl_obj.steps,
                    calling_relative_workflow_file_path=Path(relpath(run_path, original_relative_directory)),
                    calling_workflow_id=shortname(run_cwl_obj.id),
                    original_relative_directory=original_relative_directory
                )
            )

    return override_steps


def generate_plot_png(
        packed_json: Dict,
        ratio_value: float
) -> Path:

    # Initialise temp files
    packed_file_temp = Path(NamedTemporaryFile(delete=False, suffix=".json").name)
    dot_file_temp = Path(NamedTemporaryFile(delete=False, suffix=".dot").name)
    plot_png_file = Path(NamedTemporaryFile(delete=False, suffix=".png").name)

    # Dump packed file
    with open(packed_file_temp, "w") as packed_file_temp_h:
        packed_file_temp_h.write(json.dumps(packed_json))

    # Build dot file
    build_dot_command_list = [
        sys.executable,
        "-m",
        "cwltool", "--print-dot", str(packed_file_temp)
    ]
    with open(str(dot_file_temp), 'w') as write_h:
        build_dot_returncode, _, build_dot_stderr = run_subprocess_proc(
            build_dot_command_list,
            stdout=write_h, stderr=subprocess.PIPE
        )

    if not build_dot_returncode == 0:
        logger.error(f"Could not build dot file, got returncode {build_dot_returncode}")
        logger.error(f"Stderr was {build_dot_stderr}")
        raise ChildProcessError

    # Build png file
    dot_command = [
        "dot",
        f"-Gratio={ratio_value}",
        "-Tpng",
        f"-o{plot_png_file}",
        f"{dot_file_temp}"
    ]

    dot_returncode, dot_stdout, dot_stderr = run_subprocess_proc(
        dot_command,
        capture_output=True
    )

    if not dot_returncode == 0:
        logger.error("Could not build the png file command")
        raise ChildProcessError

    return plot_png_file.absolute().resolve()


def generate_standalone_html_through_pandoc(markdown_file_path: Path) -> Path:
    """
    Generate a standalone html through pandoc from the markdown file
    :param markdown_file_path:
    :return:
    """

    output_html_file = Path(NamedTemporaryFile(delete=False, suffix=".html").name)

    pandoc_command_list = [
        "pandoc",
        "--embed-resources",
        "--standalone",
        "--from",
        "markdown",
        "--to",
        "html",
        "--output",
        str(output_html_file),
        str(markdown_file_path)
    ]

    pandoc_returncode, pandoc_stderr, pandoc_stdout = run_subprocess_proc(
        pandoc_command_list,
        capture_output=True
    )

    if not pandoc_returncode == 0:
        logger.error("Unsuccessful conversion of markdown file to html")
        raise ValueError

    return output_html_file.absolute().resolve()


def generate_markdown_doc(
        title: str,
        description: str,
        label: str,
        cwl_inputs: List[WorkflowInputParameter],
        cwl_steps: List[WorkflowStep],
        cwl_outputs: List[WorkflowOutputParameter],
        workflow_image_page_path: Path,
        workflow_md5sum: str,
        input_json_template: Optional[Dict] = None,
        overrides_template: Optional[List] = None,
) -> Path:
    """
    Generate a markdown document (that we will then convert to html)
    :param overrides_template:
    :param input_json_template:
    :param workflow_md5sum:
    :param workflow_image_page_path:
    :param cwl_outputs:
    :param cwl_steps:
    :param cwl_inputs:
    :param label:
    :param title:
    :param description:
    :param inputs:
    :param steps:
    :param outputs:
    :return:
    """

    mdoutput_file = Path(NamedTemporaryFile(delete=False, suffix=".md").name)

    md_file_obj: MdUtils = MdUtils(
        file_name=str(mdoutput_file),
        title=title
    )

    # Header
    md_file_obj.new_header(level=2, title=f"{label} Overview", add_table_of_contents="n")
    md_file_obj.new_line("\n")

    # Add MD5Sum
    md_file_obj.new_line(f"> md5sum: {workflow_md5sum}")
    md_file_obj.new_line("\n")

    # Add Documentation
    md_file_obj.new_header(level=3, title=f"{label} documentation", add_table_of_contents="n")
    md_file_obj.new_line(f"{description}", wrap_width=0)
    md_file_obj.new_line("\n")

    # Get visuals
    md_file_obj.new_header(level=2, title="Visual Workflow Overview", add_table_of_contents="n")
    md_file_obj.new_line(
        md_file_obj.new_inline_image(
                path=str(workflow_image_page_path.absolute()),
                text=workflow_image_page_path.name
        ),
        wrap_width=0
    )
    md_file_obj.new_line("\n")

    # TODO - add plots of subfunctions too

    # Get inputs
    md_file_obj.new_header(level=2, title=f"{label} Inputs", add_table_of_contents="n")

    for input_obj in cwl_inputs:
        # TODO render type
        md_file_obj.new_header(level=3, title=input_obj.label, add_table_of_contents='n')

        # Add new paragraph
        md_file_obj.new_paragraph("\n")
        md_file_obj.new_line(f"> ID: {shortname(input_obj.id)}\n")
        md_file_obj.new_line(f"**Docs:**")
        md_file_obj.new_line(f"{input_obj.doc}\n", wrap_width=0)

    md_file_obj.new_line("\n")

    # Get steps
    md_file_obj.new_header(level=2, title=f"{label} Steps", add_table_of_contents="n")

    for step_obj in cwl_steps:
        md_file_obj.new_header(level=3, title=step_obj.label, add_table_of_contents='n')

        # Add new paragraph
        md_file_obj.new_paragraph("\n")
        md_file_obj.new_line(f"> ID: {shortname(step_obj.id)}\n")
        md_file_obj.new_line(f"**Docs:**")
        md_file_obj.new_line(f"{step_obj.doc}\n", wrap_width=0)

    md_file_obj.new_line("\n")

    # Get outputs
    for output_obj in cwl_outputs:
        # TODO render type
        md_file_obj.new_header(level=3, title=output_obj.label, add_table_of_contents='n')

        # Add new paragraph
        md_file_obj.new_paragraph("\n")
        md_file_obj.new_line(f"> ID: {shortname(output_obj.id)}\n")
        md_file_obj.new_line(f"**Docs:**")
        md_file_obj.new_line(f"{output_obj.doc}\n", wrap_width=0)

    md_file_obj.new_line("\n")


    # Add json template
    md_file_obj.new_header(level=2, title=f"{label} InputsJson Template", add_table_of_contents="n")

    # Insert code
    md_file_obj.insert_code(
        code=json.dumps(input_json_template, indent=4),
        language="json"
    )
    md_file_obj.new_line("\n")


    # Add overrides template
    md_file_obj.new_header(level=2, title=f"{label} Overrides Template", add_table_of_contents="n")

    # Insert code
    md_file_obj.insert_code(
        code=json.dumps(overrides_template, indent=4),
        language="json"
    )

    md_file_obj.new_line("\n")

    # Create the output markdown file
    md_file_obj.create_md_file()

    # Update title
    run_subprocess_proc(
        [
            "sed",
            "-i",
            "-e", "1c---",
            "-e", "2s/^/title: /",
            "-e", "3c---",
            str(mdoutput_file)
        ]
    )

    return mdoutput_file.absolute().resolve()
