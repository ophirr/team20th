#!/usr/bin/python
#
# Copyright 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import urllib2
import json
from errors import error_result
from errors import APIError

nest_api_url = 'https://developer-api.nest.com'

def fetch_snapshot_url(token):
    headers = {
        'Authorization': "Bearer {0}".format(token),
    }
    req = urllib2.Request(nest_api_url, None, headers)
    response = urllib2.urlopen(req)
    data = json.loads(response.read())

  # Verify the account has devices
    if 'devices' not in data:
        raise APIError(error_result("Nest account has no devices"))
    devices = data["devices"]

    # Verify the account has cameras
    if 'cameras' not in devices:
        raise APIError(error_result("Nest account has no cameras"))
    cameras = devices["cameras"]

    # Verify the account has 1 Nest Cam
    if len(cameras.keys()) < 1:
        raise APIError(error_result("Nest account has no cameras"))

    camera_id = cameras.keys()[0]
    camera = cameras[camera_id]

    # Verify the Nest Cam has a Snapshot URL field
    if 'snapshot_url' not in camera:
        raise APIError(error_result("Camera has no snapshot URL"))
    snapshot_url = camera["snapshot_url"]

    return snapshot_url
