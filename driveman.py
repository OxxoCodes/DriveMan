from __future__ import print_function
import sys
import traceback
import os
import io
from time import sleep

import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from apiclient.http import *

from cfg import service, sharedDriveIDs, sharedDriveNames, getCreds

def usageCheck(args, n):
    if len(args) == n:
        return True
    else:
        print('USAGE:   python main.py [ALIAS] [COMMAND] [ARGUMENTS]')
        print('For more information please visit https://github.com/OxxoCode/DriveMan')
        return False

def help(args):
    print('USAGE:')
    print('python main.py [ALIAS] [COMMAND] [ARGUMENTS]\n')
    print('-u, -upload     DIR DEST              Uploads a file located in DIR to folder DEST')
    print('-d, -download   SOURCE DIR            Downloads a file from SOURCE to DIR')
    print('-r, -remove     SOURCE                Removes/deletes a file/folder located at SOURCE')
    print('-m, -meta       SOURCE                Displays the metadata for a file/folder in raw JSON')
    print('-l, -list       SOURCE                Lists the names of all files within a folder\n')

    print('For more information please visit https://github.com/OxxoCode/DriveMan')

def cleanInput(args):
    clean = []
    for i in args:
        if 'drive.google.com' in i:
            clean.append( i.split('/')[-1] )
        else:
            clean.append(i)
    return clean

def meta(args):
    fileID = args[0]
    print(getMetadata(fileID))

def getMetadata(fileID):
    metadata = service.files().get(fileId=fileID, supportsAllDrives=True, fields='*').execute()
    return metadata

def getSize(args):
    fileID = args[0]
    size = 0
    meta = service.files().get(fileId=fileID, supportsAllDrives=True, fields='mimeType, size, name').execute()
    mimeType = meta['mimeType']
    if mimeType == 'application/vnd.google-apps.folder':
        children = folderList(fileID)
        files = []
        for child in children['files']:
            files.append(child['id'])
        files = set(files) #folderList() appears to sometimes list a folder twice. Unsure why, this is, so this is a temp fix (god i hope)
        for f in files:
            size += getSize([f])
    else:
        size += int(meta['size'])

    print('{} : {}'.format(meta['name'],size))
    return size

def getRootFolderID(fileID):
    root = fileID
    while True:
        parent = service.files().get(fileId=root, fields='parents', supportsAllDrives=True).execute()
        if 'parents' not in parent:
            return root
        root = parent['parents'][0]

def handleEmptyFile(path, parents=None): #Drive API throws HTTP 400 when uploading empty file - this function handles that
    if os.path.getsize([path]) == 0:
        name = path.split('/')[-1]
        file_metadata = {
                'name': name
            }
        if parents is not None:
            file_metadata['parents'] = [parents]
        file = service.files().create(body=file_metadata, supportsAllDrives=True).execute()
        return True
    else:
        return False

def upload(args, parents=None): #Resumable upload - Reliable transfer, works well with large files & small files, requires an additional HTTP request
    path = args[0]
    if len(args) > 1:
        parents = args[1]

    if os.path.isdir(path):
        uploadFolder(path, parents)
    else:
        if handleEmptyFile(path, parents) == True:
            return
        
        name = path.split('/')[-1] #Retrieves name at end of path, including file extension
        
        file_metadata = {
                'name': name
            }
        if parents is not None:
            file_metadata['parents'] = [parents]
        media = MediaFileUpload(path,
                                resumable=True)

        print(file_metadata)
        file = service.files().create(body=file_metadata, media_body=media, supportsAllDrives=True).execute()
        print('File {} uploaded'.format(name))

def uploadFolder(path, parents=None):
    if path[-1] != '/':
        path += '/'
    folderName = path.split('/')[-2]
    
    file_metadata = {
            'name': folderName,
            'mimeType': 'application/vnd.google-apps.folder',
            'parents': [parents]
            }
        
    file = service.files().create(body=file_metadata, fields='id', supportsAllDrives=True).execute()
    print('Folder {} created'.format(folderName))
    
    folderID = file['id']
    #folderID = file.get('id', supportsAllDrives=True)
    
    everythingInFolder = next(os.walk(path))
    childFiles = everythingInFolder[2]
    childFolders = everythingInFolder[1]

    print(childFiles, childFolders)
    
    for file in childFiles:
        upload([path+file], parents=folderID)
    for folder in childFolders:
        uploadFolder([path+folder], parents=folderID)

def downloadFolder(folderID, path):
    if path[-1] != '/':
        path += '/'
    if not os.path.exists(path):
        os.makedirs(path)
    name = service.files().get(fileId=folderID, fields='name', supportsAllDrives=True).execute()['name']
    children = folderList(folderID)
    files = []
    for file in children['files']:
        files.append(file['id'])
    for file in files:
        download([file, path+name])

def download(args):
    fileID, path = args[0], args[1]
    if path[-1] != '/':
        path += '/'
    if not os.path.exists(path):
        os.makedirs(path)
    
    metaData = service.files().get(fileId=fileID, fields='name, mimeType', supportsAllDrives=True).execute()
    mimetype = metaData['mimeType']
    name = metaData['name']

    if 'google-apps' in mimetype:
        if mimetype == 'application/vnd.google-apps.folder': #If file is folder
            downloadFolder(fileID, path)
            return True
        else: #Skip Google files, as they require their own download process
            return None
    
    request = service.files().get_media(fileId=fileID)
    fh = io.FileIO(path+name, 'wb')
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    print('Downloading {}'.format(name))
    while done is False:
        while True:
            try:
                status, done = downloader.next_chunk()
                break
            except HttpError:
                print('ERROR 500: Retrying request')
                sleep(2)
                pass
            
    print('File {} downloaded'.format(path+name))

def copy(args, parents=None):
    global service
    fileID = args[0]
    if len(args) > 1:
        parents = args[1]
    mimetype = service.files().get(fileId=fileID, fields='mimeType', supportsAllDrives=True).execute()['mimeType']
    if mimetype == 'application/vnd.google-apps.folder':
        copyFolder(fileID, parents)
    else:
        file_metadata = {}
        if parents is not None:
            file_metadata['parents'] = [parents]
        file = service.files().copy(fileId=fileID, body=file_metadata, supportsAllDrives=True, fields='id, name').execute()
        print('Copying file {}'.format(file.get('name')))
        p = service.files().get(fileId=file['id'], supportsAllDrives=True, fields='parents').execute()['parents']

def copyFolder(folderID, parents=None):
    name = service.files().get(fileId=folderID, fields='name', supportsAllDrives=True).execute()
    print('Copying folder {}...'.format(name['name']))
    file_metadata = {'name': name['name'],
                     'mimeType': 'application/vnd.google-apps.folder'}
    if parents is not None:
        file_metadata['parents'] = [parents]
    folder = service.files().create(body=file_metadata, supportsAllDrives=True, fields='id').execute()
    id_ = folder.get('id')
    children = folderList(folderID)
    for file in children['files']:
        if file['mimeType'] == 'application/vnd.google-apps.folder':
            copyFolder(file['id'], parents=id_)
        else:
            copy([file['id']], parents=id_)

def list(args):
    list = folderList(args[0])
    for file in list['files']:
        print(file['name'])

def folderList(folderID): #Use driveID to specify the shared drive to search in
    root = getRootFolderID(folderID)
    if root in sharedDriveIDs:
        children = service.files().list(driveId=root, includeItemsFromAllDrives=True,
                                        corpora='drive', supportsAllDrives=True,
                                        q='\'{}\' in parents'.format(folderID)).execute()
    else:
        children = service.files().list(q='\'{}\' in parents'.format(folderID)).execute()
    return children

def getFolders(folderID):
    children = folderList(folderID)
    folders = []
    for child in children['files']:
        if child['mimeType'] == 'application/vnd.google-apps.folder':
            folders.append(child['name'])
    return folders

def remove(args):
    fileID = args[0]
    if service.files().get(fileId=fileID, fields='mimeType', supportsAllDrives=True).execute()['mimeType'] == 'application/vnd.google-apps.folder':
        for file in folderList(fileID)['files']:
            remove([file['id']])
        service.files().delete(fileId=fileID, supportsAllDrives=True).execute()
    else:
        service.files().delete(fileId=fileID, supportsAllDrives=True).execute()
