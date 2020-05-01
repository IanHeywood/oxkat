# ian.heywood@physics.ox.ac.uk
# 
# set versionname=... on command line call to CASA
# can also specify csv mslist=...,... otherwise project_info.p will be relied upon
#


import pickle
import sys

mslist = False

args = sys.argv
for item in sys.argv:
    parts = item.split('=')
    if parts[0] == 'versionname':
        versionname = parts[1]
    if parts[0] == 'mslist':
        mslist = parts[1].split(',')


if not mslist:
    project_info = pickle.load(open('project_info.p','rb'))
    targets = project_info['target_list'] 
    mslist = []
    for targ in targets:
        mslist.append(targ[2])


for myms in mslist:
    flagmanager(vis=myms,
        mode='restore',
        versionname=versionname)
