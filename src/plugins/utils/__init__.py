import re
from typing import Dict, Any
from uuid import UUID

version = "2.10.0"


# Miscellaneous functions that don't go anywhere
def camel_to_snake_case(camel_case: str) -> str:
    return re.sub(r'(?<!^)(?=[A-Z])', '_', camel_case).lower()


def sanitise_dict_keys(input_dict: Dict) -> Dict:
    output_dict = {}
    key: str
    value: Any
    for key, value in input_dict.items():
        output_dict[camel_to_snake_case(key)] = value
    return output_dict


def is_uuid_format(project_id: str) -> bool:
    try:
        _ = UUID(project_id, version=4)
        return True
    except ValueError:
        return False
