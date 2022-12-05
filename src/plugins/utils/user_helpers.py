#!/usr/bin/env python3

"""
Libicav2 user handlers

get_user_name_from_user_id
"""

from utils.config_helpers import get_libicav2_configuration

from libica.openapi.v2 import ApiClient, ApiException
from libica.openapi.v2.api.user_api import UserApi
from libica.openapi.v2.model.user import User


def get_user_from_user_id(user_id: str) -> User:
    """
    Call the user endpoint
    :param user_id:
    :return:
    """
    with ApiClient(get_libicav2_configuration()) as api_client:
        # Create an instance of the API class
        api_instance = UserApi(api_client)
    user_id = "userId_example"  # str |

    # Get the user
    try:
        # Retrieve a user.
        api_response: User = api_instance.get_user(user_id)
    except ApiException as e:
        raise ValueError("Exception when calling UserApi->get_user: %s\n" % e)

    return api_response

