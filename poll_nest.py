#!/usr/bin/python

import requests
import configparser
from errors import error_result
from errors import APIError


# Our event data object
def get_camera_dict(source, camera_id):
    return {
        'routing_key': 'R0157YB9LD9RLMHIGSHE753210DFAAU9',
        'event_action': 'trigger',
        'payload': {
            'summary': '',
            'severity': '',
            'source': source,
            'component': 'Camera',
            'timestamp': ''
        },
        'cam_id': camera_id,
        'base_url' : 'https://developer-api.nest.com/devices/cameras/',
        'url' : '',
        'last_event_time' : '',
        'web_url' : ''
    }

conf = configparser.ConfigParser()
conf.read("config")

auth_t = conf.get('configuration', 'auth_token')
nest_api_url = conf.get('configuration', 'nest_api')


#### GET NEST DATA FROM CAMERAS #####

def get_nest_data():
    # type: () -> object

    headers = {
        'authorization': "Bearer " + auth_t,
        'content-type': "application/json",
    }

    # SOMETIMES WE DON'T GET DATA AND NEED TO TRY AGAIN OTHERWISE WE FAIL
    #  File "/Users/ophir/src/team20th/team20-alerts.py", line 75, in poll_cameras
    #     cameras[key]["payload"]["timestamp"] = response["last_event"]["start_time"]
    # TypeError: 'NoneType' object has no attribute '__getitem__'

    try:
        init_res = requests.get(nest_api_url, headers=headers, allow_redirects=False)

        if init_res.status_code == 429:
                return "Blocked - too many requests"
        elif init_res.status_code == 402:
                return "Unauthorized - bad token?"
        elif init_res.status_code == 307:
            api_response = requests.get(init_res.headers['Location'], headers=headers, allow_redirects=False)
            if  api_response.status_code == 200:
                return api_response.json()
        elif init_res.status_code == 200:
            return init_res.json()
    except Exception as ce:
        print(ce)


# Initialize
def init_cam_structures():
    cameras = get_nest_data()
    for key, value in cameras.items():  # type: (object, object)
        print (key, value)

init_cam_structures()

def poll_cameras():
    # type: (object) -> object

    data = get_nest_data()

    camera_id = cameras.keys()[0]
    camera = cameras[camera_id]

    number_cams = len(cameras.keys())

    print ("Found", number_cams, "cameras")

    i = 0
    while i < number_cams:
        camera_id = cameras.keys()[i]
        camera = cameras[camera_id]
        print("Found", camera["name"])
        i += 1

        # Verify the Nest Cam has a Snapshot URL field
        if 'snapshot_url' not in camera:
            raise APIError(error_result("Camera has no snapshot URL"))

        snapshot_url = camera["snapshot_url"]
        print ("Snapshot url : ", snapshot_url)

    return snapshot_url


#fetch_snapshot_url(auth_t)

poll_cameras()
