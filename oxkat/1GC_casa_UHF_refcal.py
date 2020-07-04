# ian.heywood@physics.ox.ac.uk
# Very experimental

import glob
import pickle
import shutil
import time


def stamp():
    return str(time.time()).replace('.','')


    

# ------- Parameters


myuvrange = '>300m'
myspw = '850~900MHz'


project_info = pickle.load(open('project_info.p','rb'))
myms = project_info['master_ms']
bpcal = project_info['primary'][0] # Using field names because targets will be removed
pcals = project_info['secondary']
primary_tag = project_info['primary_tag']
ref_ant = project_info['ref_ant']


# ------- Setup names


tt = stamp()


ktab0 = 'cal_'+myms+'_'+tt+'.K0'
bptab0 = 'cal_'+myms+'_'+tt+'.B0'
gtab0 = 'cal_'+myms+'_'+tt+'.G0'
gtab1 = 'cal_'+myms+'_'+tt+'.G1'
ftab1 = 'cal_'+myms+'_'+tt+'.flux'



# --------------------------------------------------------------- #
# --------------------------------------------------------------- #
# --------------------------- STAGE 0 --------------------------- #
# --------------------------------------------------------------- #
# --------------------------------------------------------------- #


# ------- Setup models


if primary_tag == '1934':
    setjy(vis=myms,
        field=bpcal_name,
        standard='Stevens-Reynolds 2016',
        scalebychan=True,
        usescratch=True)
    
    
elif primary_tag == '0408':
    bpcal_mod = ([17.066,0.0,0.0,0.0],[-1.179],'1284MHz')
    setjy(vis=myms,
        field=bpcal_name,
        standard='manual',
        fluxdensity=bpcal_mod[0],
        spix=bpcal_mod[1],
        reffreq=bpcal_mod[2],
        scalebychan=True,
        usescratch=True)


elif primary_tag == 'other':
    setjy(vis=myms,
        field=bpcal_name,
        standard='Perley-Butler 2010',
        scalebychan=True,
        usescratch=True)


# ------- K0 (primary)


gaincal(vis=myms,
    field=bpcal,
    #uvrange=myuvrange,
    spw=myspw,
    caltable=ktab0,
    refant = str(ref_ant),
    gaintype = 'K',
    solint = 'inf',
    parang=False)


# ------- G0 (primary; apply K0)


gaincal(vis=myms,
    field=bpcal,
    uvrange=myuvrange,
    spw=myspw,
    caltable=gtab0,
    gaintype='G',
    solint='inf',
    calmode='p',
    minsnr=5,
    gaintable=[ktab0],
    gainfield=[bpcal],
    interp=['nearest'])



# ------- B0 (primary; apply K0, G0)


bandpass(vis=myms,
    field=bpcal, 
    uvrange=myuvrange,
    caltable=bptab0,
    refant = str(ref_ant),
    solint='inf',
    combine='',
    solnorm=False,
    minblperant=4,
    minsnr=3.0,
    bandtype='B',
    fillgaps=64,
    parang=False,
    gainfield=[bpcal,bpcal],
    interp = ['nearest','nearest'],
#    spwmap = [[0,0,0,0,0,0,0,0],[]],
    gaintable=[ktab0,gtab0])




# ------- G1 (primary; a&p sols per scan / SPW)


gaincal(vis = myms,
    field = bpcal,
    uvrange = myuvrange,
    spw=myspw,
    caltable = gtab1,
    refant = str(ref_ant),
    solint = 'inf',
    solnorm = False,
    combine = '',
    minsnr = 3,
    calmode = 'ap',
    parang = False,
    gaintable = [ktab0,gtab0,bptab0],
    gainfield = [bpcal,bpcal,bpcal],
    interp = ['nearest','nearest','nearest'],
    append = False)



for i in range(0,len(pcals)):


    pcal = pcals[i][0] # Using field names


    # --- G2 (secondary)


    gaincal(vis = myms,
        field = pcal,
        uvrange = myuvrange,
        spw=myspw,
        caltable = gtab1,     
        refant = str(ref_ant),
        smodel = [1,0,0,0],
        minblperant = 4,
        minsnr = 3,
        solint = 'inf',
        solnorm = False,
        gaintype = 'G',
        combine = '',
        calmode = 'ap',
        parang = False,
        gaintable=[ktab0,gtab0,bptab0],
        gainfield=[bpcal,bpcal,bpcal],
        interp=['nearest','nearest','nearest'],
        append=True)


# ------- F2


fluxscale(vis=myms,
    caltable = gtab1,
    fluxtable = ftab1,
    reference = bpcal,
    append = False,
    transfer = '')


# ------- Apply final tables to secondaries


for i in range(0,len(pcals)):


    pcal = pcals[i][1]


    # --- Correct secondaries with K0, G0, B0, F1


    applycal(vis = myms,
        gaintable = [ktab0,gtab0,bptab0,ftab1],
        field = pcal,
        parang = False,
        gainfield = [bpcal,bpcal,bpcal,''],
        interp = ['nearest','linear','linear','linear'])


# ------- Apply final tables to targets


for targ in targets:

    target = targ[1]
    related_pcal = pcals[targ[3]][1]


    # --- Correct targets with K0, G0, B0, F1


    applycal(vis=myms,
        field=target,
        gaintable = [ktab0,gtab0,bptab0,ftab1],
        parang = False,
        gainfield = [bpcal,bpcal,bpcal,''],
        interp = ['nearest','linear','linear','linear'])



