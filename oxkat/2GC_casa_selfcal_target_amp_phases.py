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


gptab = GAINTABLES+'/cal_'+myms+'_'+stamp()+'.GP0'
gatab = GAINTABLES+'/cal_'+myms+'_'+stamp()+'.GA0'


gaincal(vis=myms,
    field='0',
    uvrange=myuvrange,
    caltable=gptab,
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


gaincal(vis=myms,
    field='0',
    uvrange=myuvrange,
    caltable=gatab,
    refant = str(ref_ant),
    solint='inf',
    solnorm=False,
    combine='',
    minsnr=3,
    calmode='ap',
    parang=False,
    gaintable=[gptab],
    gainfield=[''],
    interp=[''],
    append=False)



applycal(vis=myms,
    gaintable=[gptab,gatab],
    field='0',
    calwt=False,
    parang=False,
    applymode='calonly',
    gainfield=['',''],
    interp = ['nearest','linear'])


# statwt(vis=myms,
#     field='0')


clearstat()
clearstat()


