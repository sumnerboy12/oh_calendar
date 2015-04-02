# -*- coding: utf-8 -*-
#
# Copyright (C) 2013 Google Inc.
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

"""Command-line application for accessing a Google Calendar API.
Usage:
  $ python oh_calendar.py

You can also get help on all the command-line flags the program understands
by running:

  $ python oh_calendar.py --help

"""

import argparse
import httplib2
import os
import time
import sys
import requests

from datetime import datetime, date, time, timedelta
from apiclient import discovery
from oauth2client import file
from oauth2client import client
from oauth2client import tools
from dateutil.parser import parse

# Parser for command-line arguments.
parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter,
    parents=[tools.argparser])

# CLIENT_SECRETS is name of a file containing the OAuth 2.0 information for this
# application, including client_id and client_secret. You can see the Client ID
# and Client secret on the APIs page in the Cloud Console:
# <https://cloud.google.com/console#/project/920731717151/apiui>
CLIENT_SECRETS = os.path.join(os.path.dirname(__file__), 'client_secrets.json')

# Set up a Flow object to be used for authentication.
# Add one or more of the following scopes. PLEASE ONLY ADD THE SCOPES YOU
# NEED. For more information on using scopes please see
# <https://developers.google.com/+/best-practices>.
FLOW = client.flow_from_clientsecrets(CLIENT_SECRETS,
  scope=[
      'https://www.googleapis.com/auth/calendar',
      'https://www.googleapis.com/auth/calendar.readonly',
    ],
    message=tools.message_if_missing(CLIENT_SECRETS))


def main(argv):
  # Parse the command-line flags.
  flags = parser.parse_args(argv[1:])

  # If the credentials don't exist or are invalid run through the native client
  # flow. The Storage object will ensure that if successful the good
  # credentials will get written back to the file.
  storage = file.Storage('credentials.dat')
  credentials = storage.get()
  if credentials is None or credentials.invalid:
    credentials = tools.run_flow(FLOW, storage, flags)

  # Create an httplib2.Http object to handle our HTTP requests and authorize it
  # with our good Credentials.
  http = httplib2.Http()
  http = credentials.authorize(http)

  # Construct the service object for the interacting with the Calendar API.
  service = discovery.build('calendar', 'v3', http=http)

  # Load the configuration file
  conf = {}
  try:
    execfile('oh_calendar.conf', conf)
  except Exception, e:
    print "Cannot load configuration file: %s" % str(e)
    sys.exit(1)
  
  # Work out what dates to query the calendar (i.e. today only)
  # NOTE: this now seems to return events from tomorrow as well
  #       even if I shrink the query to < 1 day
  dateQueryMin = datetime.combine(date.today(), time(0, 0))
  dateQueryMax = dateQueryMin + timedelta(days=1)
  
  # Format for our request
  dateQueryMinStr = dateQueryMin.isoformat() + 'Z'
  dateQueryMaxStr = dateQueryMax.isoformat() + 'Z'

  # Check each calendar in turn
  isHoliday = 'OFF'  
  for calendar in conf['calendars']:
    try:
      # The Calendar API's events().list method returns paginated results, so we
      # have to execute the request in a paging loop. First, build the
      # request object. The arguments provided are:
      #   primary calendar for user
      request = service.events().list(calendarId=calendar, timeMin=dateQueryMinStr, timeMax=dateQueryMaxStr)
      # Loop until all pages have been processed.
      while request != None:
        # Get the next page.
        response = request.execute()
        # Accessing the response like a dict object with an 'items' key
        # returns a list of item objects (events).
        events = response.get('items', [])
        for event in events:
          # Check each events start date as this query can return dates outside
          # our query range
          start = event.get('start').get('date')
          if parse(start) == dateQueryMin:
            #print "%s is reporting a holiday: %s" % (calendar, event.get('summary'))
            isHoliday = 'ON'
        # Keep processing
        request = service.events().list_next(request, response)
        
    except client.AccessTokenRefreshError:
      print ("The credentials have been revoked or expired, please re-run the application to re-authorize")
      sys.exit(1)
  
  # Get the openHAB connection properties
  server = conf['server']
  port = conf['port']
  itemname = conf['itemname']
  username = conf['username']
  password = conf['password']

  # Send an update to the openHAB REST API
  url = 'http://' + username + ':' + password + '@' + server + ':' + str(port) + '/rest/items/' + itemname + '/state'
  headers = { 'Content-Type': 'text/plain' }
  try:
    r = requests.put(url, headers=headers, data=isHoliday)
    if (r.status_code != requests.codes.ok):
      print "url: %s" % url
      print "value: %s" % isHoliday
      print "failed put request: %s" % r.status_code
      sys.exit(1)
  except Exception, e:
    print "url: %s" % url
    print "value: %s" % isHoliday
    print str(e)
    sys.exit(1)
    
# For more information on the Calendar API you can visit:
#
#   https://developers.google.com/google-apps/calendar/firstapp
#
# For more information on the Calendar API Python library surface you
# can visit:
#
#   https://developers.google.com/resources/api-libraries/documentation/calendar/v3/python/latest/
#
# For information on the Python Client Library visit:
#
#   https://developers.google.com/api-client-library/python/start/get_started
if __name__ == '__main__':
  main(sys.argv)
