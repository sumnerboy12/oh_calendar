oh_calendar
===========

Python script to query a list of Google Calendars and update openHAB.

The idea is to use the publicly available Google Calendars which list public holidays for just about every country (see http://www.guidingtech.com/2329/add-public-holidays-google-calendar/) to automatically update an openHAB item which indicates if 'today' is a holiday or not. This item can then be used to disable wakeup alarms or whatever else you see fit.

You will need to sign up to Google and follow the instructions at https://developers.google.com/google-apps/calendar/get_started to setup a project and enable the Calendar API. You will need to follow the steps to configure a new 'command line python' project which will automatically generate a client_secrets.json file and sample python app (which this script is based off).

You can ignore the sample app but you will need the client_secrets.json file. Copy this into the same path as the oh_calendar files.

You will then need to edit the oh_calendar.conf file to set the openHAB host and port as well as the openHAB item to update, and the list of Google Calendar ids.

You will also need to update oh_calendar to set the location of the oh_calendar scripts.

You will need to run the bash script (oh_calendar) for the first time manually. You should be presented with a URL you will need to copy to a browser to authenticate your app. Copy the code generated from the browser back into your shell and hit enter. This will save your credentials for later use, i.e. this is a once off operation.

Then configure a cron job to run this script every day at just after midnight.