# ian.heywood@physics.ox.ac.uk


import pickle


project_info = pickle.load(open('project_info.p','rb'))
myms = project_info['master_ms']
targets = project_info['target_list'] 


clearstat()
clearstat()


for target in targets:
	flagdata(vis=myms,mode='tfcrop',datacolumn='corrected',field=target[1])


flagmanager(vis=myms,mode='save',versionname='tfcrop_targets')


clearstat()
clearstat()
