#!/usr/bin/python

import os
import sys
import logging
import re
import subprocess
import subprocess

sys.path.append('./')
import constants as c

def auditBranches(**args):

    logger = logging.getLogger()

    vobDict=args['vobDict']

    for vob in vobDict:
       logger.debug('collecting data on branches in %s since %s' % 
            (vob, vobDict[vob]['history_to_migrate']))         


    sys.exit(0)
    

def branchesSince(**args):

    logger = logging.getLogger()

    vob=args['vob']
    sinceDate=args['since']

    inFile=args['infile']
    #if 'infile' in args:
    if inFile:
        inFile=args['infile']
        logger.debug('loading versions from %s' % inFile)
        f = open(inFile, 'r')
        if f:
            contents=f.read()
            f.close()
            branchList=parseBranches(vob=vob, versionListing=contents)
        else:
            logger.error('problems opening %s' % inFile)

    else:

        ccom='%s find %s -version "created_since(%s)" -print ' % (c.Cleartool, vob, sinceDate)

        logger.debug('running find command: %s' % ccom)

        process=subprocess.Popen(ccom, 
            shell=True, 
            executable=c.Shell, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE)

        (out, err)=process.communicate()

        sts=process.poll()

        if sts==0:
            #logger.debug('desc command was successful -- now parsing stdout.')
            #logger.debug('parsing /%s/' % out)
            branchList=parseBranches(vob=vob, versionListing=out)

    branchList.sort()
    for branch in branchList:
        print "%s" % (branch) 

    return branchList 

def parseBranches(**args):

    rval = []
    logger = logging.getLogger()
    branchDict={}

    vob=args['vob']
    versionListing=args['versionListing']

    pattobj = re.compile( r'.*@@/main/(.*)/(?:\d+|CHECKEDOUT)$') 

    #pattobj = re.compile( r'(.*)$') 

    lines=versionListing.split('\n')
    for line in lines:
        matchobj=pattobj.match(line)

        if matchobj:
            branchString=matchobj.group(1)
            branchList=branchString.split('/')
            for branch in branchList:
                if branch in branchDict:
                    branchDict[branch]+=1
                else:
                    branchDict[branch]=1
                #branchDict[branch]=descBranch(vob=vob, branch=branch)
                #logger.debug('branch parsed=%s' %  matchobj.group(1))
        else:
            logger.info('skipping %s' % line)

    logger.debug("branches parsed...")
    logger.debug(branchDict)

    for branch in branchDict:
        branchDict[branch]=descBranch(vob=vob, branch=branch, versions=branchDict[branch])
        print branchDict[branch]
        rval.append(branch)

    return rval

def descBranch(**args):

    logger = logging.getLogger()

    # initialize the return value dictionary in case parsing fails
    rval=dict(created_date='',
         created_username='',
         owner='',
         group='',
         comment='')

    vob=args['vob']
    branch=args['branch']
    versions=args['versions']

    curDir=os.getcwd()
    os.chdir(vob)

    ccom='%s desc -fmt "%%Sd|%%u|%%Gu|%%Nc" brtype:%s' % (c.Cleartool, branch)

    logger.debug('running command: %s' % ccom)

    process=subprocess.Popen(ccom, 
        shell=True, 
        executable=c.Shell, 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE)

    (out, err)=process.communicate()

    sts=process.poll()

    os.chdir(curDir)

    if sts==0:
        logger.debug('desc command was successful -- now parsing stdout.')
        logger.debug('parsing /%s/' % out)

        # sample of what will be parsed
        # 2002-11-05|crew_scm|cip|This branch is created on latest element version of core in vobs:
        # /vobs/acrew_core   and    /vobs/acrew_pair
        # as of Tuesday 05 November 2002. This branch is primarily made for clients:
        # CI...China Air   VH...Aeropostal   DJ...Virgin Blue

        pattobj = re.compile( r'([^|]*)\|' # created_date
                              r'([^|]*)\|' # owner 
                              r'([^|]*)\|' # group 
                              r'([^|]*)'   # comment 
                             )

        matchobj=pattobj.match(out)

        if matchobj:

                logger.debug('match successful')

                logger.debug('vob: [%s]' % vob)
                logger.debug('created_date: [%s]' % matchobj.group(1))
                logger.debug('versions: [%s]' % versions)
                logger.debug('owner: [%s]' % matchobj.group(2))
                logger.debug('group: [%s]' % matchobj.group(3))
                logger.debug('comment: [%s]' % matchobj.group(4))

                rval=dict(vob=vob,
                    created_date=matchobj.group(1),
                    versions=versions,
                    owner=matchobj.group(2),
                    group=matchobj.group(3),
                    comment=matchobj.group(4))

        else:
            logger.warn('desc parsing regex failed for vob: %s' % vob)
    else:
        logger.warn('command failed due to: %s' % (err))

    return rval
