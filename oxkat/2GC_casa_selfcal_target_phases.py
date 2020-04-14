# ian.heywood@physics.ox.ac.uk


import sys
import time
import shutil


execfile('oxkat/config.py')


def stamp():
    return str(time.time()).replace('.','')


args = sys.argv
for item in sys.argv:
    parts = item.split('=')
    if parts[0] == 'mslist':
        mslist = parts[1].split(',')


myuvrange = '>150m'


clearstat()
clearstat()


gtab = GAINTABLES+'/cal_'+myms+'_'+stamp()+'.GP0'


gaincal(vis=myms,
    field='0',
    uvrange=myuvrange,
    caltable=gtab,
    refant = str(ref_ant),
    solint='64s',
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


# statwt(vis=myms,
#     field='0')


clearstat()
clearstat()


