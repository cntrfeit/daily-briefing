#!/usr/bin/python
# -*- coding: utf-8 -*-

from datetime import datetime, timedelta, date, time
import pytz
from dateutil.tz import UTC
import ssl
import configparser

import logging

import icalendar
import recurring_ical_events
import urllib.request

ssl._create_default_https_context = ssl._create_unverified_context

location = 'temp/debug_cal.txt'

config = configparser.ConfigParser(interpolation=None)
config.read('config.txt')

TIME_ZONE = config['general']['timezone']
CALENDARS_DAYS_AHEAD = config['general'].getint('days_ahead', fallback=3)
CALENDARS = [
        {
            'url':config['calendar1']['url'],
            'apple':config['calendar1'].getboolean('apple'),
            'name':config['calendar1']['name']},
        {
            'url':config['calendar2']['url'],
            'apple':config['calendar2'].getboolean('apple'),
            'name':config['calendar2']['name']},
        {
            'url':config['calendar3']['url'],
            'apple':config['calendar3'].getboolean('apple'),
            'name':config['calendar3']['name']}
        ]

def add_timed_event(eventdat,cal):
    tz = pytz.timezone(TIME_ZONE)
    event_info = {}
    event_info['start'] = eventdat['DTSTART'].dt
    event_info['end'] = eventdat['DTEND'].dt
    event_info['summary'] = eventdat.get('SUMMARY').to_ical().decode('UTF-8').strip().replace('\,',',')
    event_info['allday'] = (type(eventdat['DTSTART'].dt) is date)
    event_info['cal'] = cal
    event_info['sortstart'] = event_info['start'].astimezone(tz)
    event_info['sortend'] = event_info['end'].astimezone(tz)

    return event_info

def add_fullday_events(eventdat,cal):
    tz = pytz.timezone(TIME_ZONE)
    full_day_events = []
    numdays = (eventdat['DTEND'].dt - eventdat['DTSTART'].dt).days

    for i in range(0,numdays+1):
        event_info = {}
        event_info['start'] = eventdat['DTSTART'].dt
        event_info['end'] = eventdat['DTEND'].dt
        event_info['summary'] = eventdat.get('SUMMARY').to_ical().decode('UTF-8').strip().replace('\,',',')
        event_info['allday'] = (type(eventdat['DTSTART'].dt) is date)
        event_info['cal'] = cal
        event_info['sortstart'] = (datetime.combine(event_info['start'], time(0,0)) + timedelta(days=i)).astimezone(tz)
        event_info['sortend'] = (datetime.combine(event_info['start'], time(11,59)) + timedelta(days=i)).astimezone(tz)
        full_day_events.append(event_info)

    return full_day_events

def get_calendar_data():
    tz = pytz.timezone(TIME_ZONE)
    start_dt = datetime.now().astimezone(tz)
    end_dt = start_dt + timedelta(days = CALENDARS_DAYS_AHEAD)

    allevents = []
    for cal in CALENDARS:
        logging.info("get calendar info")
        ical_string = urllib.request.urlopen(cal['url']).read()
        calendar = icalendar.Calendar.from_ical(ical_string)
        caldat = recurring_ical_events.of(calendar).between(start_dt, end_dt)
        #caldat = events(url=cal['url'], fix_apple=cal['apple'], start=start_dt, end=end_dt)
        logging.info("processing calendar info")
        for eventdat in caldat:
            if type(eventdat['DTSTART'].dt) is date:
                allevents = allevents + add_fullday_events(eventdat,cal['name'])
            else:
                allevents.append(add_timed_event(eventdat,cal['name']))

    return allevents

def before_today(enddate):
    tz = pytz.timezone(TIME_ZONE)
    starttoday = datetime.now().replace(microsecond=0,second=0, minute=0, hour=0).astimezone(tz)

    if enddate < starttoday:
        return True
    else:
        return False

def cal_for_display():
    calendardat = get_calendar_data()

    logging.info("create calendar lines: start")
    tz = pytz.timezone(TIME_ZONE)
    lines = {}
    sortedevents = sorted(calendardat, key=lambda k: (k['sortstart'], -k['allday'], k['sortend']))

    currdate = datetime(1990,1,1,0,0,0,0,pytz.UTC)
    row = 0
    for event_info in sortedevents:
        # check if the day is in the past and skip it
        if before_today(event_info['sortend']) == True:
                continue

        # all day events
        if event_info['allday'] == True:
            # check if it's the first event of the day
            if event_info['sortstart'].replace(microsecond=0,second=0, minute=0, hour=0, day=(event_info['sortstart'] + timedelta(days=1)).day) > currdate:
                lines[row] = {'display': event_info['sortstart'].replace(microsecond=0,second=0, minute=0, hour=0, day=(event_info['sortstart'] + timedelta(days=1)).day).strftime("%-d %b").upper(),
                        'font': 'font24', 'header': True}
                row = row+1
                currdate = event_info['sortstart'].replace(microsecond=0,second=0, minute=0, hour=0, day=event_info['sortstart'].day+1)

            # print ALL DAY and description
            lines[row] = {'display': '   ' + event_info['summary'],
                    'font': 'font21', 'header': False}

        # events at specific times
        else:
            # check if it's the first event of the day
            if event_info['sortstart'].replace(microsecond=0,second=0, minute=0, hour=0) > currdate:
                lines[row] = {'display': event_info['sortstart'].strftime("%-d %b").upper(),
                        'font': 'font24', 'header': True}
                row = row+1
                currdate = event_info['sortstart'].replace(microsecond=0,second=0, minute=0, hour=0)

            # print start time and description
            lines[row] = {'display': '   ' + event_info['sortstart'].strftime("%I:%M%p") + ': ' + event_info['summary'],
                    'font': 'font21', 'header': False}

        # iterate line count up
        row = row+1

    logging.info("create calendar lines: end")
    return lines

def save_to_disk(caldat, location):
    numrows = len(caldat)

    with open(location, 'w') as text_file:
        for i in range(0, numrows):
            line = caldat[i]
            print("{}".format(line['display']), file=text_file)

if __name__ == "__main__":
    caldat = cal_for_display()
    save_to_disk(caldat, location)

