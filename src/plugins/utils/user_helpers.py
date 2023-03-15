#!/usr/bin/env python3

"""
Libicav2 user handlers

get_user_name_from_user_id
"""
from libica.openapi.v2.model.user_list import UserList

from utils.config_helpers import get_libicav2_configuration

from libica.openapi.v2 import ApiClient, ApiException
from libica.openapi.v2.api.user_api import UserApi
from libica.openapi.v2.model.user import User

from utils.logger import get_logger

logger = get_logger()


def get_user_from_user_name(user_name: str) -> User:
    """
    Call the user endpoint
    :param user_name:
    :return:
    """
    with ApiClient(get_libicav2_configuration()) as api_client:
        # Create an instance of the API class
        api_instance = UserApi(api_client)

    # Get the user
    try:
        # Retrieve a user.
        api_response: UserList = api_instance.get_users()
    except ApiException as e:
        raise ValueError("Exception when calling UserApi->get_user: %s\n" % e)

    try:
        return next(
            filter(
                lambda x: x.firstname + " " + x.lastname == user_name,
                api_response.items
            )
        )
    except StopIteration:
        logger.error(f"Could not find user name '{user_name}'")
        raise ValueError


def get_user_from_user_id(user_id: str) -> User:
    """
    Call the user endpoint
    :param user_id:
    :return:
    """
    with ApiClient(get_libicav2_configuration()) as api_client:
        # Create an instance of the API class
        api_instance = UserApi(api_client)

    # Get the user
    try:
        # Retrieve a user.
        api_response: User = api_instance.get_user(user_id)
    except ApiException as e:
        raise ValueError("Exception when calling UserApi->get_user: %s\n" % e)

    return api_response

