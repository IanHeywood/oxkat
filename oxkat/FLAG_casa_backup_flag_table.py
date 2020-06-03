# ian.heywood@physics.ox.ac.uk
# 
# set versionname=... on command line call to CASA
# can also specify csv mslist=...,... otherwise project_info.p will be
# used and the operation will proceed on all available target Measurement Sets.
#
# versionname must be supplied
#

import os
import sys


execfile('oxkat/casa_read_project_info.py')


mslist = False

args = sys.argv
for item in sys.argv:
    parts = item.split('=')
    if parts[0] == 'versionname':
        versionname = parts[1]
    if parts[0] == 'mslist':
        mslist = parts[1].split(',')


if not mslist:
    mslist = []
    for targ in target_ms:
        mslist.append(targ)


for myms in mslist:
    if os.path.isdir(myms):
        flagmanager(vis=myms,
            mode='save',
            versionname=versionname)
    else:
        print(myms+' not found')
