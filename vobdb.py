#!/usr/bin/python

import xlrd
import xlwt
import logging

def loadVobDictFromVobsTab(ss, skipList):

    logger = logging.getLogger()

    book = xlrd.open_workbook(ss)

    #print "The number of worksheets is", book.nsheets
    #print "Worksheet name(s):", book.sheet_names()

    sh = book.sheet_by_index(0)
    #print sh.name, sh.nrows, sh.ncols
    #print "Cell D30 is", sh.cell_value(rowx=29, colx=3)

    #[text:u'/vobs/spie           ', 
    #text:u' PDvob01', 
    #text:u'James Calvert', 
    #text:u'Scott Lindquist', 
    #text:u'YES', 
    #text:u'YES', 
    #text:u'YES', 
    #text:u'YES', 
    #text:u'SVN', 
    #text:u'Lock & Unmount']

    vobs={}
    for rx in range(1, sh.nrows):

        if sh.row(rx)[0].value.rstrip() in skipList:
            logger.debug("Skipping %s because it's in the skip list" %
                sh.row(rx)[0].value.rstrip())
        else: 
            vobs[sh.row(rx)[0].value.rstrip()]=dict(
                loc=sh.row(rx)[1].value.rstrip(),
                contact1=sh.row(rx)[2].value.rstrip(),
                contact2=sh.row(rx)[3].value.rstrip(),
                empty=sh.row(rx)[4].value.rstrip(),
                migrated=sh.row(rx)[5].value.rstrip(),
                mounted=sh.row(rx)[6].value.rstrip(),
                to_be_locked=sh.row(rx)[7].value.rstrip(),
                locked=sh.row(rx)[8].value.rstrip(),
                target_vcs=sh.row(rx)[9].value.rstrip(),
                comment=sh.row(rx)[10].value.rstrip(),
                prev_owner_username=sh.row(rx)[11].value.rstrip(),
                prev_owner_email=sh.row(rx)[12].value.rstrip(),
                prev_group=sh.row(rx)[13].value.rstrip(),
                owner=sh.row(rx)[14].value.rstrip(),
                group=sh.row(rx)[15].value.rstrip(),
                created_username=sh.row(rx)[16].value.rstrip(),
                created_email=sh.row(rx)[17].value.rstrip(),
                created_date=sh.row(rx)[18].value.rstrip(),
                storage_loc=sh.row(rx)[19].value.rstrip(),
                storage_global_loc=sh.row(rx)[20].value.rstrip(),
                last_mod_date=sh.row(rx)[21].value.rstrip(),
                last_mod_username=sh.row(rx)[22].value.rstrip(),
                last_mod_email=sh.row(rx)[23].value.rstrip(),
                history_to_migrate=xlDateAsText(sh.row(rx)[24].value, book))

            #vobs[sh.row(rx)[0].value.rstrip()]['history_to_migrate']='2012-11-01'

    return vobs

def xlDateAsText(xldate, book):

    year, month, day, hour, minute, second = xldate_as_tuple(xldate, book.datemode)

    rval='(%s-%s-%s)' % (year, month, day)

    return rval


def loadBranchDictFromBranchesTab(ss, skipList):

    logger = logging.getLogger()

    book = xlrd.open_workbook(ss)

    sh = book.sheet_by_index(1)

    branches={}
    for rx in range(1, sh.nrows):

        if sh.row(rx)[0].value.rstrip() in skipList:
            logger.debug("Skipping %s because it's in the skip list" %
                sh.row(rx)[0].value.rstrip())
        else: 
            branches[sh.row(rx)[0].value.rstrip()]=dict(
                vob=sh.row(rx)[1].value.rstrip(),
                branch=sh.row(rx)[2].value.rstrip(),
                created_date=sh.row(rx)[3].value.rstrip(),
                num_versions=sh.row(rx)[4].value.rstrip(),
                owner=sh.row(rx)[5].value.rstrip(),
                group=sh.row(rx)[6].value.rstrip(),
                comment=sh.row(rx)[7].value.rstrip(),
                to_be_migrated=sh.row(rx)[8].value.rstrip())

    return vobs

def loadVobListFromVobsTab(ss, skipList):

    vobDict=loadVobDictFromVobsTab(ss, skipList)

    vobList = []
    for vob in vobDict:
        #print "%s: %s: %s" % (vob, vobDict[vob]['owner'], vobDict[vob]['locked'])
        #print vob 
        vobList.append(vob)

    return vobList

def writeVobsTab(fileName, vobDict):

    style0 = xlwt.easyxf('font: name Calibri, bold on',
        num_format_str='#,##0.00')

    style1 = xlwt.easyxf('font: name Calibri', 
        num_format_str='#,##0.00')

    style3 = xlwt.easyxf(num_format_str='D-MMM-YY')

    wb = xlwt.Workbook()
    ws = wb.add_sheet('vobs')

    ws.write(0, 0, 'vob', style0)
    ws.write(0, 1, 'loc', style0)
    ws.write(0, 2, 'contact1', style0)
    ws.write(0, 3, 'contact2', style0)
    ws.write(0, 4, 'empty', style0)
    ws.write(0, 5, 'migrated', style0)
    ws.write(0, 6, 'mounted', style0)
    ws.write(0, 7, 'to_be_locked', style0)
    ws.write(0, 8, 'locked', style0)
    ws.write(0, 9, 'target_vcs', style0)
    ws.write(0, 10, 'comment', style0)
    ws.write(0, 11, 'prev_owner_username', style0)
    ws.write(0, 12, 'prev_owner_email', style0)
    ws.write(0, 13, 'prev_group', style0)
    ws.write(0, 14, 'owner', style0)
    ws.write(0, 15, 'group', style0)
    ws.write(0, 16, 'created_username', style0)
    ws.write(0, 17, 'created_email', style0)
    ws.write(0, 18, 'created_date', style0)
    ws.write(0, 19, 'storage_loc', style0)
    ws.write(0, 20, 'storage_global_loc', style0)
    ws.write(0, 21, 'last_mod_date', style0)
    ws.write(0, 22, 'last_mod_username', style0)
    ws.write(0, 23, 'last_mod_email', style0)
    ws.write(0, 24, 'history_to_migrate', style0)

    row=0
    for vob in vobDict:
        row=row+1
        ws.write(row, 0, vob, style1)
        ws.write(row, 1, vobDict[vob]['loc'], style1)
        ws.write(row, 2, vobDict[vob]['contact1'], style1)
        ws.write(row, 3, vobDict[vob]['contact2'], style1)
        ws.write(row, 4, vobDict[vob]['empty'], style1)
        ws.write(row, 5, vobDict[vob]['migrated'], style1)
        ws.write(row, 6, vobDict[vob]['mounted'], style1)
        ws.write(row, 7, vobDict[vob]['to_be_locked'], style1)
        ws.write(row, 8, vobDict[vob]['locked'], style1)
        ws.write(row, 9, vobDict[vob]['target_vcs'], style1)
        ws.write(row, 10, vobDict[vob]['comment'], style1)
        ws.write(row, 11, vobDict[vob]['prev_owner_username'], style1)
        ws.write(row, 12, vobDict[vob]['prev_owner_email'], style1)
        ws.write(row, 13, vobDict[vob]['prev_group'], style1)
        ws.write(row, 14, vobDict[vob]['owner'], style1)
        ws.write(row, 15, vobDict[vob]['group'], style1)
        ws.write(row, 16, vobDict[vob]['created_username'], style1)
        ws.write(row, 17, vobDict[vob]['created_email'], style1)
        ws.write(row, 18, vobDict[vob]['created_date'], style1)
        ws.write(row, 19, vobDict[vob]['storage_loc'], style1)
        ws.write(row, 20, vobDict[vob]['storage_global_loc'], style1)
        ws.write(row, 21, vobDict[vob]['last_mod_date'], style1)
        ws.write(row, 22, vobDict[vob]['last_mod_username'], style1)
        ws.write(row, 23, vobDict[vob]['last_mod_email'], style1)
        ws.write(row, 24, vobDict[vob]['history_to_migrate'], style1)

    #ws.write(1, 0, datetime.now(), style1)
    #ws.write(2, 0, 1)
    #ws.write(2, 1, 1)
    #ws.write(2, 2, xlwt.Formula("A3+B3"))

    wb.save(fileName)

def writeBranchesTab(fileName, branchDict):

    style0 = xlwt.easyxf('font: name Calibri, bold on',
        num_format_str='#,##0.00')

    style1 = xlwt.easyxf('font: name Calibri', 
        num_format_str='#,##0.00')

    style3 = xlwt.easyxf(num_format_str='D-MMM-YY')

    wb = xlwt.Workbook()
    ws = wb.add_sheet('vobs')

    ws.write(0, 0, 'vob', style0)
    ws.write(0, 1, 'branch', style0)
    ws.write(0, 2, 'created_date', style0)
    ws.write(0, 3, 'num_versions', style0)
    ws.write(0, 4, 'owner', style0)
    ws.write(0, 5, 'group', style0)
    ws.write(0, 6, 'comment', style0)
    ws.write(0, 7, 'to_be_migrated', style0)

    row=0
    for branch in branchDict:
        row=row+1
        ws.write(row, 0, branchDict[branch], style1)
        ws.write(row, 1, vob, style1)
        ws.write(row, 2, branchDict[branch]['created_date'], style1)
        ws.write(row, 3, branchDict[branch]['num_versions'], style1)
        ws.write(row, 4, branchDict[branch]['owner'], style1)
        ws.write(row, 5, branchDict[branch]['group'], style1)
        ws.write(row, 6, branchDict[branch]['comment'], style1)
        ws.write(row, 7, branchDict[branch]['to_be_migrated'], style1)

    wb.save(fileName)
