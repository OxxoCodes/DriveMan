from __future__ import print_function
import sys
import traceback
import os
import io
import shutil
import hashlib
from time import sleep

import pickle
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import *

import backoff

class GDrive:
    def auth(self, user):
        SCOPES = ['https://www.googleapis.com/auth/drive']

        self.creds = None
        if os.path.exists('{}.pickle'.format(user)):
            with open('{}.pickle'.format(user), 'rb') as token:
                self.creds = pickle.load(token)

        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                self.creds = flow.run_local_server(port=0)

            with open('{}.pickle'.format(user), 'wb') as token:
                pickle.dump(self.creds, token)

        self.service = build('drive', 'v3', credentials=self.creds)

    def cleanInput(self, orig_input):
        output = orig_input
        if os.path.isdir(orig_input) or os.path.isfile(orig_input): #Handle local files/directories
            output = output.replace('\\', '/')
            return output

        if 'drive.google.com' in output: #handle https://drive.google.com/drive/... and change it to just /drive/...
            output = output.split('drive.google.com')[1:]
            output = ''.join(output)
        if '/' in output: #Handle URLs. If this if statement doesn't run, assume only the file ID was passed
            output = output.split('/')
            for i in output:
                if len(i) > 10 and "usp=sharing" not in i:
                    return i
        return output

    def meta(self, args): #Gets all metadata from getMetadata() and prints it
        metadata = self.getMetadata(args)
        print(metadata)

    def getMetadata(self, fileID): #Returns all metadata of a file
        metadata = self.service.files().get(fileId=fileID, supportsAllDrives=True, fields='*').execute()
        return metadata

    def getSize(self, args): #Gives the size of a file/folder
        fileID = args[0]
        size = 0
        meta = self.service.files().get(fileId=fileID, supportsAllDrives=True, fields='mimeType, size, name').execute()
        mimeType = meta['mimeType']
        if mimeType == 'application/vnd.google-apps.folder':
            children = self.folderList(fileID)
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

    def getRootFolderID(self, fileID): #Gets the root folder id of a file/folder
        root = fileID
        while True: #Iterates through all parents until there are no more parent folders, then returns the topmost folder id
            parent = self.service.files().get(fileId=root, fields='parents', supportsAllDrives=True).execute()
            if 'parents' not in parent:
                return root
            root = parent['parents'][0]

    def listSharedDrives(self):
        content = {}
        sharedDrives = self.service.drives().list(pageSize='100').execute()
        for sharedDrive in sharedDrives['drives']:
            content[sharedDrive['id']] = sharedDrive['name']

        self.sharedDriveIDs = list(content)
        self.sharedDriveNames = list(content.values())

    def handleEmptyFile(self, path, parents=None): #Drive API throws HTTP 400 when uploading empty file - this function handles that by creating the empty file with the same name
        if os.path.getsize(path) == 0:
            name = path.split('/')[-1]
            file_metadata = {
                    'name': name
                }
            if parents is not None:
                file_metadata['parents'] = [parents]
            self.service.files().create(body=file_metadata, supportsAllDrives=True).execute()
            return True
        else:
            return False

    def move(self, path, parents=None): #Moves a file/folder
        if (':/' in path or ':\\' in path) and 'drive.google.com/drive' not in path: #First arg is a local directory
            if self.upload(path, parents): #Only delete file if successfully uploaded
                try:
                    shutil.rmtree(args[0])
                except NotADirectoryError:
                    os.remove(args[0])
        else: #Not a local directory; assuming it is a cloud file
            self.copy(path, parents)
            self.remove(path)

    def getMd5(self, fileID): #Obtains the md5 checksum of a file from Drive API
        try:
            md5 = self.service.files().get(fileId=fileID, fields='md5Checksum', supportsAllDrives=True).execute()['md5Checksum']
            return md5
        except KeyError:
            return None

    def calculateMd5(self, path): #Calculates the md5 checksum of a local file
        with open(path, 'rb') as f:
            md5 = hashlib.md5( f.read() ).hexdigest()
            return md5

    def upload(self, path, parents=None, skipHash=False): #Uploads file. If a folder, passes to uploadFolder(). Uses resumable upload
        if os.path.isdir(path):
            self.uploadFolder(path, parents)
        else:
            #If no parent is provided, then upload to "My Drive"
            if parents is None:
                parents = self.service.files().get(fileId='root').execute()['id']
                
            if self.handleEmptyFile(path, parents) == True:
                return True
        
            if '/' in path:
                name = path.split('/')[-1] #Retrieves name at end of path, including file extension
            elif '\\' in path:
                name = path.split('\\')[-1]
        
            file_metadata = {
                    'name': name,
                    'parents': [parents]
                }
            
            media = MediaFileUpload(path,
                                    resumable=True)

            file = self.service.files().create(body=file_metadata, media_body=media, fields='id', supportsAllDrives=True).execute()

            if not skipHash: #Do not check hash if nocheck argument is passed
                print('Checking hash...')
                if self.getMd5(file['id']) != self.calculateMd5(path):
                    print('ERROR: Checksums do not match')
            print('File {} uploaded'.format(name))

            return True

    def uploadFolder(self, path, parents=None): #Uploads a folder and its contents
        if path[-1] != '/':
            path += '/'
        folderName = path.split('/')[-2]
        
        #If no parent is provided, then upload to "My Drive"
        if parents is None:
            parents = self.service.files().get(fileId='root').execute()['id']
        
        file_metadata = {
                'name': folderName,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parents]
                }
        
        file = self.service.files().create(body=file_metadata, fields='id', supportsAllDrives=True).execute()
        print('Folder {} created'.format(folderName))
    
        folderID = file['id']
    
        everythingInFolder = next(os.walk(path))
        childFiles = everythingInFolder[2]
        childFolders = everythingInFolder[1]
    
        for file in childFiles:
            self.upload(path+file, parents=folderID)
        for folder in childFolders:
            self.uploadFolder(path+folder, parents=folderID)

    def downloadFolder(self, folderID, path, skipHash=False): #Downloads a folder and its contents
        #if '-nohash' in args:
        #    skipHash = True

        if path[-1] != '/':
            path += '/'
        if not os.path.exists(path):
            os.makedirs(path)

        name = self.service.files().get(fileId=folderID, fields='name', supportsAllDrives=True).execute()['name']
        children = self.folderList(folderID)
        print('Downloading folder \"'+name+'\"')
        files = []

        for file in children['files']:
            files.append(file['id'])
        for file in files:
            self.download(file, path+name, skipHash=skipHash)

    def download(self, fileID, path, skipHash=False): #Downloads a file. If a folder, pass to downloadFolder()
        #if '-nohash' in args:
        #    skipHash = True

        if path[-1] != '/':
            path += '/'
        if not os.path.exists(path):
            os.makedirs(path)
    
        metaData = self.service.files().get(fileId=fileID, fields='name, mimeType, size', supportsAllDrives=True).execute()
        mimetype = metaData['mimeType']
        name = metaData['name']

        if 'google-apps' in mimetype:
            if mimetype == 'application/vnd.google-apps.folder': #If file is folder
                self.downloadFolder(fileID, path, skipHash=skipHash)
                return True
            else: #Skip Google files, as they require their own download process
                print('ERROR: Unable to download Google files (docs, sheets, etc)')
                return False

        size = metaData['size']

        print('Downloading file \"{}\"'.format(name))

        if size == '0':
            with open(path+name, 'w') as f:
                pass
        else:
            request = self.service.files().get_media(fileId=fileID)
            fh = io.FileIO(path+name, 'wb')
            self.downloader = MediaIoBaseDownload(fh, request)
            self.done = False
        
            errorCounter = 1
            maxErrors = 5
            while done is False:
                while True:
                    try:
                        status, done = downloader.next_chunk()
                        break
                    except HttpError as e: #Wait 2 seconds then retry download request. Need to implement exponential backoff decorator
                        status_code = e.resp['status']
                        print('HttpError {}: Retrying request ({}/{}).'.format(status_code, errorCounter, maxErrors))
                        errorCounter += 1
                        sleep(2)
                        if errorCounter > maxErrors:
                            print('Skipping file \"{}\"...\n'.format(name))
                            done = True
                            return False
    
            if not skipHash:
                print('checking hash...')
                if self.getMd5(fileID) != self.calculateMd5(path+name):
                    print('ERROR: Checksums do not match')
        print('File \"{}\" downloaded\n'.format(path+name))

    def copy(self, fileID, parents=None): #Copies a file. If a folder, pass to copyFolder()
        print(fileID)
        mimetype = self.service.files().get(fileId=fileID, fields='mimeType', supportsAllDrives=True).execute()['mimeType']
        if mimetype == 'application/vnd.google-apps.folder':
            self.copyFolder(fileID, parents)
        else:
            file_metadata = {}
            if parents is not None:
                file_metadata['parents'] = [parents]
            file = self.service.files().copy(fileId=fileID, body=file_metadata, supportsAllDrives=True, fields='id, name').execute()
            print('Copying file {}'.format(file.get('name')))

    def copyFolder(self, folderID, parents=None): #Copies a folder and its contents
        name = self.service.files().get(fileId=folderID, fields='name', supportsAllDrives=True).execute()

        print('Copying folder {}...'.format(name['name']))

        file_metadata = {'name': name['name'],
                         'mimeType': 'application/vnd.google-apps.folder'}

        if parents is not None:
            file_metadata['parents'] = [parents]

        folder = self.service.files().create(body=file_metadata, supportsAllDrives=True, fields='id').execute()
        id_ = folder.get('id')

        #Iterate through all items found in folder. Recursively call copyFolder on subdirectories and call download on files
        children = self.folderList(folderID)
        for file in children['files']:
            if file['mimeType'] == 'application/vnd.google-apps.folder':
                self.copyFolder(file['id'], parents=id_)
            else:
                self.copy(file['id'], parents=id_)

    def list(self, fileID): #Prints all files within folder. NOT recursive
        list = self.folderList(fileID)
        for file in list['files']:
            print(file['name'])

    def folderList(self, folderID): #Returns list of all files in folder
        root = self.getRootFolderID(folderID) #Get root directory ID

        #Listing files is handled differently in shared drives
        if root in self.sharedDriveIDs:
            children = self.service.files().list(driveId=root, includeItemsFromAllDrives=True,
                                            corpora='drive', supportsAllDrives=True,
                                            q='\'{}\' in parents'.format(folderID)).execute()
        else:
            children = self.service.files().list(q='\'{}\' in parents'.format(folderID)).execute()
        return children

    #Currently unused
    def getFolders(folderID): #List all folders within folder (does not check within subfolders; only returns folders that are one level below folderID)
        children = self.folderList(folderID)
        folders = []
        for child in children['files']:
            if child['mimeType'] == 'application/vnd.google-apps.folder':
                folders.append(child['name'])
        return folders

    def remove(self, fileID): #Deletes a file/folder and its contents
        if self.service.files().get(fileId=fileID, fields='mimeType', supportsAllDrives=True).execute()['mimeType'] == 'application/vnd.google-apps.folder':
            for file in self.folderList(fileID)['files']:
                self.remove(file['id'])
            self.service.files().delete(fileId=fileID, supportsAllDrives=True).execute()
        else:
            self.service.files().delete(fileId=fileID, supportsAllDrives=True).execute()
