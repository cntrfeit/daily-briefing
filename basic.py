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

config = configparser.ConfigParser()
config.read('config.txt')

# lat/lon for Dark Sky weather
lat = round(config['DS weather'].getfloat('lat'),3)
lon = round(config['DS weather'].getfloat('lon'),3)

# station ID for Environment Canada (old)
#WEATHERSTATIONID = config['EC weather']['WEATHERSTATIONID']

TIME_ZONE = config['general']['timezone']

import logging
import time
from PIL import Image,ImageDraw,ImageFont
import traceback

from lib import epd7in5bc_V2

from datetime import datetime, timedelta, date, time
import pytz
from dateutil.tz import UTC

#from weatherinfo import get_weather, extract_alerts, extract_forecasts
from weatherinfo import get_DS_forecasts, extract_DS_alerts, extract_DS_forecasts

from calendarinfo import cal_for_display

from mwwotd import pull_wotd_page, extract_wotd_info

def get_day():
    tz = pytz.timezone(TIME_ZONE)
    now = datetime.now()
    now_righttz = now.astimezone(tz)
    return now_righttz.strftime("%A")

def get_date():
    tz = pytz.timezone(TIME_ZONE)
    now = datetime.now()
    now_righttz = now.astimezone(tz)
    return now_righttz.strftime("%-d %b %Y")

def get_lastupdatedtime():
    tz = pytz.timezone(TIME_ZONE)
    now_righttz = datetime.now().astimezone(tz)
    return now_righttz.strftime("%Y-%m-%d %H:%M:%S %Z%z")

def text_wrap(text, font, max_width):
    """Wrap text base on specified width. 
        This is to enable text of width more than the image width to be display
        nicely.
        @params:
            text: str
                text to wrap
            font: obj
                font of the text
            max_width: int
                width to split the text with
        @return
            lines: list[str]
                list of sub-strings
    """
    lines = []

    # If the text width is smaller than the image width, then no need to split
    # just add it to the line list and return
    if font.getsize(text)[0]  <= max_width:
        lines.append(text)
    else:
        #split the line by spaces to get words
        words = text.split(' ')
        i = 0
        # append every word to a line while its width is shorter than the image width
        while i < len(words):
            line = ''
            while i < len(words) and font.getsize(line + words[i])[0] <= max_width:
                line = line + words[i]+ " "
                i += 1
            if not line:
                line = words[i]
                i += 1
            lines.append(line)
    return lines

def make_image():
    font48 = ImageFont.truetype(os.path.join(libdir, 'Font.ttc'), 48)
    font36 = ImageFont.truetype(os.path.join(libdir, 'Font.ttc'), 36)
    font24 = ImageFont.truetype(os.path.join(libdir, 'Font.ttc'), 24)
    font21 = ImageFont.truetype(os.path.join(libdir, 'Font.ttc'), 21)
    font18 = ImageFont.truetype(os.path.join(libdir, 'Font.ttc'), 18)
    font15 = ImageFont.truetype(os.path.join(libdir, 'Font.ttc'), 15)
    font12 = ImageFont.truetype(os.path.join(libdir, 'Font.ttc'), 12)

    # for 1/4 inch top and bottom borders, need 30.76 pixels
    # take an extra one for buffer
    topborder = 32
    bottomborder = epd.width - 32

    # basic portrait layout
    logging.info("draw basic vertical image")
    image = Image.new('1', (epd.height, epd.width), 255)
    imagered = Image.new('1', (epd.height, epd.width), 255)
    draw_image = ImageDraw.Draw(image)
    draw_imagered = ImageDraw.Draw(imagered)

    # date at the top
    today_dt = get_date()
    w,h = draw_image.textsize(today_dt, font = font48)
    draw_image.text(((epd.height-w)/2,topborder), today_dt, font = font48, fill = 0)
    topheight = topborder+h+2

    # weekday just below
    today_day = get_day()
    w,h = draw_image.textsize(today_day, font = font36)
    draw_image.text(((epd.height-w)/2,topheight), today_day, font = font36, fill = 0)
    topheight = topheight+h+24

    # draw weather

    # alert info
    (forecasts, alerts) = get_DS_forecasts(lat, lon)
    #(alertdat, forecastdat) = get_weather(WEATHERSTATIONID)
    (alertcolor, alerts_blurb) = extract_DS_alerts(alerts)
    #(alertcolor, alerts_blurb) = extract_alerts(alertdat)
    w,h = draw_image.textsize(alerts_blurb, font=font18)
    w2,h2 = draw_image.textsize(alerts_blurb, font=font15)
    if alertcolor == 'red':
        draw_imagered.rectangle(((epd.height-w-4)/2,topheight,(epd.height-w-4)/2 + w + 2,topheight+h+4),outline=0)
        draw_image.text(((epd.height-w)/2,topheight+2), alerts_blurb, font=font18,fill=0)
    else:
        draw_image.text(((epd.height-w2)/2,topheight+2), alerts_blurb, font=font15,fill=0)
    topheight = topheight+h+6
        
    # 3-hour interval forecasts
    for x in range(0,5):
        relhr = 3*x
        left = 96*x
        #(hr,temp,pop,icon) = extract_forecasts(forecastdat,relhr,TIME_ZONE)
        (hr,temp,pop,icon) = extract_DS_forecasts(forecasts,x)
        # box
        draw_image.rectangle((left+1,topheight,left+94,topheight+192), outline=0)

        # time
        w,h = draw_image.textsize(hr, font=font15)
        draw_image.text((left+1+(94-w)/2,topheight+2), hr, font=font15, fill=0)

        # temperature in C
        tempC = temp + "°C"
        w2,h2 = draw_image.textsize(tempC, font=font24)
        draw_image.text((left+1+(94-w2)/2,topheight+4+h+2), tempC, font=font24, fill=0)
        # temperature in F
        tempF = str(int(float(temp)*9/5 + 32)) + "°F"
        w3,h3 = draw_image.textsize(tempF, font=font24)
        draw_image.text((left+1+(94-w3)/2,topheight+4+h+2+h2+2), tempF, font=font24, fill=0)

        # image
        image.paste(icon,(left+3,topheight+4+h+2+h2+2+h3+12))
        #draw_image.rectangle((left+3,topheight+4+h+2+h2+2+h3+12,left+92,topheight+4+h+2+h2+2+h3+101), outline=0)

        # prob of precip
        poptext = "PoP: " + pop + "%"
        w,h = draw_image.textsize(poptext, font=font12)
        draw_image.text((left+1+(94-w)/2,topheight+192-h-2), poptext, font=font12, fill=0)
    topheight = topheight + 204

    # calendar
    sortedlines = cal_for_display()
    beginheight = topheight
    rows = 0
    rowmax = 10
    for i in range(0,len(sortedlines)):
        line = sortedlines[i]
        if line['header'] == True:
            beginheight = beginheight + 4
        writelines = text_wrap(line['display'], eval(line['font']), 479)
        first = True
        for writeline in writelines:
            if first == False:
                writeline = '        ' + writeline
            w,h = draw_image.textsize(writeline, font=eval(line['font']))
            draw_image.text((1,beginheight), writeline, font=eval(line['font']), fill=0)
            beginheight = beginheight + h + 2

            rows = rows+1
            first = False

        if rows == rowmax:
            break
    topheight = beginheight + 12

    # word of the day
    wotdpage = pull_wotd_page()
    (word, part_of_speech, pronunciation, definition) = extract_wotd_info(wotdpage)
    wotd_line1 = text_wrap(word, font24, 479)
    wotd_line2 = text_wrap("/" + pronunciation + "/ " + part_of_speech, font21, 479)
    wotd_line3 = text_wrap(definition, font21, 460)
    beginheight = topheight
    for line in wotd_line1:
        w,h = draw_image.textsize(line, font=font24)
        draw_image.text((1,beginheight), line, font=font24, fill=0)
        beginheight = beginheight + h + 2 
    for line in wotd_line2:
        w,h = draw_image.textsize(line, font=font21)
        draw_image.text((1,beginheight), line, font=font21, fill=0)
        beginheight = beginheight + h + 2
    for line in wotd_line3:
        w,h = draw_image.textsize(line, font=font21)
        if beginheight + h < bottomborder - 20:
            draw_image.text((19,beginheight), line, font=font21, fill=0)
        beginheight = beginheight + h + 2
    topheight = beginheight + 4

    # updated at timestamp, at bottom
    lastupdatedtext = 'Last updated: ' + get_lastupdatedtime()
    w,h = draw_image.textsize(lastupdatedtext, font=font12)
    draw_image.text(((epd.height-w)/2,bottomborder-h-2), lastupdatedtext, font=font12, fill=0)
    
    return (image,imagered)

def save_image():

    logging.info("save image")
    (image,imagered) = make_image()
    image.save(os.path.join(basedir, 'test.bmp'))
    imagered.save(os.path.join(basedir, 'testred.bmp'))

def display_image():

    logging.info("initialize and clear")
    epd.init()
    epd.Clear()

    (image,imagered) = make_image()

    epd.display(epd.getbuffer(image),epd.getbuffer(imagered))

    logging.info("Sleep")
    epd.sleep()

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    logging.info("epd7in5bc_V2 basic test")

    if len(sys.argv) > 1 and sys.argv[1] == 'save':
        save_image()
    else:
        epd = epd7in5bc_V2.EPD()
        display_image()
