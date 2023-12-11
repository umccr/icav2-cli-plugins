#!/usr/bin/env python

"""
East datetime handlers
"""

from datetime import datetime, timedelta


def file_friendly_datetime_format(date: datetime) -> str:
    return date.strftime('%Y-%m-%d-%H%M%S')


def calculate_presigned_url_expiry(current_time: datetime) -> datetime:
    return current_time + timedelta(weeks=1)

