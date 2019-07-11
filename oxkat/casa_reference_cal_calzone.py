# ian.heywood@physics.ox.ac.uk


import pickle
import time
import shutil


def stamp():
    return str(time.time()).replace('.','')


myuvrange = '>150m'

remove_cal_tables = False


project_info = pickle.load(open('project_info.p','rb'))


myms = project_info['master_ms']
bpcal = project_info['primary']
primary_tag = project_info['primary_tag']
pcal = project_info['secondary']
ref_ant = project_info['ref_ant'] = str(ref_ant)
k0 = project_info['k0'] = k0
k1 = project_info['k1'] = k1


gtab0 = 'cal_'+myms+'_'+stamp()+'.G0'
ktab0 = 'cal_'+myms+'_'+stamp()+'.K0'
bptab0 = 'cal_'+myms+'_'+stamp()+'.B0'
gtab1 = 'cal_'+myms+'_'+stamp()+'.G1'
ftab0 = 'cal_'+myms+'_'+stamp()+'.flux0'


# 1 = setup models, solve for B and K
# 2 = solve for G
# 3 = apply solutions to cals 


dosteps = [1,2,3]



if 1 in dosteps:


    if primary_tag == '1934':
        setjy(vis=myms,
            field=bpcal,
            standard='Perley-Butler 2010',
            scalebychan=True)
#           usescratch=True)
        
        
    elif primary_tag == '0408':
        bpcal_mod = ([17.066,0.0,0.0,0.0],[-1.179],'1284MHz')
        setjy(vis=myms,
            field=bpcal,
            standard='manual',
            fluxdensity=bpcal_mod[0],
            spix=bpcal_mod[1],
            reffreq=bpcal_mod[2],
            scalebychan=True)
#           usescratch=True)


    gaincal(vis=myms,
        field=bpcal,
        uvrange=myuvrange,
        caltable=gtab0,
        gaintype='G',
        solint='int',
        calmode='ap',
        minsnr=5)


    gaincal(vis=myms,
        field=bpcal,
        uvrange=myuvrange,
        caltable=ktab0,
        refant = str(ref_ant),
        spw = delayspw,
        gaintype = 'K',
        solint = 'inf',
        parang=False,
        gaintable=[gtab0],
        gainfield=[bpcal],
        interp=['nearest'],
        combine = 'scan')


    bandpass(vis=myms,
        field=bpcal,
        uvrange=myuvrange,
        caltable=bptab0,
        refant = str(ref_ant),
        solint='inf',
        combine='scan',
        solnorm=False,
        minblperant=4,
        bandtype='B',
        fillgaps=8,
        parang=False,
        gainfield=[bpcal,bpcal],
        interp = ['nearest','nearest'],
        gaintable=[gtab0,ktab0])


if 2 in dosteps:


    gaincal(vis=myms,
        field=bpcal,
        uvrange=myuvrange,
        caltable=gtab1,
        refant = str(ref_ant),
        solint='inf',
        solnorm=False,
        combine='',
        minsnr=3,
        calmode='ap',
        parang=False,
        gaintable=[gtab0,ktab0,bptab0],
        gainfield=[bpcal,bpcal,bpcal],
        interp=['nearest','nearest','nearest'],
        append=False)

    
    gaincal(vis=myms,
        field=pcal,
        uvrange=myuvrange,
        caltable=gtab1,     
        refant = str(ref_ant),
        smodel=[1,0,0,0],
        minblperant=4,
        minsnr=3,
        solint='inf',
        solnorm=False,
        gaintype='G',
        combine='',
        calmode='ap',
        parang=False,
        gaintable=[gtab0,ktab0,bptab0],
        gainfield=[bpcal,bpcal,bpcal],
        interp=['nearest','nearest','nearest'],
        append=True)


    fluxscale(vis=myms,
        caltable=gtab1,
        fluxtable=ftab0,
        reference=bpcal,
        append=False,
        transfer='')


if 3 in dosteps:


    applycal(vis=myms,
        gaintable=[gtab0,ktab0,bptab0,ftab0],
        field=bpcal,
        calwt=False,
        parang=False,
        gainfield=[bpcal,bpcal,bpcal,bpcal],
        interp = ['nearest','nearest','nearest','linear'])


    applycal(vis=myms,
        gaintable=[gtab0,ktab0,bptab0,ftab0],
        field=pcal,
        calwt=False,
        parang=False,
        gainfield=[bpcal,bpcal,bpcal,pcal],
        interp = ['nearest','nearest','nearest','linear'])

flagmanager(vis=opms,mode='save',versionname='refcal-cals')

if remove_cal_tables:
    shutil.rmtree(gtab0)
    shutil.rmtree(ktab0)
    shutil.rmtree(bptab0)
    shutil.rmtree(gtab1)
    shutil.rmtree(ftab0)
