#!/usr/bin/python

import os
import pwd
import sys
import logging
import re
import getopt 
import subprocess
#import xlrd
#import xlwt
import glob
from branches import *
from vobdb import *

sys.path.append('./')
import constants as c

def usage():
    print """
        usage: lockVobs.py -a [lock|report|reconcile] 
            [-d sincedate]
            [-i inputFile -g globSpec] 
            [-l DEBUG|INFO|WARN|ERROR|CRITICAL] 
            -[v]erbose
    """ 


def init():

    global InFile
    global LogLevel
    global Action
    global GlobSpec
    global Source
    global SinceDate

    GlobSpec='/vobs/*'

    thisUser=pwd.getpwuid(os.getuid())[0]

    rval=True
    logDir='./logs'
    logFileName='%s/auditvobs-%s.log' % (logDir, thisUser)

    try:
        (opts, args) = getopt.getopt(sys.argv[1:], "a:d:g:hi:l:v", ["help", "InFile="])
    except getopt.GetoptError as err:
        # print help information and exit:
        print str(err) # will print something like "option -a not recognized"
        usage()
        sys.exit(2)

    InFile = None
    LogLevel = 'DEBUG'
    verbose = False
    for o, a in opts:
        if o == "-v":
            verbose = True
        elif o in ("-g", "--globspec"):
            Source="fs"
            GlobSpec = a
        elif o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o in ("-a", "--action"):
            Action = a
        elif o in ("-d", "--sincedate"):
            SinceDate = a
        elif o in ("-i", "--infile"):
            Source="infile"
            InFile = a
        elif o in ("-l", "--loglevel"):
            LogLevel = a
        else:
            assert False, "unhandled option"
            
    if os.path.exists(logDir):
        rval=True
    else:
        if os.mkdir(logDir, 0777) != False:
            # chmod because the mkdir
            # mode still depends on umask
            if os.chmod(logDir, 0777) != False:
                rval=True
            else:
                print "Unable to set permissions on logs dir: %s" % logDir
                rval=False
        else:
             print "Unable to create logs directory: %s" % logDir 

    if rval:
        if os.access(logDir, os.W_OK):
            rval=True
        else:
            print "logs dir is not writeable"
            rval=False
        
    if rval:
        # assuming loglevel is bound to the string value obtained from the
        # command line argument. Convert to upper case to allow the user to
        # specify --log=DEBUG or --log=debug
        numeric_level = getattr(logging, LogLevel.upper(), None)
        if not isinstance(numeric_level, int):
            raise ValueError('Invalid log level: %s' % LogLevel)
            rval=False

    if rval:
        # All you need to log to a file
        #logging.basicConfig(filename='%s' % logFileName, filemode='w', level=numeric_level)

        # To log to the console, too
        logger = logging.getLogger()
        logger.setLevel(numeric_level)
        formatter = logging.Formatter("%(levelname)s - %(message)s")

        # Add the file handler
        #fh = logging.RotatingFileHandler(filename='%s/lockVobs.log', mode='a', maxBytes=1000, backupCount=5, encoding=None, delay=0)
        fh = logging.FileHandler(filename='%s' % logFileName, mode='a')
        fh.setLevel(numeric_level)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        fh.setFormatter(formatter)
        logger.addHandler(fh)

        if verbose:
            # Add the console handler
            ch = logging.StreamHandler()
            ch.setLevel(numeric_level)
            #formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            formatter = logging.Formatter("%(levelname)s - %(message)s")
            ch.setFormatter(formatter)
            logger.addHandler(ch)

    if InFile:
        if os.path.exists(InFile):
            rval=True                
        else:
            logger.error("Specified infile doesn't exist: %s" % InFile)
            rval=False

    if rval:
        if Action in ('lock', 'report', 'reconcile'):
            if InFile:
                    rval=True                
            else:
                logger.error("InFile is required")
                rval=False
    
    if rval:
        if Action.lower() == "lock":
            if thisUser == c.VobAdmin:
                logger.debug('Performing protected action as %s ' % c.VobAdmin)
            else: 
                logger.error('Must be %s to perform action: %s and you are %s' % (c.VobAdmin, Action, thisUser)) 
                rval=False

    return rval 

def isLocked(vob):

    rval=False

    logger = logging.getLogger()

    logger.debug('verifying if %s is locked' % vob)
    ccom='%s lslock vob:%s' % (c.Cleartool, vob)
    logger.debug("executing cc com '%s' " % ccom)

    process=subprocess.Popen(ccom, 
        shell=True, 
        executable=c.Shell, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE)

    (out, err)=process.communicate()

    sts=process.poll()

    if sts==0:
        logger.debug('cc command was successful -- now parsing stdout.')
        logger.debug('parsing /%s/' % out)
        rval=lsLockSaysLocked(out)

    else:
        logger.debug('cc command failed due to: %s.' % err)

    return rval

def lsLockSaysLocked(desc):

    rval=False
 
    logger = logging.getLogger()

    lockedString='Locked for all users'

    # works with python 2.6, not with 2.4.3 
    pattobj = re.compile(r'.*(%s)(.*)' % lockedString, re.M|re.S)
    # works with python 2.6 and 2.4.3
    #pattobj = re.compile(r'(?msi).*(Locked for all users)(.*)')

    matchobj=pattobj.match(desc)

    if matchobj:
        logger.debug('lslock says this vob is locked: %s' % matchobj.group(1))
        rval=True
    else:
        logger.debug('lslock says this vob is not locked: %s' % desc)

    return rval


def descSaysLocked(desc):

    rval=False
 
    logger = logging.getLogger()

    #versioned object base "/vobs/cargomax" (locked)

    logger.debug('parsing /%s/ to see if vob is locked' % desc)
    pattobj = re.compile(r'versioned object base\s+"([^"]+)"\s+\(locked\)$', re.M|re.S)

    matchobj=pattobj.match(desc)

    if matchobj:
        logger.debug('desc says %s is locked.' % matchobj.group(1))
        rval=True
    else:
        logger.debug('desc says vob is not locked.')

    return rval


def lockVob(vob):

    rval=False

    logging.debug('locking vob:%s' % vob)
    ccom='%s lock vob:%s' % (c.Cleartool, vob)
    expResponse='Locked versioned object base'

    logging.debug("executing cc com '%s' " % ccom)

    process=subprocess.Popen(ccom, 
        shell=True, 
        executable=c.Shell, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE)

    (out, err)=process.communicate()

    sts=process.poll()

    if sts==0:
        logging.debug('cc command was successful -- now parsing stdout.')
        logging.debug('parsing /%s/' % out)

        # works with python 2.6, not with 2.4.3 
        pattobj = re.compile(r'.*(%s)(.*)' % expResponse, re.M|re.S)
        # works with python 2.6 and 2.4.3
        #pattobj = re.compile(r'(?msi).*(Locked for all users)(.*)')

        matchobj=pattobj.match(out)

        if matchobj:
            logging.debug('expected response found: %s' % matchobj.group(1))
            rval=True
        else:
            logging.warn('failed to get a match for: %s' % line)
    else:
        logging.error('cc command failed due to: %s.' % err)

    return rval

def lockVobs(inFile):

    logging.debug("InFile=%s" % inFile) 

    inFileName, inFileExt=os.path.splitext(inFile)
    if inFileExt == '.xlsx':
        rval=lockVobsFromSS(inFile)
    else:
        rval=lockVobsFromTxt(inFile)

    return rval

def lockVobsFromSS(inFile):

    rval=0
    numVobs=0
    numToBeLocked=0
    numLocked=0

    vobDict = []
    failedList = [] 
    skipList = []

    vobDict = loadVobDictFromVobsTab(inFile, skipList)

    for vob in vobDict:
        numVobs+=1
        if vobDict[vob]['to_be_locked'] == "YES":
            logging.debug('vob is set to be locked: %s' % vob) 
            numToBeLocked+=1
            if isLocked(vob):
                logging.debug('vob is already locked: %s' % vob)
                numLocked+=1
            else:
                if lockVob(vob):
                    numLocked+=1
                else:
                    failedList.append(vob)
        else:
            logging.debug('vob is not set to be locked: %s' % vob) 

    logging.info('-----locking summary---------')
    logging.info('%s total vobs' % numVobs)
    logging.info('%s vobs were set to be locked' % numToBeLocked)
    logging.info('%s vobs were locked' % numLocked)

    if numLocked==numToBeLocked: 
        logging.info('SUCCESS -- all vobs that should be locked are')
    else:
        logging.error('FAIL -- the following vobs should be locked but were not:')
        for vob in failedList:
            logging.error(vob)
        rval=1

    return rval


def lockVobsFromTxt(inFile):

    rval=0
    numVobs=0
    numLocked=0

    vobList = []
    failedList = [] 
    skipList = []

    vobList = loadVobListFromInFile(inFile, skipList)

    for vob in vobList:

        numVobs+=1
        if isLocked(vob):
            logging.debug('vob is already locked: %s' % vob)
            numLocked+=1
        else:
            if lockVob(vob):
                numLocked+=1
            else:
                failedList.append(vob)

    logging.info('%s out of %s vobs locked' % (numLocked, numVobs))

    if numLocked==numVobs:
        logging.info('SUCCESS -- all vobs are locked')
    else:
        logging.error('FAIL -- the following vobs were not locked:')

        for vob in failedList:
            logging.error(vob)

        rval=1

    return rval

def loadVobListFromTxt(inFile, skipList):

    global LogLevel

    rval=True

    logging.debug("inFile=%s" % inFile) 


    f = open(inFile, 'r')
    if f:
        logging.debug("opened %s" % inFile)

        list = [line.rstrip() for line in f.readlines()]
        f.close()
        #logging.debug(list)
    else:
        rval=False

    return list

def isaVob(vob):

    rval=True

    #logging.debug('verifying that %s is a vob' % vob)
    ccom='%s desc vob:%s' % (c.Cleartool, vob)

    process=subprocess.Popen(ccom, 
        shell=True, 
        executable=c.Shell, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE)

    (out, err)=process.communicate()

    sts=process.poll()

    if sts==0:
        #logging.debug('clearcase says this is a vob: %s.' % vob)
        rval=True
    else:
        logging.warn('clearcase failed to desc vob: %s due to: %s' % (vob, err))
        rval=False

    return rval

def descVob(vob):

    # initialize the return value dictionary in case parsing fails
    rval=dict(created_date='',
         created_username='',
         created_email='',
         storage_loc='',
         storage_global_loc='',
         owner='',
         group='')

    logging.debug('running desc command on %s' % vob)
    ccom='%s desc vob:%s' % (c.Cleartool, vob)

    process=subprocess.Popen(ccom, 
        shell=True, 
        executable=c.Shell, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE)

    (out, err)=process.communicate()

    sts=process.poll()

    if sts==0:
        logging.debug('desc command was successful -- now parsing stdout.')
        logging.debug('parsing /%s/' % out)

        # sample of what will be parsed
        #  created 2003-12-02T14:27:28-06:00 by Karim Chaid (mtscm.crm@sally)
        #  created 1995-05-15T14:31:25-05:00 by ODYM (Chris Waitman) (odym.odym@notlob)
        #  VOB family feature level: 4
        #  VOB storage host:pathname "cmeuxdfw03:/var/scm/PDvob01/crm/merchant.vbs"
        #  VOB storage global pathname "/var/scm/PDvob01/crm/merchant.vbs"
        #  database schema version: 54
        #  modification by remote privileged user: allowed
        #  atomic checkin: disabled
        #  VOB ownership:
        #    owner dev.sabre.com/mtscm
        #    group dev.sabre.com/crm
        #  Additional groups:
        #    group dev.sabre.com/wmbs
        #  Attributes:
        #    FeatureLevel = 4

        pattobj = re.compile( r'.*created\s+(\d{4}-\d\d-\d\d)[^\s]+'
                             r'\s+by\s+(\w+\s+\w+)\s+'
                             r'\(([^)]+)\)'
                             r'.*VOB storage host:pathname "([^"]+)"'
                             r'.*VOB storage global pathname "([^"]+)"'
                             r'.*VOB ownership:.*owner (?:dev\.sabre\.com\/)?([^\n]*)'
                             r'\n\s*group (?:dev\.sabre\.com\/)?([^\n]*).*'
                             ,re.M|re.S)

        matchobj=pattobj.match(out)

        if matchobj:

            logging.debug('match successful')

            logging.debug('7 groups')
            logging.debug('created_date: [%s]' % matchobj.group(1))
            logging.debug('created_username: [%s]' % matchobj.group(2))
            logging.debug('created_email: [%s]' % matchobj.group(3))
            logging.debug('storage_loc: [%s]' % matchobj.group(4))
            logging.debug('storage_global_loc: [%s]' % matchobj.group(5))
            logging.debug('owner: [%s]' % matchobj.group(6))
            logging.debug('group: [%s]' % matchobj.group(7))

            rval=dict(created_date=matchobj.group(1),
                 created_username=matchobj.group(2),
                 created_email=matchobj.group(3),
                 storage_loc=matchobj.group(4),
                 storage_global_loc=matchobj.group(5),
                 owner=matchobj.group(6),
                 group=matchobj.group(7),
                 locked="YES" if descSaysLocked(out) else "NO")

        else:
            logging.warn('desc parsing regex failed for vob: %s' % vob)
    else:
        logging.warn('clearcase failed to desc vob: %s due to: %s' % (vob, err))

    return rval

def loadVobListFromFS(globSpec, verifyVob):

    vobList=[] 
    for dirName in glob.glob(globSpec):
        if verifyVob:
            if isaVob(dirName):
                vobList.append(dirName)
            else:
                logging.warn('Not a valid vob: %s' % dirName)
        else:
            vobList.append(dirName)
        

    return vobList
               
def loadVobDictFromFS(globSpec):

    vobDict={}
    vobList=[]

    vobList=loadVobListFromFS(globSpec)

    for vob in vobList:
        desc=descVob(vob)
        if desc:
            vobDict[vob]=desc
            vobDict[vob]['locked']=isLocked(vob)
        else:
            logging.error('skipping vob %s' % vob)

    return vobDict

def listDict(vobDict):

    rval=True

    for vob in vobDict:
        #logging.debug(vob)
        print "%s->%s" % (vob, vobDict[vob])

    return rval

def loadVobListFromInFile(inFile, skipList):

    inFileName, inFileExt=os.path.splitext(inFile)
    if inFileExt == '.xlsx':
        rval=loadVobListFromVobsTab(inFile, skipList)
    else:
        rval=loadVobListFromTxt(inFile, skipList)

    return rval

def loadVobDictFromInfile(inFile, skipList):

    inFileName, inFileExt=os.path.splitext(inFile)
    if inFileExt == '.xlsx':
        rval=loadVobDictFromVobsTab(inFile, skipList)
    else:
        # don't support loading dict from txt yet -- may never need
        rval=loadVobListFromTxt(inFile, skipList)

    return rval

def reconcileDicts(baseDict, testDict):

    rval=True
    notInTestKeys=0 

    for baseVob in baseDict:
        if baseVob in testDict.keys():
            logging.debug('%s is in both.' % baseVob)
        else:
            logging.debug('%s is is missing in testDict.' % baseVob)
            rval=False
            #notInTestKeys

    return rval

def reconcileVobLists(baseList, testList):

    rval=0
    notInTestKeys=0 

    inSyncList = []
    missingList = []

    for baseVob in baseList:
        #logging.debug('looking for %s in testList.' % baseVob)
        if baseVob in testList:
            logging.debug('%s is in both.' % baseVob)
            inSyncList.append(baseVob) 
        else:
            logging.debug('%s is is missing in testList.' % baseVob)
            missingList.append(baseVob)

    return inSyncList, missingList

def normalizeVobLists(globSpec, inFile):

    logging.debug('globSpec=%s' % globSpec) 

    # We will build 6 lists:
    #   vobListFromFS       -   vobs from the file system
    #   vobListFromInFile   -   vobs from the infile
    #   inSyncFromInFile    -   vobs from the infile that are also on the file system 
    #   inSyncFromFS        -   vobs on the file system that are also in the infile
    #   missingFromInFile   -   vobs from the infile that are not on the file system
    #   missingFromFS       -   vobs from the file system that are not in the infile

    vobListFromFS = []
    vobListFromInFile = []
    inSyncFromInFile = []
    inSyncFromFS = []
    missingFromInFile = []
    missingFromFS = []

    vobListFromFS=loadVobListFromFS(globSpec, missingFromFS)
    vobListFromInFile=loadVobListFromInFile(inFile, vobListFromInFile)
    (inSyncFromInFile, missingFromFS) = reconcileVobLists(vobListFromInFile, vobListFromFS)

    if len(missingFromFS) == 0:
        logging.info('All %s vobs in %s are present in %s' % 
            (inSyncFromInFile, inFile, globSpec))
    else:
        logging.info('The following vobs are in %s but not in %s' % 
            (inFile, globSpec))
        for vob in missingFromFS:
            logging.info(vob)

    (inSyncFromFS, missingFromInFile) = reconcileVobLists(vobListFromFS, vobListFromInFile)

    if len(missingFromInFile) == 0:
        logging.info('All %s vobs in %s are present in %s' % 
            (inSyncFromFS, globSpec, inFile))
    else:
        logging.info('The following vobs are in %s but not in %s' % 
            (globSpec, inFile))
        for vob in missingFromInFile:
            logging.info(vob)

    return (vobListFromFS, 
        vobListFromInFile, 
        inSyncFromInFile, 
        inSyncFromFS, 
        missingFromInFile, 
        missingFromFS)

def reconcileVobs(globSpec, inFile):

    (vobListFromFS,
    vobListFromInFile,
    inSyncFromInFile,
    inSyncFromFS,
    missingFromInFile,
    missingFromFS) =  normalizeVobLists(globSpec, inFile)

    combinedVobDict = {}
    branchesDict = {}

    dictFromInFile=loadVobDictFromInfile(InFile, missingFromFS) 

    for vob in dictFromInFile:
        combinedVobDict = dictFromInFile.copy()
        combinedVobDict[vob].update(descVob(vob))

    branchesDict=auditBranches(vobDict=combinedVobDict) 

    writeVobsTab('vobs-generated.xls', combinedVobDict)

def findLastMod(vob):

    rval = "unknown"

#lshist -fmt "%Sd|%u|%En|%e\n"

    logger = logging.getLogger()

    logging.debug('looking for last modification to vob:%s' % vob)
    ccom='%s lshist -fmt "%Sd|%u|%En|%e\n vob:%s' % (c.Cleartool, vob)

    logging.debug("executing cc com '%s' " % ccom)

    process=subprocess.Popen(ccom, 
        shell=True, 
        executable=c.Shell, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE)

    (out, err)=process.communicate()

    sts=process.poll()

    if sts==0:
        logging.debug('cc command was successful -- now parsing stdout and loading finding most recent mod')
        #logging.debug('parsing /%s/' % out)

        pattobj = re.compile(r'.*(%s)(.*)' % expResponse, re.M|re.S)

        matchobj=pattobj.match(out)

        if matchobj:
            logging.debug('expected response found: %s' % matchobj.group(1))
            rval=True
        else:
            logging.warn('failed to get a match for: %s' % line)
    else:
        logging.debug('cc command failed due to: %s.' % err)

    return rval
    return rval

def main():

    global InFile
    global LogLevel
    global Action
    global GlobSpec
    global SinceDate

    SinceDate = ''

    skipList = []

    if init():

        if Action.lower() == 'lock':
            lockVobs(InFile)

        elif Action.lower() == 'branches':
            branchesSince(vob=GlobSpec, since=SinceDate, infile=InFile)

        elif Action.lower() == 'list':

            if Source=="fs":
                logging.debug('GlobSpec=%s' % GlobSpec) 
                dictFromFS=loadVobDictFromFS(GlobSpec)
                #listVobDict(vobDictFromFS)
                listDict(dictFromFS)

            else:
                #listFromSS=loadVobListFromInFile(InFile, True)
                dictFromSS=loadVobDictFromSS(InFile, skipList)
                #loadVobListFromInFile(InFile, True)
                #dictFromFS=loadVobDictFromFS('/vobs/*')
                listDict(dictFromSS)

        elif Action.lower() == 'reconcile':
            reconcileVobs(GlobSpec, InFile)

        else:
            logging.error('Invalid action %s' % Action)

if __name__ == "__main__":
    main()
