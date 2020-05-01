# ian.heywood@physics.ox.ac.uk


import pickle
import sys
import time


execfile('oxkat/config.py')


def stamp():
    return str(time.time()).replace('.','')

myuvrange = ''

args = sys.argv
for item in sys.argv:
    parts = item.split('=')
    if parts[0] == 'mslist':
        mslist = parts[1].split(',')
    if parts[0] == 'uvmin':
        myuvrange = '>'+parts[1]

if myuvrange == '':
    myuvrange = '>150m'


project_info = pickle.load(open('project_info.p','rb'))
ref_ant = project_info['ref_ant']


for myms in mslist:

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


