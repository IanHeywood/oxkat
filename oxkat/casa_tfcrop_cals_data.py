# ian.heywood@physics.ox.ac.uk


import pickle


project_info = pickle.load(open('project_info.p','rb'))
myms = project_info['master_ms']
bpcal = project_info['primary']
pcal = project_info['secondary']


flagdata(vis=myms,mode='tfcrop',datacolumn='data',field=bpcal[1])
flagdata(vis=myms,mode='tfcrop',datacolumn='data',field=pcal[1])


flagmanager(vis=myms,mode='save',versionname='tfcrop_cals_data')