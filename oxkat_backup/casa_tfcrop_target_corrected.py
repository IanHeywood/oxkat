# ian.heywood@physics.ox.ac.uk


import pickle
import numpy


project_info = pickle.load(open('project_info.p','rb'))
targets = project_info['target_list'] 


myms = project_info['master_ms']

for target in targets:
	flagdata(vis=myms,mode='tfcrop',datacolumn='corrected',field=target[1])
