from __future__ import print_function
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
import sys, os
import pickle

SCOPES = ['https://www.googleapis.com/auth/drive']

def getCreds(user):
    creds = None
    if os.path.exists('{}.pickle'.format(user)):
        with open('{}.pickle'.format(user), 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)

        with open('{}.pickle'.format(user), 'wb') as token:
            pickle.dump(creds, token)

    return creds

def listSharedDrives():
    global service
    content = {}
    sharedDrives = service.drives().list(pageSize='100').execute()
    for sharedDrive in sharedDrives['drives']:
        content[sharedDrive['id']] = sharedDrive['name']
    sharedDriveIDs = list(content)
    sharedDriveNames = list(content.values())
    return sharedDriveIDs, sharedDriveNames

creds = getCreds(sys.argv[1])
service = build('drive', 'v3', credentials=creds)
sharedDriveIDs, sharedDriveNames = listSharedDrives()
