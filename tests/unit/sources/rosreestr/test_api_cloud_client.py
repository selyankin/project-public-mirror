"""Проверка ApiCloudRosreestrClient."""

import pytest

from sources.rosreestr.api_cloud_client import ApiCloudRosreestrClient
from sources.rosreestr.exceptions import RosreestrClientError


def test_api_cloud_client_requires_token():
    with pytest.raises(RosreestrClientError):
        ApiCloudRosreestrClient(token=None)
