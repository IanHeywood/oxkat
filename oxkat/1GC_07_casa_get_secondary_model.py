# ian.heywood@physics.ox.ac.uk


import glob
import pickle
import shutil
import time



execfile('oxkat/casa_read_project_info.py')
execfile('oxkat/config.py')


# def stamp():
#     return str(time.time()).replace('.','')


def stamp():
    now = str(datetime.datetime.now()).replace(' ','-').replace(':','-').split('.')[0]
    return now


def getfieldid(myms,field):
    tb.open(myms.rstrip('/')+'/FIELD')
    names = tb.getcol('NAME').tolist()
    for i in range(0,len(names)):
        if names[i] == field:
            idx = i
    return idx

    

# ------- Parameters


myuvrange = CAL_1GC_UVRANGE
gapfill = CAL_1GC_FILLGAPS

myms = glob.glob('*calibrators.ms')[0]



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


interim_pickle = GAINTABLES+'/secondary_models_interim_'+tt+'.p'
secondary_pickle = GAINTABLES+'/secondary_models_final_'+tt+'.p'


# --------------------------------------------------------------- #
# --------------------------------------------------------------- #
# --------------------------- STAGE 0 --------------------------- #
# --------------------------------------------------------------- #
# --------------------------------------------------------------- #


# ------- Setup models
# Now handled by separate scripts
# No need to repeat for calibrators MS as this is now split using 'all' columns,
# so MODEL_DATA should be copied and partitioned into SPWs also..

# if primary_tag == '1934':
#     setjy(vis=myms,
#         field=bpcal_name,
#         standard='Stevens-Reynolds 2016',
#         scalebychan=True,
#         usescratch=True)
    
    
# elif primary_tag == '0408':
#     bpcal_mod = ([17.066,0.0,0.0,0.0],[-1.179],'1284MHz')
#     setjy(vis=myms,
#         field=bpcal_name,
#         standard='manual',
#         fluxdensity=bpcal_mod[0],
#         spix=bpcal_mod[1],
#         reffreq=bpcal_mod[2],
#         scalebychan=True,
#         usescratch=True)


# elif primary_tag == 'other':
#     setjy(vis=myms,
#         field=bpcal_name,
#         standard='Perley-Butler 2010',
#         scalebychan=True,
#         usescratch=True)



# ------- G0 (primary)


gaincal(vis=myms,
    field=bpcal_name,
    uvrange=myuvrange,
    caltable=gtab0,
    gaintype='G',
    solint='inf',
    calmode='p',
    minsnr=5)
#     gainfield=[bpcal],
#     interp = ['nearest'],
# #    spwmap = [0,0,0,0,0,0,0,0],
#     gaintable=[ktab0])


# ------- B0 (primary; apply G0)


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
    interp = ['nearest'],
#    spwmap = [[0,0,0,0,0,0,0,0],[]],
    gaintable=[gtab0])

#     gainfield=[bpcal,bpcal],
#     interp = ['nearest','nearest'],
# #    spwmap = [[0,0,0,0,0,0,0,0],[]],
#     gaintable=[ktab0,gtab0])


# ------- Correct primary data with B0,G0


applycal(vis=myms,
    gaintable=[gtab0,bptab0],
#    applymode='calonly',
    field=bpcal_name,
#    calwt=False,
    parang=False,
    gainfield=[bpcal_name,bpcal_name],
    interp = ['nearest','nearest'])


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


# gaincal(vis=myms,
#     field=bpcal,
#     caltable=ktab1,
#     refant = str(ref_ant),
#     gaintype = 'K',
#     solint = 'inf',
#     parang=False,
#     gaintable=[bptab0,gtab0],
#     gainfield=[bpcal,bpcal],
# #       combine='spw',
#     interp=['nearest','nearest'])


# ------- G1 (primary; apply B0)


gaincal(vis=myms,
    field=bpcal_name,
    uvrange=myuvrange,
    caltable=gtab1,
    gaintype='G',
    solint='inf',
    calmode='p',
    minsnr=5,
    gainfield=[bpcal_name],
    interp = ['nearest'],
#    spwmap = [[0,0,0,0,0,0,0,0],[]],
    gaintable=[bptab0])


# ------- B1 (primary; apply G1)


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
    gainfield=[bpcal_name],
    interp = ['nearest'],
#    spwmap = [[0,0,0,0,0,0,0,0],[]],
    gaintable=[gtab1])


# ------- Correct primary data with G1,B1


applycal(vis=myms,
    gaintable=[gtab1,bptab1],
#    applymode='calonly',
    field=bpcal_name,
#    calwt=False,
    parang=False,
    gainfield=[bpcal_name,bpcal_name],
#    spwmap = [[0,0,0,0,0,0,0,0],[],[]],
    interp = ['nearest','nearest'])


# --------------------------------------------------------------- #
# --------------------------------------------------------------- #
# --------------------------- STAGE 2 --------------------------- #
# --------------------------------------------------------------- #
# --------------------------------------------------------------- #


# ------- G2 (primary; a&p sols per scan / SPW)


gaincal(vis = myms,
    field = bpcal_name,
    uvrange = myuvrange,
    caltable = gtab2,
    refant = str(ref_ant),
    solint = 'inf',
    solnorm = False,
    combine = '',
    minsnr = 3,
    calmode = 'ap',
    parang = False,
    gaintable = [gtab1,bptab1],
    gainfield = [bpcal_name,bpcal_name],
    interp = ['nearest','nearest'],
    append = False)


# ------- Duplicate G2 (to save repetition of above step)


shutil.copytree(gtab2,gtab3)


# ------- Looping over secondaries


for i in range(0,len(pcal_names)):


    pcal = pcal_names[i] # Using field names


    # --- G2 (secondary)


    gaincal(vis = myms,
        field = pcal,
        uvrange = myuvrange,
        caltable = gtab2,     
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
        gaintable=[gtab1,bptab1],
        gainfield=[bpcal_name,bpcal_name],
        interp=['linear','linear'],
#        spwmap = [[0,0,0,0,0,0,0,0],[],[]],
        append=True)


# ------- F2


secondary_models = fluxscale(vis=myms,
    caltable = gtab2,
    fluxtable = ftab2,
    reference = bpcal_name,
    append = False,
    transfer = '')


# ------- Looping over secondaries


secondary_mapping = [] # To link field names to IDs in model dict, as different from master MS


for i in range(0,len(pcal_names)):


    pcal = pcal_names[i] # Using field names
    pcal_idx = getfieldid(myms,pcal)
    secondary_mapping.append((pcal,pcal_idx))


    # --- Correct secondaries with G1, B1, F2


    applycal(vis = myms,
        gaintable = [gtab1,bptab1,ftab2],
#        applymode='calonly',
        field = pcal,
        calwt = False,
        parang = False,
        gainfield = [bpcal_name,bpcal_name,pcal],
#        spwmap = [[0,0,0,0,0,0,0,0],[],[],[]],
        interp = ['nearest','nearest','linear'])


    # --- Predict model data from fitted secondary models


    iflux = secondary_models[str(pcal_idx)]['fitFluxd']
    spidx = secondary_models[str(pcal_idx)]['spidx']
    if len(spidx) == 2:
        myspix = spidx[1] 
    elif len(spidx) == 3:
        alpha = spidx[1]        
        beta = spidx[2]
        myspix = [alpha,beta]
    ref_freq = str(secondary_models[str(pcal_idx)]['fitRefFreq'])+'Hz'


    setjy(vis =myms,
        field = pcal,
        standard = 'manual',
        fluxdensity = [iflux,0,0,0],
        spix = myspix,
        reffreq = ref_freq,
        usescratch = True)


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



pickle.dump((secondary_models,secondary_mapping),open(interim_pickle,'wb'))


# --------------------------------------------------------------- #
# --------------------------------------------------------------- #
# --------------------------- STAGE 3 --------------------------- #
# --------------------------------------------------------------- #
# --------------------------------------------------------------- #


# ------- Looping over secondaries


for i in range(0,len(pcal_names)):


    pcal = pcal_names[i] # Using field names
    pcal_idx = getfieldid(myms,pcal)


    # --- G3 (secondary)


    gaincal(vis = myms,
        field = pcal,
        uvrange = myuvrange,
        caltable = gtab3,     
        refant = str(ref_ant),
        minblperant = 4,
        smodel=[1,0,0,0],
        minsnr = 3,
        solint = 'inf',
        solnorm = False,
        gaintype = 'G',
        combine = '',
        calmode = 'ap',
        parang = False,
        gaintable=[gtab1,bptab1],
        gainfield=[bpcal_name,bpcal_name],
        interp=['nearest','nearest'],
#        spwmap = [[0,0,0,0,0,0,0,0],[],[]],
        append=True)



# ------- F3


secondary_models_final = fluxscale(vis=myms,
    caltable = gtab3,
    fluxtable = ftab3,
    reference = bpcal_name,
    append = False,
    transfer = '')


pickle.dump((secondary_models_final,secondary_mapping),open(secondary_pickle,'wb'))

