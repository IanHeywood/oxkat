# ian.heywood@physics.ox.ac.uk


import glob
import shutil
import time


execfile('oxkat/casa_read_project_info.py')
execfile('oxkat/config.py')



def stamp():
    now = str(datetime.datetime.now()).replace(' ','-').replace(':','-').split('.')[0]
    return now
    

# ------- Parameters


myuvrange = CAL_1GC_UVRANGE
delaycut = CAL_1GC_DELAYCUT
gapfill = CAL_1GC_FILLGAPS



# ------- Setup names


tt = stamp()


ktab0 = GAINTABLES+'/cal_1GC_'+myms+'_'+tt+'.K0'
bptab0 = GAINTABLES+'/cal_1GC_'+myms+'_'+tt+'.B0'
gtab0 = GAINTABLES+'/cal_1GC_'+myms+'_'+tt+'.G0'


ktab1 = GAINTABLES+'/cal_1GC_'+myms+'_'+tt+'.K1'
bptab1 = GAINTABLES+'/cal_1GC_'+myms+'_'+tt+'.B1'
gtab1 = GAINTABLES+'/cal_1GC_'+myms+'_'+tt+'.G1'


ktab2 = GAINTABLES+'/cal_1GC_'+myms+'_'+tt+'.K2'
gtab2 = GAINTABLES+'/cal_1GC_'+myms+'_'+tt+'.G2'
ftab2 = GAINTABLES+'/cal_1GC_'+myms+'_'+tt+'.flux2'


ktab3 = GAINTABLES+'/cal_1GC_'+myms+'_'+tt+'.K3'
gtab3 = GAINTABLES+'/cal_1GC_'+myms+'_'+tt+'.G3'
ftab3 = GAINTABLES+'/cal_1GC_'+myms+'_'+tt+'.flux3'





# --------------------------------------------------------------- #
# --------------------------------------------------------------- #
# --------------------------- STAGE 0 --------------------------- #
# --------------------------------------------------------------- #
# --------------------------------------------------------------- #



# ------- Setup models


if primary_tag == '1934':
    setjy(vis=myms,
        field=bpcal,
        standard='Perley-Butler 2010',
        scalebychan=True,
        usescratch=True)
    
    
elif primary_tag == '0408':
    bpcal_mod = ([17.066,0.0,0.0,0.0],[-1.179],'1284MHz')
    setjy(vis=myms,
        field=bpcal,
        standard='manual',
        fluxdensity=bpcal_mod[0],
        spix=bpcal_mod[1],
        reffreq=bpcal_mod[2],
        scalebychan=True,
        usescratch=True)


elif primary_tag == 'other':
    setjy(vis=myms,
        field=bpcal_name,
        standard='Perley-Butler 2013',
        scalebychan=True,
        usescratch=True)
    

# ------- K0 (primary)


gaincal(vis=myms,
    field=bpcal,
    #uvrange=myuvrange,
    caltable=ktab0,
    refant = str(ref_ant),
    gaintype = 'K',
    solint = 'inf',
    parang=False)


# ------- G0 (primary; apply K0)


gaincal(vis=myms,
    field=bpcal,
    uvrange=myuvrange,
    caltable=gtab0,
    gaintype='G',
    solint='inf',
    calmode='p',
    minsnr=5,
    gainfield=[bpcal],
    interp = ['nearest'],
    gaintable=[ktab0])


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
    fillgaps=gapfill,
    parang=False,
    gainfield=[bpcal,bpcal],
    interp = ['nearest','nearest'],
    gaintable=[ktab0,gtab0])


flagdata(vis=bptab0,mode='tfcrop',datacolumn='CPARAM')
flagdata(vis=bptab0,mode='rflag',datacolumn='CPARAM')


# ------- Correct primary data with K0,B0,G0


applycal(vis=myms,
    gaintable=[ktab0,gtab0,bptab0],
#    applymode='calonly',
    field=bpcal,
#    calwt=False,
    parang=False,
    gainfield=[bpcal,bpcal,bpcal],
    interp = ['nearest','nearest','nearest'])


# ------- Flag primary on CORRECTED_DATA - MODEL_DATA


flagdata(vis=myms,
    mode='rflag',
    datacolumn='residual',
    field=bpcal)


flagdata(vis=myms,
    mode='tfcrop',
    datacolumn='residual',
    field=bpcal)

if SAVE_FLAGS:
    flagmanager(vis=myms,
        mode='save',
        versionname='bpcal_residual_flags')


# --------------------------------------------------------------- #
# --------------------------------------------------------------- #
# --------------------------- STAGE 1 --------------------------- #
# --------------------------------------------------------------- #
# --------------------------------------------------------------- #


# ------- K1 (primary; apply B0, G0)


gaincal(vis=myms,
    field=bpcal,
    #uvrange=myuvrange,
    caltable=ktab1,
    refant = str(ref_ant),
    gaintype = 'K',
    solint = 'inf',
    parang=False,
    gaintable=[bptab0,gtab0],
    gainfield=[bpcal,bpcal],
    interp=['nearest','nearest'])


# ------- G1 (primary; apply K1,B0)


gaincal(vis=myms,
    field=bpcal,
    uvrange=myuvrange,
    caltable=gtab1,
    gaintype='G',
    solint='inf',
    calmode='p',
    minsnr=5,
    gainfield=[bpcal,bpcal],
    interp = ['nearest','nearest'],
    gaintable=[ktab1,bptab0])


# ------- B1 (primary; apply K1, G1)


bandpass(vis=myms,
    field=bpcal,
    uvrange=myuvrange,
    caltable=bptab1,
    refant = str(ref_ant),
    solint='inf',
    combine='',
    solnorm=False,
    minblperant=4,
    minsnr=3.0,
    bandtype='B',
    fillgaps=gapfill,
    parang=False,
    gainfield=[bpcal,bpcal],
    interp = ['nearest','nearest'],
    gaintable=[ktab1,gtab1])


flagdata(vis=bptab1,mode='tfcrop',datacolumn='CPARAM')
flagdata(vis=bptab1,mode='rflag',datacolumn='CPARAM')


# ------- Correct primary data with K1,G1,B1


applycal(vis=myms,
    gaintable=[ktab1,gtab1,bptab1],
#    applymode='calonly',
    field=bpcal,
#    calwt=False,
    parang=False,
    gainfield=[bpcal,bpcal,bpcal],
    interp = ['nearest','nearest','nearest'])


# --------------------------------------------------------------- #
# --------------------------------------------------------------- #
# --------------------------- STAGE 2 --------------------------- #
# --------------------------------------------------------------- #
# --------------------------------------------------------------- #


# ------- G2 (primary; a&p sols per scan / SPW)


gaincal(vis = myms,
    field = bpcal,
    uvrange = myuvrange,
    caltable = gtab2,
    refant = str(ref_ant),
    solint = 'inf',
    solnorm = False,
    combine = '',
    minsnr = 3,
    calmode = 'ap',
    parang = False,
    gaintable = [ktab1,gtab1,bptab1],
    gainfield = [bpcal,bpcal,bpcal],
    interp = ['nearest','nearest','nearest'],
    append = False)


# ------- Apply final tables to targets


for i in range(0,len(targets)):


    target = targets[i]
    related_pcal = target_cal_map[i]


    # --- Correct targets with K3, G1, B1, G3


    applycal(vis=myms,
        gaintable=[ktab1,gtab1,bptab1,gtab2],
#        applymode='calonly',
        field=target,
#        calwt=False,
        parang=False,
        gainfield=[bpcal,bpcal,bpcal,bpcal],
        interp=['nearest','linear','linear','linear'])


if SAVE_FLAGS:
    flagmanager(vis=myms,mode='save',versionname='refcal-full')
