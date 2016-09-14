#!/usr/bin/env python
import os
import time
import sys
sys.path.append('/usr/local/munki')
import argparse 
from urllib2 import Request, urlopen, URLError
from munkilib import FoundationPlist
from munkilib import munkicommon
import subprocess

parser = argparse.ArgumentParser(description='setManifest.py')
parser.add_argument('-v','--verbose', help='Run script in verbose mode.', action='store_true')
args = parser.parse_args()

if args.verbose:
    def verboseprint(*args):
        # Print each argument separately so caller doesn't need to
        # stuff everything to be printed into a single string
        for arg in args:
           print arg,
        print
else:   
    verboseprint = lambda *a: None      # do-nothing function


def createAndPrintManifestChoicesDict(file):
    choices = file.readlines()
    ###separates the textfile line by line into a list so that I can add the user shortname to it
    test = []
    for item in choices:
        test = test + [item]
    ###appends shortname to the list
    account = subprocess.Popen(['users'],shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (out, err) = account.communicate()
    
    ##should address issues if user is logged into multiple accounts
    if " " in out:
        out = out.split(" ")
        
        for item in out:
             
            if '\n' in item:
                item = item.replace("\n","")
            test.append(item)         
    else:
        test.append(out)


    i = 1
    choicesDict = {}
    
    for line in test:
        if line == '-\n':
            print '-'
            continue
        else:
            choicesDict[i] = line.strip('\n')
            print i, choicesDict[i]
            i += 1
    verboseprint('****INFO**** closing inputfile')   
    return choicesDict

def UpdateClientIdentifier(ManifestName): 
        munkicommon.set_pref("ClientIdentifier", ManifestName)


# main
verboseprint('**************Verbose Mode*************')

if os.getuid() != 0:
    print 'You must run this as root.'
    sys.exit(0)



# get manifestChoices.txt from the server 
verboseprint('****INFO**** attempting to fetch inputfile')
try:
    inputfile = urlopen('http://munki.reed.edu/munki_repo/manifestChoices.txt')
    choicesDict = createAndPrintManifestChoicesDict(inputfile)
except URLError as e:
    verboseprint('****ERROR**** ',e)
    print 'Failed to fetch list of available manifests.'
    print 'You either don\'t have a network connection or the munki server is down.' 
    sys.exit(0)


# get the current ClientIdentifier
currentClientIdentifier = munkicommon.pref('ClientIdentifier')

# display the current ClientIdentifier
print '\nCurrent:',currentClientIdentifier

# prompt for selection and test for errors
while True:
    selection = raw_input('Select new:\n> ')
    try:
        choicesDict[int(selection)]
        break
    except (ValueError, KeyError):
        print 'Invalid selection.  Try again or press Ctrl-c to abort'
        continue

manifest = choicesDict[int(selection)]

# display selection & prompt for verification
while True:
    raw_input('Hit Ctrl-c to abort or ENTER to confirm change to {}'.format(manifest))
    break

# modify ManagedInstalls.plist
UpdateClientIdentifier(manifest)

# test for successful change
# get the new ClientIdentifier from ManagedInstalls
newClientIdentifier = munkicommon.pref('ClientIdentifier')
if newClientIdentifier == manifest:
    print '\nClientIdentifier successfully changed from %s to %s' % (currentClientIdentifier, newClientIdentifier)
    print 'Launching ManagedSoftwareUpdate.app'
    os.system('open \"/Applications/Utilities/Managed Software Update.app\"')
else:
    print 'Sorry, something went wrong.  The ClientIdentifier was not changed.'
    sys.exit(0)

#END

