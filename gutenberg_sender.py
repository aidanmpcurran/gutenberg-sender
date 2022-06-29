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

from spreadsheet_scheduler import schedule_on_spreadsheet


# If modifying these scopes, delete the file token.json.
SCOPES = ['https://mail.google.com/']

def create_message(sender, to, subject, message_text):
    message = MIMEText(message_text)
    message['to'] = to
    message['from'] = sender
    message['subject'] = subject
    raw_message = base64.urlsafe_b64encode(message.as_string().encode("utf-8"))
    return {
        'raw': raw_message.decode("utf-8")
    }

def create_draft(service, user_id, message_body):
    try:
        message = {'message': message_body}
        draft = service.users().drafts().create(userId=user_id, body=message).execute()

        print("Draft id: %s\nDraft message: %s" % (draft['id'], draft['message']))

        return draft
    except Exception as e:
        print('An error occurred: %s' % e)
        return None


def send_message(service, user_id, message):
    try:
        message = service.users().messages().send(userId=user_id, body=message).execute()
        print('Message Id: %s' % message['id'])
        return message
    except Exception as e:
        print('An error occurred: %s' % e)
        return None



def use_appropriate_regexes(text):
    returned_dates = []
    date_to_chapter = {} #maybe use this at some point later
    int_to_chapter = {}
    counter = 1
    for chapter in text:
        match_date1 = r'(\d+)\w* (January|February|March|April|May|June|July|August|September|October|November|December)'
        match_date2 = r'(January|February|March|April|May|June|July|August|September|October|November|December) (\d+)'
        match_date3 = r'\d+\/\d+\/\d+'
        possible_regexes = [match_date1, match_date2, match_date3]
        for regex in possible_regexes:
            if len(re.findall(regex, chapter)) == max(len(re.findall(match_date1, chapter)), len(re.findall(match_date2, chapter)), len(re.findall(match_date3, chapter))):
                returned_dates.append(re.findall(regex, chapter)[0])
                date_to_chapter[chapter] = re.findall(regex, chapter)[0]
                int_to_chapter[counter] = chapter
                counter += 1

    #return returned_dates
    return [date_to_chapter, int_to_chapter, returned_dates]


def chapter_split(url):
    """Takes an HTML link from Project Gutenberg and returns a list of the book text split into chapters"""
    chap_content = []
    raw_html = request.urlopen(url)
    soup2 = BeautifulSoup(raw_html, features="lxml")
    hrefs_list = re.findall(r'href="#([\S]+)">' , soup2.prettify())

    for href in hrefs_list:
        assembled_regex = "name=\"" + href+ "([\s\S]+?)<a"
        found = re.findall(assembled_regex, str(soup2))[0]
        found = re.sub(r'(  )+', " ", found)
        chap_content.append(re.sub(r'<.+?>|\r|\n', " ", found))

    return chap_content


def main():
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    creds = None #uhhhh excuse me????
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    flow = InstalledAppFlow.from_client_secrets_file(
        'credentials.json', SCOPES)
    creds = flow.run_local_server(port=0)

    try:
        # Call the Gmail API
        service = build('gmail', 'v1', credentials=creds)
        results = service.users().labels().list(userId='me').execute()
        labels = results.get('labels', [])
        my_url = input("Please enter the link to the HTML version of Project Gutenberg text: ")
        chapters = chapter_split(my_url)

        send_as_drafts = input("If this is an epistolary novel, would you like to create drafts at the appropriate times?: ")
        if send_as_drafts == "N":
            for chapter in chapters:
                msg = create_message("aidanmpcurran@gmail.com", "aidan.miguel.curran@berkeley.edu", "Email bot test", chapter)
                send_message( service ,"aidanmpcurran@gmail.com" ,msg) #service, userID, message
                #https://www.gutenberg.org/files/521/521-h/521-h.htm
        else:
            funcCall = use_appropriate_regexes(chapters)
            schedule_on_spreadsheet(funcCall)



##

    except HttpError as error:
        # TODO(developer) - Handle errors from gmail API.
        print(f'An error occurred: {error}')


if __name__ == '__main__':
    main()