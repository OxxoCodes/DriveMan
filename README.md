# DriveMan
A cloud file manager, currently focused on Google Drive

# USAGE:
  `python driveman.py [ARGUMENTS]`

# Dependencies:
The Google Drive API must be enabled and installed on your device for DriveMan to operate correctly. In addition, a `credentials.json` file is required.

To complete these dependencies, follow steps 1 and 2 on the following page, and place `credentials.json` in the same directory that DriveMan is installed to.

https://developers.google.com/drive/api/v3/quickstart/python

Tested on Python 3.8.2 - https://www.python.org/downloads/

## Alias:
 The alias is the name tied to your Google account.
 For example, if you have the email johndoe@gmail.com, you can use the alias 'john' (or any other alias you wish) to refer to this account.
 You can have seperate aliases pointing to seperate accounts, and you can have multiple aliases pointing to the same account.
 Aliases are stored as `YOURALIAS.pickle`
 When an alias is not recognized, your browser will open a webpage in which you can log into your Google account and allow DriveMan access to your Google Drive files.
 
## Arguments:
Note: When referring to local directories that contain spaces in their name, please surround them in double quotation marks. 
For example: "C:/Users/John/My Directory"

    -user, --username                        Specify the username/alias of the account being used
    -sv, --service   SERVICE                 Specify the service being used (currently only supports gdrive)
    -c, --copy     SOURCE DEST               Copies a file or folder from SOURCE to DIR
    -d, --download       SOURCE DEST         Downloads a file or folder from SOURCE to DIR
    -u, --upload       SOURCE DEST           Uploads a file or folder from SOURCE to DIR
    -m, --move       SOURCE DEST             Move a file or folder from SOURCE to DIR (does not yet support local files)
    -meta, --metadata       FILE/FOLDER      Lists all available metadata of a file or folder
    -l, --list     DIR DEST                  Lists all files & folders available in DIR (including those in trash; not recursive)
    -r, --remove   FILE/FOLDER               Removes a file located in DIR
    -s, --size     FILE/FOLDER               Gets the size of a file or folder (currently broken)
    -n, --nohash                             Don't ensure file integrity when uploading/downloading

 
## Roadmap (In order of current importance):
•Implement DropBox support

•Implement OneDrive support

•If possible, implement MEGA support through mega.py

•While it's not a cloud storage service, per se, having the ability to move files directly to/from Internet Archive could be beneficial in some use cases

•iCloud Drive via PyiCloud?

•Box?
