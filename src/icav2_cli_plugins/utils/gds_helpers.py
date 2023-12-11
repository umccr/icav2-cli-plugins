#!/usr/bin/env python3

"""
A few ICAv1 helpers.  We support GDS files through a presigned url.

We can also support gds folders.


"""


def convert_gds_uri_to_download_url(uri: str) -> str:
    """
    Convert a gds uri to download url
    :param uri:
    :return:
    """
