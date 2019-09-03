# ian.heywood@physics.ox.ac.uk


import sys
import pickle
import time
import shutil


def stamp():
    return str(time.time()).replace('.','')


project_info = pickle.load(open('project_info.p','rb'))
ref_ant = project_info['ref_ant']
targets = project_info['target_list'] 

myuvrange = '>150m'

myms = sys.argv[3]

for target in targets:
    if target[2] == myms:
        target_name = target[0]


clearstat()
clearstat()


code = target_name[-3:]


gtab = 'cal_'+myms+'_'+target_name+'_'+stamp()+'.GP0'


gaincal(vis=myms,
    field='0',
    uvrange=myuvrange,
    caltable=gtab,
    refant = str(ref_ant),
    solint='128s',
    solnorm=False,
    combine='',
    minsnr=3,
    calmode='p',
    parang=False,
    gaintable=[],
    gainfield=[],
    interp=[],
    append=False)


applycal(vis=myms,
    gaintable=[gtab],
    field='0',
    calwt=False,
    parang=False,
    applymode='calonly',
    gainfield='0',
    interp = ['nearest'])


statwt(vis=myms,
    field='0')


clearstat()
clearstat()


