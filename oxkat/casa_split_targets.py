# ian.heywood@physics.ox.ac.uk


import pickle


project_info = pickle.load(open('project_info.p','rb'))


myms = project_info['master_ms']
targets = project_info['target_list'] 


for targ in targets:
    target = targ[1]
    opms = targ[2]

    mstransform(vis=myms,outputvis=opms,field=target,usewtspectrum=True,datacolumn='corrected')