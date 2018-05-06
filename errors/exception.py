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
class Error(Exception):
    """Base class for exceptions in this module."""
    pass

class APIError(Error):
    def __init__(self, code, result):
        self.code = code
        self.result = result

def get_error_msg_help(code, default=""):
    help_msgs = {
        # HTTP Redirect code handled by application, not sent to browser.
        # This error may show as a 401 Unauthorized,
        # if not handled by the WWN client.
        # See
# https://developers.nest.com/documentation/cloud/how-to-handle-redirects
        # Adding here to show all error codes from the API server.
        307: "The WWN API has sent a redirect endpoint",

        # INVALID REQUEST  - This is a general error but the message
        # returned from the API will be more specific,
        # such as "Thermostat is not online", "Not writable",
        # "Invalid value for Away", etc.
        # Only use the following message to append to the message returned
        # from the Nest API server, not replace it.
        400: """The request made by this client was not valid.
             Please revise this request before repeating it.""",

        # AUTHORIZATION ERROR - see
        # https://developers.nest.com/documentation/cloud/how-to-auth
        401: """The Works with Nest connection has been removed.
             Please re-authorize to get a valid token, 
             then retry the request.""",

        # FORBIDDEN
        403: """The credentials being used to access the Nest service 
                are invalid. This request should not be repeated.""",

        # NOT FOUND
        404: "The requested path could not be found.",

        # REJECTED DUE TO RATE LIMITATIONS - see
        # https://developers.nest.com/documentation/cloud/data-rate-limits
        429: """The WWN client has reached its rate limits.
             Please retry this request at a later time. """,

        # INTERNAL ERROR
        500: """The WWN API has reported an internal server error (500).
             Please review the request and re-attempt at a 
             later point in time.""",

        # SERVICE UNAVAILABLE
        503: """The WWN API is not currently available to service 
                client requests.  Please retry at a later time."""
    }

    return help_msgs.get(code, default)