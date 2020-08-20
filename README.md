# DriveMan
A cloud-based file manager, currently focused on Google Drive

# USAGE:
  `python main.py [ALIAS] [COMMAND] [ARGUMENTS]`

When referring to files/folders located within Google Drive, ensure you are using the file ID. This can be found in the URL linking to the file/folder.

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
 
## Commands:
    -u, -upload     DIR DEST              Uploads a file located in DIR to folder DEST
    -d, -download   SOURCE DIR            Downloads a file from SOURCE to DIR
    -r, -remove     SOURCE                Removes/deletes a file/folder located at SOURCE
    -m, -meta       SOURCE                Displays the metadata for a file/folder in raw JSON
    -l, -list       SOURCE                Lists the names of all files within a folder
    -s, -size       SOURCE                Displays the size of all files and folders within the given source, in bytes
    -h, -help       N/A                   Displays the basic syntax, list of commands, and the link to the project's GitHub page
 
