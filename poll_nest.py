#!/usr/bin/python

import requests
import configparser
import schedule
import time
from errors import error_result
from errors import APIError


conf = configparser.ConfigParser()
conf.read("config")

auth_t = conf.get('configuration', 'auth_token')
nest_api_url = conf.get('configuration', 'nest_api')


local_cams_object = {
        # 'name' : name_object
        }

# Our event data object
def get_camera_dict(name, camera_id):
    # type: (object, object) -> object
    return {
        'routing_key': 'R0157YB9LD9RLMHIGSHE753210DFAAU9',
        'event_action': 'trigger',
        'payload': {
            'summary': '',
            'severity': '',
            'source': name,
            'component': 'Camera',
            'timestamp': ''
        },
        'cam_id': camera_id,
        'base_url' : nest_api_url,
        'url' : '',
        'last_event_time' : '',
        'web_url' : ''
    }


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
    cameras_json = get_nest_data()

    for key, value in cameras_json.items():  # type: (object, object)

        # populate our local cameras datastructure
        name = cameras_json[key]['device_id']
        local_cams_object[name] = get_camera_dict(cameras_json[key]['name'], cameras_json[key]['device_id'])


init_cam_structures()

def poll_cameras():
    # type: (object) -> object

    for key, value in local_cams_object.items():
        # print key, value
        local_cams_object[key]['url'] = local_cams_object[key]['base_url'] + local_cams_object[key]['cam_id'] + '/'
        # print key, value
        response = get_nest_data()

        # If Nest Cloud is not responding
        # HTTPSConnectionPool(host='developer-api.nest.com', port=443): Max retries exceeded with url: /devices/cameras/f3lekKgaeNvSnmjlvY9kwpIeqdEWjvst8opkq0o-ecTH_fxyUXJyZQ/ (Caused by NewConnectionError('<urllib3.connection.VerifiedHTTPSConnection object at 0x10cdb6e50>: Failed to establish a new connection: [Errno 8] nodename nor servname provided, or not known',))
        # No response from

        if response is None:
            print ("No response from ")
            print (cameras[key])
            break

        # DEBUG print (response)
        local_cams_object[key]["payload"]["severity"] = 'critical'
        local_cams_object[key]["payload"]["timestamp"] = response[key]["last_event"]["start_time"]
        local_cams_object[key]["payload"]["source"] = response[key]["name_long"]
        local_cams_object[key]["web_url"] = response[key]["last_event"]["web_url"]

        if response[key]["last_event"]["has_person"]:
            local_cams_object[key]["payload"]["summary"] = "API: " + local_cams_object[key]["payload"]["source"] + ' spotted a person'

        elif response[key]["last_event"]["has_motion"]:
            local_cams_object[key]["payload"]["summary"] = "API: " + local_cams_object[key]["payload"]["source"] + ' spotted movement'

        elif response[key]["last_event"]["has_sound"]:
            local_cams_object[key]["payload"]["summary"] = "API: " + local_cams_object[key]["payload"]["source"] + ' heard a loud noise'

        # sanitize
        data = dict(local_cams_object[key])

        # Sanitize before sending to PD
        del data['url']
        del data['base_url']
        del data['cam_id']

        oldtime = local_cams_object[key]["last_event_time"]
        newtime = response[key]["last_event"]["start_time"]

        print (local_cams_object[key]["payload"]["source"])
        print ("testing newtime == oldtime")
        print ("oldtime : " + oldtime + "  " + "newtime : " + newtime)

        # Skip on start up
        if oldtime:
            if newtime == oldtime:
                print ("last event time matched -- skipping")
            else:
                try:
                    #### SEND AN EVENT TO PAGERDUTY #####
                    # create a version 2 event
                    alert = pypd.EventV2.create(data)

                    # alert return {u'status': u'success', u'message': u'Event processed', u'dedup_key': u'15bf1c5df8fe4ec3bb06cffd4c317cac'}

                    print
                    print ("last event time NOT matched -- sending PD Alert")
                    print (local_cams_object[key]["payload"]["summary"])
                    print

                except Exception as bad:
                    print(bad)
        local_cams_object[key]["last_event_time"] = newtime

# Run every two minutes
schedule.every(2).minutes.do(poll_cameras)

while True:
    schedule.run_pending()
    time.sleep(1)

