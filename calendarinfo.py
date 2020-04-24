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

class calday:
    def __init__(self,dt):
        self.date = dt.date()
        self.datestr = dt.strftime("%-d %b")
        self.fulldayevents = []
        self.timedevents = []

    def add_fullday_event(self,event):
        self.fulldayevents.append(event)

    def add_timed_event(self,event):
        self.timedevents.append(event)

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

    for i in range(0,numdays):
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

def sort_calendar_data(eventslist):
    days = {}
    for event in eventslist:
        if event['start'].date() not in days:
            days[event['start'].date()] = calday(event['start'])
        if event['allday'] == True:
            days[event['start'].date()].add_fullday_event(event)
        else:
            days[event['start'].date()].add_timed_event(event)

    return days

def cal_for_display():
    calendardat = get_calendar_data()
    splitcalendar = sort_calendar_data(calendardat)

    logging.info("create calendar lines: start")
    tz = pytz.timezone(TIME_ZONE)

    # sort through all upcoming days
    lines=[]
    for day in sorted(splitcalendar.keys()):
        # print day
        lines.append({'display': day.strftime("%-d %b").upper(),
            'font': 'font24',
            'header': True})

        # list fullday events first
        for fulldayevent in splitcalendar[day].fulldayevents:
            lines.append({'display': '   ' + fulldayevent['summary'],
                'font': 'font21', 'header': False})

        # list timed events next (sorted)
        sortedtimedevents = sorted(splitcalendar[day].timedevents, key=lambda k: (k['sortstart'], k['sortend']))
        for timedevent in sortedtimedevents:
            lines.append({'display': '   ' + timedevent['sortstart'].strftime("%-I:%M%p") + ' : ' + timedevent['summary'],
                'font': 'font21', 'header': False})

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

