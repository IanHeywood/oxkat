# ian.heywood@physics.ox.ac.uk


import pickle


with open('project_info.p','rb') as f:
    project_info = pickle.load(f,encoding='latin1')
#project_info = pickle.load(open('project_info.p','rb'))


myms = project_info['master_ms']
targets = project_info['target_list'] 


clearstat()
clearstat()


for target in targets:
    flagdata(vis=myms,mode='tfcrop',datacolumn='corrected',field=target[1])


flagmanager(vis=myms,mode='save',versionname='tfcrop_targets')


clearstat()
clearstat()
