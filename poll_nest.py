from __future__ import print_function
import requests
import urllib3
import configparser
import sseclient
import pypd
import json

from string import Template
from errors import error_result
from errors import APIError

#### GET CONFIGURATION FROM CONFIG.TXT

conf = configparser.ConfigParser()
conf.read("config.txt")

auth_t = conf.get('configuration', 'auth_token')
nest_api_url = conf.get('configuration', 'nest_api')
routing_key = conf.get('configuration', 'routing_key')


local_cams_object = {
        # 'name' : name_object
        }


#### OUR FUNCTIONS #####

# Our event data object
def get_camera_dict(name, camera_id, routing_key):
    # type: (object, object) -> object
    return {
        'routing_key': routing_key,
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
            raise APIError(error_result("Received 429 - Throttled - Polling to fast?"))
        elif init_res.status_code == 402:
                raise APIError(error_result("Received 402 - Unauthorized - bad token?"))
        elif init_res.status_code == 307:
            api_response = requests.get(init_res.headers['Location'], headers=headers, allow_redirects=False)
            if init_res.status_code == 429:
                raise APIError(error_result("Received 429 - Throttled - Polling to fast?"))
            elif  api_response.status_code == 200:
                return api_response.json()
        elif init_res.status_code == 200:
            return init_res.json()
    except Exception as ce:
        print(ce)


def get_data_stream(token, api_endpoint):
    """ Start REST streaming device events given a Nest token.  """
    headers = {
        'Authorization': "Bearer {0}".format(token),
        'Accept': 'text/event-stream'
    }
    url = api_endpoint


    http = urllib3.PoolManager()

    try:
        response = http.request('GET', url, headers=headers, preload_content=False)
    except requests.exceptions.Timeout:
        # Maybe set up for a retry, or continue in a retry loop
        raise APIError(error_result("Timeout on request"))
    except requests.exceptions.TooManyRedirects:
        # Tell the user their URL was bad and try a different one
        raise APIError(error_result("Too many redirects on request"))
    except requests.exceptions.RequestException as e:
        # catastrophic error. bail.
        print(e)
        sys.exit(1)

    client = sseclient.SSEClient(response)

    for event in client.events(): # returns a generator
        event_type = event.event
        # print ("event: ", event_type)
        if event_type == 'open': # not always received here
            print ("The event stream has been opened")
        elif event_type == 'put':
            print ("Received an alert over the Nest stream (or initial data sent)")
            # print ("data: ", event.data)
            event_json = json.loads(event.data)
            poll_cameras(event_json)
        elif event_type == 'keep-alive':
            print ("No data updates. Receiving an HTTP header to keep the connection open.")
        elif event_type == 'auth_revoked':
            print ("The API authorization has been revoked.")
            print ("revoked token: ", event.data)
        elif event_type == 'error':
            print ("Error occurred, such as connection closed.")
            print ("error message: ", event.data)
        else:
            print ("Unknown event, no handler for it.")


# Initialize local cameras object
def init_cam_structures():
    cameras_json = get_nest_data()

    for key, value in cameras_json.items():  # type: (object, object)

        # populate our local cameras datastructure
        name = cameras_json[key]['device_id']
        local_cams_object[name] = get_camera_dict(cameras_json[key]['name'], cameras_json[key]['device_id'], routing_key)


def grab_image(device_id, event_type):

    camera = device_id
    target = Template("https://developer-api.nest.com/devices/cameras/${camera}/last_event/animated_image_url")  # type: Template
    image_url = target.substitute({'camera': camera})

    headers = {
        'authorization': "Bearer " + auth_t,
        'content-type': "application/json",
    }

    # SOMETIMES WE DON'T GET DATA AND NEED TO TRY AGAIN OTHERWISE WE FAIL
    #  File "/Users/ophir/src/team20th/team20-alerts.py", line 75, in poll_cameras
    #     cameras[key]["payload"]["timestamp"] = response["last_event"]["start_time"]
    # TypeError: 'NoneType' object has no attribute '__getitem__'

    try:
        init_res = requests.get(image_url, headers=headers, allow_redirects=False)

        if init_res.status_code == 429:
            raise APIError(error_result("Received 429 - Throttled - Polling to fast?"))
        elif init_res.status_code == 402:
            raise APIError(error_result("Received 402 - Unauthorized - bad token?"))
        elif init_res.status_code == 307:
            api_response = requests.get(init_res.headers['Location'], headers=headers, allow_redirects=False)
            if init_res.status_code == 429:
                raise APIError(error_result("Received 429 - Throttled - Polling to fast?"))
            elif api_response.status_code == 200:
                image = api_response.text
                # clean up the text
                image = image.replace('"','')

                filename = 'images/' + event_type[0] + '-' + event_type[1] + '.gif'
                r = requests.get(image)
                with open(filename, 'wb') as fout:
                    fout.write(r.content)

              #  with requests.get(image, init_res.headers['Location'], headers=headers, allow_redirects=False) as resp, open(filename, 'wb') as out_file:
              #      shutil.copyfileobj(resp, out_file)

        elif init_res.status_code == 200:
            return init_res.json()
    except Exception as ce:
        print(ce)

def poll_cameras(cam_event):
    # type: (object) -> object

    for key, value in local_cams_object.items():
    # print key, value

        # print key, value
        local_cams_object[key]['url'] = local_cams_object[key]['base_url'] + local_cams_object[key]['cam_id'] + '/'

        # If Nest Cloud is not responding
        # HTTPSConnectionPool(host='developer-api.nest.com', port=443): Max retries exceeded with url: /devices/cameras/f3lekKgaeNvSnmjlvY9kwpIeqdEWjvst8opkq0o-ecTH_fxyUXJyZQ/ (Caused by NewConnectionError('<urllib3.connection.VerifiedHTTPSConnection object at 0x10cdb6e50>: Failed to establish a new connection: [Errno 8] nodename nor servname provided, or not known',))
        # No response from

        # DEBUG print (response)
        local_cams_object[key]["payload"]["severity"] = 'critical'
        local_cams_object[key]["payload"]["timestamp"] = cam_event['data'][key]["last_event"]["start_time"]
        local_cams_object[key]["payload"]["source"] = cam_event['data'][key]["name_long"]
        local_cams_object[key]["web_url"] = cam_event['data'][key]["last_event"]["web_url"]

        if cam_event['data'][key]["last_event"]["has_person"]:
            local_cams_object[key]["payload"]["summary"] = "API: " + local_cams_object[key]["payload"]["source"] + ' spotted a person'
            event_type = ("person", cam_event['data'][key]["last_event"]["start_time"] )
        elif cam_event['data'][key]["last_event"]["has_motion"]:
            local_cams_object[key]["payload"]["summary"] = "API: " + local_cams_object[key]["payload"]["source"] + ' spotted movement'
            event_type = ("movement", cam_event['data'][key]["last_event"]["start_time"])
        elif cam_event['data'][key]["last_event"]["has_sound"]:
            local_cams_object[key]["payload"]["summary"] = "API: " + local_cams_object[key]["payload"]["source"] + ' heard a loud noise'
            event_type = ("noise", cam_event['data'][key]["last_event"]["start_time"])
        # sanitize
        clean = dict(local_cams_object[key])

        # Sanitize before sending to PD
        del clean['url']
        del clean['base_url']
        del clean['cam_id']

        oldtime = local_cams_object[key]["last_event_time"]
        newtime = cam_event['data'][key]["last_event"]["start_time"]

        # Skip on start up
        if oldtime:
            if newtime == oldtime:
                # print ("last event time matched -- skipping")
                print (".", end='')
            else:
                try:

                    # Grab the event image and store it locally
                    grab_image(cam_event['data'][key]["device_id"], event_type)

                    #### SEND AN EVENT TO PAGERDUTY #####
                    # create a version 2 event
                    alert = pypd.EventV2.create(clean)

                    # alert return {u'status': u'success', u'message': u'Event processed', u'dedup_key': u'15bf1c5df8fe4ec3bb06cffd4c317cac'}

                    # print ("oldtime : " + oldtime + "  " + "newtime : " + newtime)
                    #print ("last event time NOT matched -- sending PD Alert for", local_cams_object[key]["payload"]["source"])
                    print (local_cams_object[key]["payload"]["summary"], " -- sending PD Alert @", newtime)

                    # ADD IN CODE FOR GRABBING LAST_EVENT/ANIMATED_IMAGE_URL
                    # THEN USE THIS: https://stackoverflow.com/questions/8286352/how-to-save-an-image-locally-using-python-whose-url-address-i-already-know

                except Exception as bad:
                    print(bad)

        local_cams_object[key]["last_event_time"] = newtime




#### START EXECUTION ####


# First initialize our local cameras object
init_cam_structures()

# start listening for events over SSE
get_data_stream(auth_t, nest_api_url)


