from __future__ import print_function

import base64
import os.path
import re
from email.mime.text import MIMEText
from urllib import request

from bs4 import BeautifulSoup
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import pygsheets
import numpy as np

def schedule_on_spreadsheet(func_called):
    gc = pygsheets.authorize()

    # Open spreadsheet and then worksheet
    sh = gc.open('Scheduling Test')
    wks = sh.sheet1

    counter = 1
    for pair in func_called:
        currindice = "A" + str(counter)
        wks.update_value(currindice, str(pair[2][0]) + str(pair[2][1]))
        currindice2 =  "B" + str(counter)
        wks.update_value(currindice2, func_called[0][func_called[1][counter]])
        counter += 1




