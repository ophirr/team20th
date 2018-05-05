import requests
import pypd
import json
import schedule
import time
from errors import error_result
from errors import APIError

pypd.api_key = "Yu_k-X72qyc9JC2jcjgv"
podid = 'ku4dI5BIfYG08IVUrow8bd2YLxcmWff30XJzMWXmEtvH_fxyUXJyZQ'
tade20id = 'f3lekKgaeNvSnmjlvY9kwpIeqdEWjvst8opkq0o-ecTH_fxyUXJyZQ'
tade19id = 'mG-v4NVvs2fQAJb62IyvXT4dNwPVnOB6RnnEaebhtinH_fxyUXJyZQ'

def get_camera_dict(name, camera_id):
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


tades20 = get_camera_dict('tades20', tade20id)
tades19 = get_camera_dict('tades19', tade19id)
pod = get_camera_dict('pod', podid)


# Camera DataStructure
cameras = {
        'tades20' : tades20,
        'tades19' : tades19,
        'pod'   : pod
        }

# Retry on error
class NetworkError(RuntimeError):
    pass





#### GET NEST DATA FROM CAMERAS #####

def get_nest_data(camera_url):

    url = camera_url
    auth_t = "c.HmcoZSptsITREqWw5DiTUp6WFLMl9QN5WJPl0QiSE7djr1tPOYIWpGvnXsbi41Y1GR8uSZGra3diecATig7gUw6iUU4HaXRRru6OuD0XQTlD7HXZqWk6NXyXKmwdLSsp3vCu1YxUCS06N0ru"
    headers = {
        'authorization': "Bearer " + auth_t,
        'content-type': "application/json",
    }

    # SOMETIMES WE DON'T GET DATA AND NEED TO TRY AGAIN OTHERWISE WE FAIL
    #  File "/Users/ophir/src/team20th/team20-alerts.py", line 75, in poll_cameras
    #     cameras[key]["payload"]["timestamp"] = response["last_event"]["start_time"]
    # TypeError: 'NoneType' object has no attribute '__getitem__'

    try:
        init_res = requests.get(url, headers=headers, allow_redirects=False)

        if init_res.status_code == 429:
                return "Blocked - too many requests"
        elif init_res.status_code == 307:
            api_response = requests.get(init_res.headers['Location'], headers=headers, allow_redirects=False)
            if  api_response.status_code == 200:
                return api_response.json()
        elif init_res.status_code == 200:
            return init_res.json()
    except Exception as ce:
        print(ce)


def poll_cameras():
    print
    for key, value in cameras.items():
        #print key, value
        cameras[key]['url'] = cameras[key]['base_url'] + cameras[key]['cam_id'] + '/'
        #print key, value
        response = get_nest_data(cameras[key]['url'])

        # If Nest Cloud is not responding
        # HTTPSConnectionPool(host='developer-api.nest.com', port=443): Max retries exceeded with url: /devices/cameras/f3lekKgaeNvSnmjlvY9kwpIeqdEWjvst8opkq0o-ecTH_fxyUXJyZQ/ (Caused by NewConnectionError('<urllib3.connection.VerifiedHTTPSConnection object at 0x10cdb6e50>: Failed to establish a new connection: [Errno 8] nodename nor servname provided, or not known',))
        # No response from

        if response is None:
            print ("No response from ")
            print (cameras[key])
            break

        print (response)
        cameras[key]["payload"]["severity"] = 'critical'
        cameras[key]["payload"]["timestamp"] = response["last_event"]["start_time"]
        cameras[key]["payload"]["source"] = response["name_long"]
        cameras[key]["web_url"] = response["last_event"]["web_url"]

        if response["last_event"]["has_person"]:
            cameras[key]["payload"]["summary"] = "API: " + cameras[key]["payload"]["source"] + ' spotted a person'

        elif response["last_event"]["has_motion"]:
            cameras[key]["payload"]["summary"] = "API: " + cameras[key]["payload"]["source"] + ' spotted movement'

        elif response["last_event"]["has_sound"]:
            cameras[key]["payload"]["summary"] = "API: " + cameras[key]["payload"]["source"] + ' heard a loud noise'

        # sanitize
        data = dict(cameras[key])

        # Sanitize before sending to PD
        del data['url']
        del data['base_url']
        del data['cam_id']


        oldtime = cameras[key]["last_event_time"]
        newtime = response["last_event"]["start_time"]

        print (cameras[key]["payload"]["source"])
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
                    print (cameras[key]["payload"]["summary"])
                    print

                except Exception as bad:
                    print(bad)
        cameras[key]["last_event_time"] = newtime

schedule.every(2).minutes.do(poll_cameras)

while True:
    schedule.run_pending()
    time.sleep(1)

#response = get_nest_data()

# print(response)


#


# data = {
#             'routing_key': 'R0157YB9LD9RLMHIGSHE753210DFAAU9',
#             'event_action': 'trigger',
#             'payload': {
#                 'summary': 'This is Nest camera alert!',
#                 'severity': 'error',
#                 'source': response["name_long"],
#                 'component': 'Camera',
#                 'timestamp': response["last_event"]["start_time"]
#             },
#             "images": [{
#                 "src": response["last_event"]["animated_image_url"],
#                 "href": "https://nest.com/",
#                 "alt": "event capture"
#             }],
#             'links': [{
#                 "href": response["last_event"]["web_url"],
#                 "text": "Click to see the event video"
#             }],
#             "client": "Team20th Neighborhood Watch"
#         }
