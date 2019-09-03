# ian.heywood@physics.ox.ac.uk


import pickle
import time
import shutil


def stamp():
    return str(time.time()).replace('.','')


project_info = pickle.load(open('project_info.p','rb'))
myms = project_info['master_ms']
targets = project_info['target_list'] 


myuvrange = '>150m'


clearstat()
clearstat()


for target in targets:


    code = target[0][-3:]
    myms = target[2].rstrip('/')
    ref_ant = project_info['ref_ant']


    gtab = 'cal_'+myms+'_'+target[0]+'_'+stamp()+'.GP0'


    gaincal(vis=myms,
        field=target[1],
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
        field=target[1],
        calwt=False,
        parang=False,
        applymode='calonly',
        gainfield=[target[1]],
        interp = ['nearest'])


    statwt(vis=myms,
        field=target[1])


clearstat()
clearstat()


