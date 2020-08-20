#Driveman CLI by OxxoCode
#https://github.com/OxxoCode

from cfg import creds, service
import traceback
import sys
from googleapiclient.discovery import build

def main():
    try:
        import driveman
    except:
        print('There was an import error. Please ensure you have the proper dependencies installed.')
        print(traceback.format_exc())

    try:
        #Command: (function, numOfNecessaryArgs)
        commands = {'-c':(driveman.copy, 2),
                    '-copy':(driveman.copy, 2),
                    '-d':(driveman.download, 2),
                    '-download':(driveman.download, 2),
                    '-u':(driveman.upload, 2),
                    '-upload':(driveman.upload, 2),
                    '-m':(driveman.meta, 1),
                    '-meta':(driveman.meta, 1),
                    '-l':(driveman.list, 1),
                    '-list':(driveman.list, 1),
                    '-r':(driveman.remove, 1),
                    '-remove':(driveman.remove, 1),
                    '-s':(driveman.getSize, 1),
                    '-size':(driveman.getSize, 1),
                    '-h':(driveman.help, 0),
                    '-help':(driveman.help, 0) }
        
        creds = driveman.getCreds(sys.argv[1].lower())
        service = build('drive', 'v3', credentials=creds)

        input_ = driveman.cleanInput(sys.argv[3:len(sys.argv)])

        if not driveman.usageCheck(input_, commands[sys.argv[2]][1]):
            return
        else:
            commands[sys.argv[2]][0]( input_ )
    
    except:
        print('UNKNOWN ERROR')
        print('Please report this to the github page.\n')
        print(traceback.format_exc())

if __name__ == '__main__':
    main()