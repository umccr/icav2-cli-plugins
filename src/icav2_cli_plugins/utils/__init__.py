import re
from typing import Dict, Any
import sys
from urllib.parse import urlparse
from uuid import UUID
from ast import literal_eval


version = "2.10.0"


# Miscellaneous functions that don't go anywhere
def camel_to_snake_case(camel_case: str) -> str:
    return re.sub(r'(?<!^)(?=[A-Z])', '_', camel_case).lower()


def snake_to_camel_case(snake_case: str) -> str:
    return ''.join(word.title() for word in snake_case.split('_'))


def to_lower_camel_case(snake_str):
    # We capitalize the first letter of each component except the first one
    # with the 'capitalize' method and join them together.
    camel_string = snake_to_camel_case(snake_str)
    return snake_str[0].lower() + camel_string[1:]


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


def is_uri_format(uri_str: str) -> bool:
    """
    Determine if the string is a valid URI
    :param uri_str:
    :return:
    """
    try:
        url_obj = urlparse(uri_str)
        if url_obj.scheme and url_obj.netloc:
            return True
        else:
            return False
    except ValueError:
        return False


def is_interactive() -> bool:
    return sys.stdin.isatty()


def strip_literal(input_str: str) -> str:
    try:
        return str(literal_eval(input_str))
    except (ValueError, SyntaxError):
        return input_str


def to_jsonable_dict(model: Any) -> Any:
    """
    Convert a libica / pydantic v2 model into a JSON-serialisable structure.

    The libica models' own ``to_json`` / ``to_dict`` methods call
    ``model_dump(by_alias=True)`` which leaves UUID and datetime values as native
    Python objects, so a subsequent ``json.dumps`` raises
    ``TypeError: Object of type UUID is not JSON serializable``.

    Using ``model_dump(mode="json", ...)`` lets pydantic coerce those values
    (UUID, datetime, etc.) into strings first, matching the behaviour of
    fastapi's ``jsonable_encoder`` without adding a dependency on fastapi.

    :param model: A pydantic v2 model instance (or any object; non-models are
                  returned unchanged).
    :return: A JSON-serialisable dict (or the original object if it is not a model)
    """
    if hasattr(model, "model_dump"):
        return model.model_dump(mode="json", by_alias=True, exclude_none=True)
    return model
