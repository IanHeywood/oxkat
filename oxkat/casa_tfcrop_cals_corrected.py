# ian.heywood@physics.ox.ac.uk


import pickle


project_info = pickle.load(open('project_info.p','rb'))
bpcal = project_info['primary']
pcal = project_info['secondary']


myms = project_info['master_ms']


flagdata(vis=myms,mode='tfcrop',datacolumn='corrected',field=bpcal[1])
flagdata(vis=myms,mode='tfcrop',datacolumn='corrected',field=pcal[1])


flagmanager(vis=myms,mode='save',versionname='tfcrop_cals')