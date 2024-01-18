# ian.heywood@physics.ox.ac.uk


import glob
import shutil
import time


execfile('oxkat/casa_read_project_info.py')
execfile('oxkat/config.py')

if PRE_FIELDS != '':
    targets = user_targets
    pcals = user_pcals
    target_cal_map = user_cal_map

def stamp():
    now = str(datetime.datetime.now()).replace(' ','-').replace(':','-').split('.')[0]
    return now
    

# ------- Parameters


gapfill = CAL_1GC_FILLGAPS
myuvrange = CAL_1GC_UVRANGE 
myspw = CAL_1GC_FREQRANGE


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



# ------- Set calibrator models



if primary_tag == '1934':
    setjy(vis=myms,
        field=bpcal_name,
        standard='Stevens-Reynolds 2016',
        scalebychan=True,
        usescratch=True)
    
    
elif primary_tag == '0408':
    bpcal_mod = CAL_1GC_0408_MODEL
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
        standard='Perley-Butler 2013',
        scalebychan=True,
        usescratch=True)


for i in range(0,len(pcals)):
    pcal = pcals[i]
    setjy(vis =myms,
        field = pcal,
        standard = 'manual',
        fluxdensity = [1.0,0,0,0],
        reffreq = '1000MHz',
        usescratch = True)


# --------------------------------------------------------------- #
# --------------------------------------------------------------- #
# --------------------------- STAGE 0 --------------------------- #
# --------------------------------------------------------------- #
# --------------------------------------------------------------- #


# ------- K0 (primary)


gaincal(vis=myms,
    field=bpcal_name,
    #uvrange=myuvrange,
    #spw=myspw,
    caltable=ktab0,
    refant = str(ref_ant),
    gaintype = 'K',
    solint = 'inf',
    parang=False)


# ------- G0 (primary; apply K0)


gaincal(vis=myms,
    field=bpcal_name,
    uvrange=myuvrange,
    caltable=gtab0,
    gaintype='G',
    solint='inf',
    calmode='p',
    minsnr=5,
    gainfield=[bpcal_name],
    interp = ['nearest'],
    gaintable=[ktab0])


# ------- B0 (primary; apply K0, G0)


bandpass(vis=myms,
    field=bpcal_name, 
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
    gainfield=[bpcal_name,bpcal_name],
    interp = ['nearest','nearest'],
    gaintable=[ktab0,gtab0])


flagdata(vis=bptab0,mode='tfcrop',datacolumn='CPARAM')
flagdata(vis=bptab0,mode='rflag',datacolumn='CPARAM')


# ------- Correct primary data with K0,B0,G0


applycal(vis=myms,
    gaintable=[ktab0,gtab0,bptab0],
#    applymode='calonly',
    field=bpcal_name,
#    calwt=False,
    parang=False,
    gainfield=[bpcal_name,bpcal_name,bpcal_name],
    interp = ['nearest','nearest','nearest'])


# ------- Flag primary on CORRECTED_DATA - MODEL_DATA


flagdata(vis=myms,
    mode='rflag',
    datacolumn='residual',
    field=bpcal_name)


flagdata(vis=myms,
    mode='tfcrop',
    datacolumn='residual',
    field=bpcal_name)

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
    field=bpcal_name,
    caltable=ktab1,
    refant = str(ref_ant),
    gaintype = 'K',
    solint = 'inf',
    parang=False,
    gaintable=[bptab0,gtab0],
    gainfield=[bpcal_name,bpcal_name],
    interp=['nearest','nearest'])


# ------- G1 (primary; apply K1,B0)


gaincal(vis=myms,
    field=bpcal_name,
    uvrange=myuvrange,
    caltable=gtab1,
    gaintype='G',
    solint='inf',
    calmode='p',
    minsnr=5,
    gainfield=[bpcal_name,bpcal_name],
    interp = ['nearest','nearest'],
    gaintable=[ktab1,bptab0])


# ------- B1 (primary; apply K1, G1)


bandpass(vis=myms,
    field=bpcal_name,
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
    gainfield=[bpcal_name,bpcal_name],
    interp = ['nearest','nearest'],
    gaintable=[ktab1,gtab1])


flagdata(vis=bptab1,mode='tfcrop',datacolumn='CPARAM')
flagdata(vis=bptab1,mode='rflag',datacolumn='CPARAM')


# ------- Correct primary data with K1,G1,B1


applycal(vis=myms,
    gaintable=[ktab1,gtab1,bptab1],
#    applymode='calonly',
    field=bpcal_name,
#    calwt=False,
    parang=False,
    gainfield=[bpcal_name,bpcal_name,bpcal_name],
    interp = ['nearest','nearest','nearest'])


# --------------------------------------------------------------- #
# --------------------------------------------------------------- #
# --------------------------- STAGE 2 --------------------------- #
# --------------------------------------------------------------- #
# --------------------------------------------------------------- #


# ------- G2 (primary; a&p sols per scan / SPW)


gaincal(vis = myms,
    field = bpcal_name,
    uvrange = myuvrange,
    spw = myspw,
    caltable = gtab2,
    refant = str(ref_ant),
    solint = 'inf',
    solnorm = False,
    gaintype = 'T',
    combine = '',
    minsnr = 3,
    calmode = 'ap',
    parang = False,
    gaintable = [ktab1,gtab1,bptab1],
    gainfield = [bpcal_name,bpcal_name,bpcal_name],
    interp = ['nearest','nearest','nearest'],
    append = False)


# ------- Duplicate K1

shutil.copytree(ktab1,ktab2)

# ------- Looping over secondaries


for i in range(0,len(pcals)):


    pcal = pcals[i]


    # --- G2 (secondary)


    gaincal(vis = myms,
        field = pcal,
        uvrange = myuvrange,
        spw = myspw,
        caltable = gtab2,     
        refant = str(ref_ant),
        minblperant = 4,
        minsnr = 3,
        solint = 'inf',
        solnorm = False,
        gaintype = 'T',
        combine = '',
        calmode = 'ap',
        parang = False,
        gaintable=[ktab1,gtab1,bptab1],
        gainfield=[bpcal_name,bpcal_name,bpcal_name],
        interp=['nearest','linear','linear'],
        append=True)


    # --- K2 (secondary)


    gaincal(vis= myms,
        field = pcal,
    #   uvrange = myuvrange,
    #   spw=myspw,
        caltable = ktab2,
        refant = str(ref_ant),
        gaintype = 'K',
        solint = 'inf',
        parang = False,
        gaintable = [gtab1,bptab1,gtab2],
        gainfield = [bpcal_name,bpcal_name,pcal],
        interp = ['nearest','linear','linear'],
        append = True)


# --- F2 


fluxscale(vis=myms,
    caltable = gtab2,
    fluxtable = ftab2,
    reference = bpcal_name,
    append = False,
    transfer = '')


# ------- Looping over secondaries


for i in range(0,len(pcals)):


    pcal = pcals[i]


    # --- Correct secondaries with K2, G1, B1, F2


    applycal(vis = myms,
        gaintable = [ktab2,gtab1,bptab1,ftab2],
#        applymode='calonly',
        field = pcal,
#        calwt = False,
        parang = False,
        gainfield = ['','',bpcal_name,pcal],
        interp = ['nearest','linear','linear','linear'])


    # --- Flag secondaries on CORRECTED_DATA - MODEL_DATA


    flagdata(vis = myms,
        field = pcal,
        mode = 'rflag',
        datacolumn = 'residual')


    flagdata(vis = myms,
        field = pcal,
        mode = 'tfcrop',
        datacolumn = 'residual')

if SAVE_FLAGS:
    flagmanager(vis=myms,mode='save',versionname='pcal_residual_flags')


# --------------------------------------------------------------- #
# --------------------------------------------------------------- #
# --------------------------- STAGE 3 --------------------------- #
# --------------------------------------------------------------- #
# --------------------------------------------------------------- #


gaincal(vis = myms,
    field = bpcal_name,
    uvrange = myuvrange,
    spw = myspw,
    caltable = gtab3,
    refant = str(ref_ant),
    solint = 'inf',
    solnorm = False,
    gaintype = 'T',
    combine = '',
    minsnr = 3,
    calmode = 'ap',
    parang = False,
    gaintable = [ktab2,gtab1,bptab1],
    gainfield = [bpcal_name,bpcal_name,bpcal_name],
    interp = ['nearest','nearest','nearest'],
    append = False)


# ------- Duplicate K1 table


shutil.copytree(ktab1,ktab3)


# ------- Looping over secondaries


for i in range(0,len(pcals)):


    pcal = pcals[i]


    # --- G3 (secondary)


    gaincal(vis = myms,
        field = pcal,
        uvrange = myuvrange,
        spw = myspw,
        caltable = gtab3,     
        refant = str(ref_ant),
        minblperant = 4,
        minsnr = 3,
        solint = 'inf',
        solnorm = False,
        gaintype = 'T',
        combine = '',
        calmode = 'ap',
        parang = False,
        gaintable=[ktab2,gtab1,bptab1],
        gainfield=[bpcal_name,bpcal_name,bpcal_name],
        interp=['nearest','linear','linear'],
        append=True)


    # --- K3 secondary


    gaincal(vis= myms,
        field = pcal,
        caltable = ktab3,
        refant = str(ref_ant),
        gaintype = 'K',
        solint = 'inf',
        parang = False,
        gaintable = [gtab1,bptab1,gtab3],
        gainfield = [bpcal_name,bpcal_name,pcal],
        interp = ['linear','linear','linear'],
        append = True)


# --- F3 


fluxscale(vis=myms,
    caltable = gtab3,
    fluxtable = ftab3,
    reference = bpcal_name,
    append = False,
    transfer = pcals)


# ------- Apply final tables to secondaries


for i in range(0,len(pcals)):


    pcal = pcals[i]


    # --- Correct secondaries with K3, G1, B1, F3


    applycal(vis = myms,
        gaintable = [ktab3,gtab1,bptab1,ftab3],
#        applymode='calonly',
        field = pcal,
#        calwt = False,
        parang = False,
        gainfield = ['','',bpcal_name,pcal],
        interp = ['nearest','linear','linear','linear'])


# ------- Apply final tables to targets


for i in range(0,len(targets)):


    target = targets[i]
    related_pcal = target_cal_map[i]


    # --- Correct targets with K3, G1, B1, F3


    applycal(vis=myms,
        gaintable=[ktab3,gtab1,bptab1,ftab3],
#        applymode='calonly',
        field=target,
#        calwt=False,
        parang=False,
        gainfield=['',bpcal_name,bpcal_name,related_pcal],
        interp=['nearest','linear','linear','linear'])

if SAVE_FLAGS:
    flagmanager(vis=myms,mode='save',versionname='refcal-full')
