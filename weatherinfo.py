#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import os
import configparser
basedir = os.path.dirname(os.path.realpath(__file__))
if os.path.exists(basedir):
    sys.path.append(basedir)
libdir = os.path.join(os.path.realpath(basedir), 'lib')
assetsdir = os.path.join(os.path.realpath(basedir), 'assets')
iconsdir = os.path.join(os.path.realpath(assetsdir), 'alphaicons')

from datetime import datetime, timedelta, date, time
import pytz

from PIL import Image

from darksky.api import DarkSky
from darksky.types import languages, units, weather

from pyowm import OWM

config = configparser.ConfigParser()
config.read('config.txt')

# dark sky API
API_KEY = config['DS weather']['key']

# open weather maps API key
OWM_API_KEY = config['OWM weather']['key']

DSiconfiles = {
        'clear-day': 'sunny.png',
        'clear-night': 'clear_night.png',
        'rain': 'heavy_rain.png',
        'snow': 'heavy_snow.png',
        'sleet': 'hail.png',
        'wind': 'wind.png',
        'fog': 'mist.png',
        'cloudy': 'mostly_cloudy.png',
        'partly-cloudy-day': 'mostly_cloudy_day.png',
        'partly-cloudy-night': 'mostly_cloudy_night.png',
        'hail': 'heavy_hail.png',
        'thunderstorm': 'thunder.png',
        'tornado': 'tornado.png'
        }

ECiconfiles = {
        '00':'sunny.png',
        '01':'sunny.png',
        '02':'mostly_cloudy_day.png',
        '03':'mostly_cloudy.png',
        '04':'mostly_cloudy.png',
        '05':'mostly_cloudy_day.png',
        '06':'drizzle_day.png',
        '07':'snow_cloud_day.png',
        '08':'snow_cloud.png',
        '09':'thunder.png',
        '10':'mostly_cloudy.png',
        '11':'rain_cloud.png',
        '12':'heavy_rain.png',
        '13':'storm.png',
        '14':'hail.png',
        '15':'snow_cloud.png',
        '16':'snow_cloud.png',
        '17':'heavy_snow.png',
        '18':'heavy_snow.png',
        '19':'thunder.png',
        '23':'mist.png',
        '24':'mist.png',
        '25':'snow.png',
        '26':'snow.png',
        '27':'heavy_hail.png',
        '28':'drizzle.png',
        '29':'none.png',
        '30':'clear_night.png',
        '31':'clear_night.png',
        '32':'mostly_cloudy_night.png',
        '33':'mostly_cloudy_night.png',
        '34':'mostly_cloudy_night.png',
        '35':'mostly_cloudy_night.png',
        '36':'drizzle_night.png',
        '37':'snow_cloud_night.png',
        '38':'snow_cloud_night.png',
        '39':'thunder_night.png',
        '40':'wind.png',
        '41':'tornado.png',
        '42':'tornado.png',
        '44':'none.png',
        '45':'tornado.png'
        }

def get_weather(weatherstation):
    ecdat = ECData(station_id=weatherstation, language='english')
    return (ecdat.alerts, ecdat.hourly_forecasts)

def get_DS_forecasts(latitude, longitude):
    darksky = DarkSky(API_KEY)
    forecast = darksky.get_forecast(latitude, longitude,
            exclude=[weather.MINUTELY, weather.FLAGS]
            )

    # weather now, +[3/6/9/12] hour forecasts
    everyThreeHours = {}
    everyThreeHours[str(0)] = forecast.currently
    for i in range(1,5):
        idx = 3*i
        everyThreeHours[str(i)] = forecast.hourly.data[idx]

    return (everyThreeHours, forecast.alerts)

def get_OWM_forecasts(latitude, longitude):
    owm = OWM(OWM_API_KEY)

def extract_DS_alerts(alertdata):
    numalerts = len(alertdata)
    text = ''
    num = {'advisory': 0,'watch': 0,'warning': 0}

    for alert in alertdata:
        # count number of each type
        for alerttype in ['advisory','watch','warning']:
            if alert.severity == alerttype:
                num[alerttype] = num[alerttype] + 1
    
    prev = False
    if num['warning'] > 0:
        text = 'Warnings: ' + str(num['warning'])
        prev = True
    if num['watch'] > 0:
        if prev == True:
            text = text + '; '
        text = text + 'Watches: ' + str(num['watch'])
    if num['advisory'] > 0:
        if prev == True:
            text = text + '; '
        text = text + 'Advisories: ' + str(num['advisory'])
    
    if numalerts == 0:
        return ('black', 'no weather alerts')
    else:
        return ('red', text)

def extract_alerts(data):
    numalerts = 0
    text = ""
    for alerttyp, alertinf in data.items():
        numthistyp = len(alertinf['value'])
        numalerts = numalerts + numthistyp
        if numthistyp > 0:
            text = text + alertinf['label'] + ": " + numthistyp + "; "
    
    if numalerts == 0:
        return ('black',"no weather alerts")
    else:
        return ('red',text)

def extract_DS_forecasts(allHourlyForecasts,idx):
    weatherDat = allHourlyForecasts[str(idx)]
    temp = str(int(float(weatherDat.temperature)))
    pop = str(int(float(weatherDat.precip_probability)*100))
    icon = Image.open(os.path.join(os.path.realpath(iconsdir), DSiconfiles[weatherDat.icon]))
    hr = weatherDat.time.strftime('%-I:%M%p')

    return (hr, temp, pop, icon)

def extract_forecasts(fullforecast,relhr,TIME_ZONE):
    matchtime = datetime.utcnow().replace(microsecond=0, second=0, minute=0) + timedelta(hours=1+relhr)
    matchstr = matchtime.strftime("%Y%m%d%H%M")
    tz = pytz.timezone(TIME_ZONE)
    localtime = datetime.now().astimezone(tz).replace(microsecond=0, second=0, minute=0) + timedelta(hours=1+relhr)
    localstr = localtime.strftime("%-I%p")

    for fcast in fullforecast:
        if fcast['period'] == matchstr:
            temp = fcast['temperature']
            pop = fcast['precip_probability']
            icon = Image.open(os.path.join(os.path.realpath(iconsdir), ECiconfiles[fcast['icon_code']]))
            #icon = Image.open(os.path.join(os.path.realpath(iconsdir), "test.png"))

    return (localstr, temp, pop, icon)

if __name__ == "__main__":
    # lat/long
    lat = round(config['DS weather'].getfloat('lat'),3)
    lon = round(config['DS weather'].getfloat('lon'),3)
    #lat = round(config['OWM weather'].getfloat('lat'),3)
    #lon = round(config['OWM weather'].getfloat('lon'),3)

    # pull forecast
    (forecastsThreeHours, alerts) = get_DS_forecasts(lat, lon)
    #(forecastsThreeHours, alerts) = get_OWM_forecasts(lat, lon)

    # get any alerts
    (alertcolor, alerttext) = extract_DS_alerts(alerts)
    print(alerttext)

    # get forecasts
    for i in range(0,5):
        (hr, temp, pop, icon) = extract_DS_forecasts(forecastsThreeHours,i)
        print('Time: ' + hr)
        print('Temperature: ' + temp + 'C')
        print('Probability of Precipitation: ' + pop + '%')

    
