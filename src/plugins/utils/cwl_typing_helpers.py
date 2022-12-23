#!/usr/bin/env python

"""
Suite of unions for type helping
"""

from typing import Union

from cwl_utils.parser.cwl_v1_0 import \
    RecordSchema as RecordSchema_v1_0, \
    InputEnumSchema as InputEnumSchema_v1_0, \
    InputArraySchema as InputArraySchema_v1_0, \
    InputRecordSchema as InputRecordSchema_v1_0, \
    ArraySchema as ArraySchema_v1_0, \
    EnumSchema as EnumSchema_v1_0


from cwl_utils.parser.cwl_v1_0 import \
    ProcessRequirement as ProcessRequirement_v1_0, \
    InlineJavascriptRequirement as InlineJavascriptRequirement_v1_0, \
    SchemaDefRequirement as SchemaDefRequirement_v1_0, \
    DockerRequirement as DockerRequirement_v1_0, \
    SoftwareRequirement as SoftwareRequirement_v1_0, \
    InitialWorkDirRequirement as InitialWorkDirRequirement_v1_0, \
    EnvVarRequirement as EnvVarRequirement_v1_0, \
    ShellCommandRequirement as ShellCommandRequirement_v1_0, \
    ResourceRequirement as ResourceRequirement_v1_0, \
    SubworkflowFeatureRequirement as SubworkflowFeatureRequirement_v1_0, \
    ScatterFeatureRequirement as ScatterFeatureRequirement_v1_0, \
    MultipleInputFeatureRequirement as MultipleInputFeatureRequirement_v1_0, \
    StepInputExpressionRequirement as StepInputExpressionRequirement_v1_0


from cwl_utils.parser.cwl_v1_1 import \
    RecordSchema as RecordSchema_v1_1, \
    InputEnumSchema as InputEnumSchema_v1_1, \
    InputArraySchema as InputArraySchema_v1_1, \
    InputRecordSchema as InputRecordSchema_v1_1, \
    ArraySchema as ArraySchema_v1_1, \
    EnumSchema as EnumSchema_v1_1

from cwl_utils.parser.cwl_v1_1 import \
    WorkflowInputParameter as WorkflowInputParameter_v1_1

from cwl_utils.parser.cwl_v1_1 import \
    ProcessRequirement as ProcessRequirement_v1_1, \
    InlineJavascriptRequirement as InlineJavascriptRequirement_v1_1, \
    SchemaDefRequirement as SchemaDefRequirement_v1_1, \
    DockerRequirement as DockerRequirement_v1_1, \
    SoftwareRequirement as SoftwareRequirement_v1_1, \
    InitialWorkDirRequirement as InitialWorkDirRequirement_v1_1, \
    EnvVarRequirement as EnvVarRequirement_v1_1, \
    ShellCommandRequirement as ShellCommandRequirement_v1_1, \
    ResourceRequirement as ResourceRequirement_v1_1, \
    SubworkflowFeatureRequirement as SubworkflowFeatureRequirement_v1_1, \
    ScatterFeatureRequirement as ScatterFeatureRequirement_v1_1, \
    MultipleInputFeatureRequirement as MultipleInputFeatureRequirement_v1_1, \
    StepInputExpressionRequirement as StepInputExpressionRequirement_v1_1

from cwl_utils.parser.cwl_v1_2 import \
    RecordSchema as RecordSchema_v1_2, \
    InputEnumSchema as InputEnumSchema_v1_2, \
    InputArraySchema as InputArraySchema_v1_2, \
    InputRecordSchema as InputRecordSchema_v1_2, \
    ArraySchema as ArraySchema_v1_2, \
    EnumSchema as EnumSchema_v1_2

from cwl_utils.parser.cwl_v1_2 import \
    WorkflowInputParameter as WorkflowInputParameter_v1_2

from cwl_utils.parser.cwl_v1_2 import \
    ProcessRequirement as ProcessRequirement_v1_2, \
    InlineJavascriptRequirement as InlineJavascriptRequirement_v1_2, \
    SchemaDefRequirement as SchemaDefRequirement_v1_2, \
    DockerRequirement as DockerRequirement_v1_2, \
    SoftwareRequirement as SoftwareRequirement_v1_2, \
    InitialWorkDirRequirement as InitialWorkDirRequirement_v1_2, \
    EnvVarRequirement as EnvVarRequirement_v1_2, \
    ShellCommandRequirement as ShellCommandRequirement_v1_2, \
    ResourceRequirement as ResourceRequirement_v1_2, \
    SubworkflowFeatureRequirement as SubworkflowFeatureRequirement_v1_2, \
    ScatterFeatureRequirement as ScatterFeatureRequirement_v1_2, \
    MultipleInputFeatureRequirement as MultipleInputFeatureRequirement_v1_2, \
    StepInputExpressionRequirement as StepInputExpressionRequirement_v1_2

RecordSchemaType = Union[
    RecordSchema_v1_0,
    RecordSchema_v1_1,
    RecordSchema_v1_2
]

InputEnumSchemaType = Union[
    InputEnumSchema_v1_0,
    InputEnumSchema_v1_1,
    InputEnumSchema_v1_2
]

InputArraySchemaType = Union[
    InputArraySchema_v1_0,
    InputArraySchema_v1_1,
    InputArraySchema_v1_2
]

InputRecordSchemaType = Union[
    InputRecordSchema_v1_0,
    InputRecordSchema_v1_1,
    InputRecordSchema_v1_2
]

ArraySchemaType = Union[
    ArraySchema_v1_0,
    ArraySchema_v1_1,
    ArraySchema_v1_2
]

EnumSchemaType = Union[
    EnumSchema_v1_0,
    EnumSchema_v1_1,
    EnumSchema_v1_2
]


ProcessRequirementType = Union[
    ProcessRequirement_v1_0,
    ProcessRequirement_v1_1,
    ProcessRequirement_v1_2
]

InlineJavascriptRequirementType = Union[
    InlineJavascriptRequirement_v1_0,
    InlineJavascriptRequirement_v1_1,
    InlineJavascriptRequirement_v1_2
]

SchemaDefRequirementType = Union[
    SchemaDefRequirement_v1_0,
    SchemaDefRequirement_v1_1,
    SchemaDefRequirement_v1_2
]

DockerRequirementType = Union[
   DockerRequirement_v1_0,
   DockerRequirement_v1_1,
   DockerRequirement_v1_2
]

SoftwareRequirementType = Union[
    SoftwareRequirement_v1_0,
    SoftwareRequirement_v1_1,
    SoftwareRequirement_v1_2
]

InitialWorkDirRequirementType = Union[
    InitialWorkDirRequirement_v1_0,
    InitialWorkDirRequirement_v1_1,
    InitialWorkDirRequirement_v1_2
]

EnvVarRequirementType = Union[
   EnvVarRequirement_v1_0,
   EnvVarRequirement_v1_1,
   EnvVarRequirement_v1_2
]

ShellCommandRequirementType = Union[
    ShellCommandRequirement_v1_0,
    ShellCommandRequirement_v1_1,
    ShellCommandRequirement_v1_2
]

ResourceRequirementType = Union[
    ResourceRequirement_v1_0,
    ResourceRequirement_v1_1,
    ResourceRequirement_v1_2
]

SubworkflowFeatureRequirementType = Union[
    SubworkflowFeatureRequirement_v1_0,
    SubworkflowFeatureRequirement_v1_1,
    SubworkflowFeatureRequirement_v1_2
]

ScatterFeatureRequirementType = Union[
    ScatterFeatureRequirement_v1_0,
    ScatterFeatureRequirement_v1_1,
    ScatterFeatureRequirement_v1_2
]

MultipleInputFeatureRequirementType = Union[
    MultipleInputFeatureRequirement_v1_0,
    MultipleInputFeatureRequirement_v1_1,
    MultipleInputFeatureRequirement_v1_2
]

StepInputExpressionRequirementType = Union[
    StepInputExpressionRequirement_v1_0,
    StepInputExpressionRequirement_v1_1,
    StepInputExpressionRequirement_v1_2
]

WorkflowInputParameter = Union[
    WorkflowInputParameter_v1_1,
    WorkflowInputParameter_v1_2
]
