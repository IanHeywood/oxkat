# ian.heywood@physics.ox.ac.uk


# Work in progress.
# This is a straightforward copy of the stages for the primary calibrator for the normal 1GC script.
# There is a fillgaps modifier for the high spectral resolution MMS.
# MMS naming schemes etc. still need fixing, at present it globs for *.mms.
# Consider off a KGB block with an iterator and moving the primary flagging to tricolour if CASA proves to be too slow.
# Intermediate flag table states have been dropped for reasons of speed.


import glob
import shutil
import time


execfile('oxkat/casa_read_project_info.py')
execfile('oxkat/config.py')



def stamp():
    now = str(datetime.datetime.now()).replace(' ','-').replace(':','-').split('.')[0]
    return now
    

# ------- Parameters


mymms = glob.glob('*.mms')[0]
myuvrange = CAL_1GC_UVRANGE
gapfill = CAL_1GC_LINE_FILLGAPS


# ------- Setup names


tt = stamp()


ktab0 = GAINTABLES+'/cal_1GC_LINE_'+mymms+'_'+tt+'.K0'
bptab0 = GAINTABLES+'/cal_1GC_LINE_'+mymms+'_'+tt+'.B0'
gtab0 = GAINTABLES+'/cal_1GC_LINE_'+mymms+'_'+tt+'.G0'


ktab1 = GAINTABLES+'/cal_1GC_LINE_'+mymms+'_'+tt+'.K1'
bptab1 = GAINTABLES+'/cal_1GC_LINE_'+mymms+'_'+tt+'.B1'
gtab1 = GAINTABLES+'/cal_1GC_LINE_'+mymms+'_'+tt+'.G1'


ktab2 = GAINTABLES+'/cal_1GC_LINE_'+mymms+'_'+tt+'.K2'
gtab2 = GAINTABLES+'/cal_1GC_LINE_'+mymms+'_'+tt+'.G2'
ftab2 = GAINTABLES+'/cal_1GC_LINE_'+mymms+'_'+tt+'.flux2'


ktab3 = GAINTABLES+'/cal_1GC_LINE_'+mymms+'_'+tt+'.K3'
gtab3 = GAINTABLES+'/cal_1GC_LINE_'+mymms+'_'+tt+'.G3'
ftab3 = GAINTABLES+'/cal_1GC_LINE_'+mymms+'_'+tt+'.flux3'



# ------- K0 (primary)


gaincal(vis=mymms,
    field=bpcal,
    #uvrange=myuvrange,
    caltable=ktab0,
    refant = str(ref_ant),
    gaintype = 'K',
    solint = 'inf',
    parang=False)


# ------- G0 (primary; apply K0)


gaincal(vis=mymms,
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


bandpass(vis=mymms,
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


applycal(vis=mymms,
    gaintable=[ktab0,gtab0,bptab0],
#    applymode='calonly',
    field=bpcal,
#    calwt=False,
    parang=False,
    gainfield=[bpcal,bpcal,bpcal],
    interp = ['nearest','nearest','nearest'])


# ------- Flag primary on CORRECTED_DATA - MODEL_DATA


flagdata(vis=mymms,
    mode='rflag',
    datacolumn='residual',
    field=bpcal)


flagdata(vis=mymms,
    mode='tfcrop',
    datacolumn='residual',
    field=bpcal)



# --------------------------------------------------------------- #
# --------------------------------------------------------------- #
# --------------------------- STAGE 1 --------------------------- #
# --------------------------------------------------------------- #
# --------------------------------------------------------------- #


# ------- K1 (primary; apply B0, G0)


gaincal(vis=mymms,
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


gaincal(vis=mymms,
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


bandpass(vis=mymms,
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


applycal(vis=mymms,
    gaintable=[ktab1,gtab1,bptab1],
#    applymode='calonly',
    field=bpcal,
#    calwt=False,
    parang=False,
    gainfield=[bpcal,bpcal,bpcal],
    interp = ['nearest','nearest','nearest'])


if SAVE_FLAGS:
    flagmanager(vis=mymms,mode='save',versionname='primary-refcal')
