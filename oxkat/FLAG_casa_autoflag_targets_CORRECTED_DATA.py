# ian.heywood@physics.ox.ac.uk


import json


with open('project_info.json') as f:
    project_info = json.load(f)


myms = project_info['master_ms']
targets = project_info['target_list'] 


clearstat()
clearstat()


for target in targets:
    flagdata(vis=myms,mode='rflag',datacolumn='corrected',field=target[1])
    flagdata(vis=myms,mode='tfcrop',datacolumn='corrected',field=target[1])
    flagdata(vis=myms,mode='extend',growtime=90.0,growfreq=90.0,growaround=True,flagneartime=True,flagnearfreq=True,field=target[1])


if SAVE_FLAGS:
    flagmanager(vis=myms,mode='save',versionname='tfcrop_targets')


clearstat()
clearstat()
