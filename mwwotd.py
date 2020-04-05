#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import os
basedir = os.path.dirname(os.path.realpath(__file__))
if os.path.exists(basedir):
    sys.path.append(basedir)
libdir = os.path.join(os.path.realpath(basedir), 'lib')
assetsdir = os.path.join(os.path.realpath(basedir), 'assets')
iconsdir = os.path.join(os.path.realpath(assetsdir), 'alphaicons')
tempdir = os.path.join(os.path.realpath(basedir), 'temp')

from bs4 import BeautifulSoup
import requests

def pull_wotd_page():

    r = requests.get('https://www.merriam-webster.com/word-of-the-day')

    return r.text

def extract_wotd_info(htmldoc):
    soup = BeautifulSoup(htmldoc,'html.parser')

    word = soup.find('div','word-and-pronunciation').h1.text
    part_of_speech = soup.find('span','main-attr').text
    pronunciation = soup.find('span','word-syllables').text
    definition = soup.find('div','wod-definition-container').p.text

    return (word, part_of_speech, pronunciation, definition)

def save_to_disk(word, part_of_speech, pronunciation, definition, location):
    with open(location, 'w') as text_file:
        print("Word: {}".format(word), file=text_file)
        print("Part of speech: {}".format(part_of_speech), file=text_file)
        print("Pronunciation: {}".format(pronunciation), file=text_file)
        print("Definition: {}".format(definition), file=text_file)

if __name__ == "__main__":
    location = os.path.join(tempdir, 'merriam_webster_word_of_the_day.txt')

    webpage = pull_wotd_page()
    (word, part_of_speech, pronunciation, definition) = extract_wotd_info(webpage)
    save_to_disk(word, part_of_speech, pronunciation, definition, location)
