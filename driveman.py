#DriveMan CLI by OxxoCode
#https://github.com/OxxoCode/DriveMan


import argparse

import gdrive

class DriveMan:
    #Parse any DriveMan arguments passed by the user
    def parse_args(self):
        self.parser = argparse.ArgumentParser()
        self.parser.add_argument('-user', '--username',         nargs=1, help="Specify the username/alias for the account you are accessing")
        self.parser.add_argument('-sv', '--service',            nargs=1, help="Specify the service you are using (gdrive, dbox)")
        self.parser.add_argument('-c', '--copy',                nargs=2, help="Copy a file or folder")
        self.parser.add_argument('-d', '--download',            nargs=2, help="Download a file or folder")
        self.parser.add_argument('-u', '--upload',              nargs='+', help="Copy a file or folder")
        self.parser.add_argument('-m', '--move',                nargs=2, help="Move a file a file or folder")
        self.parser.add_argument('-meta', '--metadata',         nargs=1, help="Get the metadata of a file or folder")
        self.parser.add_argument('-l', '--list',                nargs=1, help="List all files and folders in a folder")
        self.parser.add_argument('-r', '--remove',              nargs=1, help="Remove/delete a file or folder")
        self.parser.add_argument('-s', '--size',                nargs=1, help="Get the size a file or folder")
        self.parser.add_argument('-nohash', '--no-hash-check',  nargs=1, help="Skip hash checking when uploading/downloading a file")
        self.args = self.parser.parse_args()
    
    #Handle authentication for each service, determined by value of --service
    def auth(self):
        s = self.args.service[0].lower()
        if s == "gdrive":
            self.gd = gdrive.GDrive()
            self.gd.auth( self.args.username[0] )
        elif s == "dbox":
            print('Dropbox is not currently supported. Coming soon!')
        else:
            print("ERROR: Must specify the service being used with -sv or --service.")
            print("Available services are: GDrive")
    
    #Core functionality of DriveMan
    def run(self):
        #Obtain list of all shared drives accessible by user.
        #Necessary for some functions which behave differently if a file is located in a shared drive
        self.gd.listSharedDrives() 
        
        if self.args.copy:
            self.gd.copy( self.gd.cleanInput(self.args.copy[0]) , self.gd.cleanInput(self.args.copy[1]) )

        elif self.args.download: #Has some bugs - getting HTTP Errors on some files for an unknown reason. Also seems to look at files twice?
            self.gd.download( self.gd.cleanInput(self.args.download[0]) , self.gd.cleanInput(self.args.download[1]) )

        elif self.args.upload: 
            #Could potentially improve, but it's a lot of additional code that I can just fix with an if-else, so eh. 
            #https://stackoverflow.com/questions/4194948/python-argparse-is-there-a-way-to-specify-a-range-in-nargs
            if len(self.args.upload) == 2:
                self.gd.upload( self.gd.cleanInput(self.args.upload[0]) , self.gd.cleanInput(self.args.upload[1]) )
            else:
                self.gd.upload( self.gd.cleanInput(self.args.upload[0]) )

        elif self.args.move:
            self.gd.move( self.gd.cleanInput(self.args.move[0]) , self.gd.cleanInput(self.args.move[1]) )

        elif self.args.list:
            self.gd.list( self.gd.cleanInput(self.args.list[0]) )

        elif self.args.remove:
            self.gd.remove( self.gd.cleanInput(self.args.remove[0]) )

        elif self.args.size:
            self.gd.size( self.gd.cleanInput(self.args.size[0]) )

        elif self.args.metadata:
            meta =  self.gd.getMetadata( self.gd.cleanInput(self.args.metadata[0]))
            for key in meta.keys():
                print('{} : {}'.format(key, meta[key]))


def main():
    driveman = DriveMan()

    driveman.parse_args()
    driveman.auth()
    driveman.run()

    
if __name__ == '__main__':
    main()
