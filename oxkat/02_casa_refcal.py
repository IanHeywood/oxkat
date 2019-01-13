# ianh@astro.ox.ac.uk


import numpy
import glob
import pickle
import shutil


project_info = pickle.load(open('project_info.p','rb'))


myms = glob.glob('*wtspec.ms')[0]
target = project_info['target'][0]
bpcal = project_info['primary'][0]
primary_name = project_info['primary_name']
pcal = project_info['secondary'][0]
pcal_mod = ([1.0,0.0,0.0,0.0],[0.0],'1284MHz')
opms = myms.replace('.ms','_'+target+'.ms')
ref_ant = project_info['ref_ant']
k0 = project_info['k0']
k1 = project_info['k1']


if 'LO' in myms or 'HI' in myms:
	delayspw = ''
else:
	delayspw = '0:'+str(k0)+'~'+str(k1)


gtab0 = 'cal_'+myms+'.G0'
ktab0 = 'cal_'+myms+'.K0'
bptab0 = 'cal_'+myms+'.B0'
gtab1 = 'cal_'+myms+'.G1'
ftab0 = 'cal_'+myms+'.flux0'


dosteps = [1,2,3,4]


#------------------------------------------------------


if 1 in dosteps:


	if primary_name == '1934':
		setjy(vis=myms,
			field=bpcal,
                	standard='Perley-Butler 2010',
               		usescratch=True)
	elif primary_name == '0408':
		bpcal_mod = ([17.066,0.0,0.0,0.0],[-1.179],'1284MHz')
		setjy(vis=myms,
			field=bpcal,
			standard='manual',
			fluxdensity=bpcal_mod[0],
			spix=bpcal_mod[1],
			reffreq=bpcal_mod[2],
                        usescratch=True)


	gaincal(vis=myms,
		field=bpcal,
		caltable=gtab0,
		gaintype='G',
		solint='int',
		calmode='ap',
		minsnr=5)


        gaincal(vis=myms,
                field=bpcal,
		caltable=ktab0,
                refant = str(ref_ant),
                spw = delayspw,
                gaintype = 'K',
                solint = 'inf',
                combine = 'scan',
                minsnr = 5,
                gaintable=[gtab0])


	bandpass(vis=myms,
		field=bpcal,
		caltable=bptab0,
		solint='inf',
		combine='scan',
		solnorm=False,
		gainfield=[bpcal,bpcal],
		interp = ['nearest','nearest'],
		gaintable=[ktab0,gtab0])


if 2 in dosteps:


	setjy(vis=myms,
		field=pcal,
		standard='manual',
		fluxdensity=pcal_mod[0],
		spix=pcal_mod[1],
		reffreq=pcal_mod[2],
		usescratch=True)


	gaincal(vis=myms,
		field=pcal,
		caltable=gtab1,
		solint='inf',
		combine='',
		gaintable=[bptab0,ktab0],
		gainfield=[bpcal,bpcal],
		interp=['nearest','nearest'],
		append=False)


	gaincal(vis=myms,
		field=bpcal,
		caltable=gtab1,
		solint='inf',
		combine='',
		gaintable=[bptab0,ktab0],
		gainfield=[bpcal,bpcal],
		interp=['nearest','nearest'],
		append=True)


	fluxscale(vis=myms,
		caltable=gtab1,
		fluxtable=ftab0,
		reference=bpcal,
		transfer=pcal)


if 3 in dosteps:


	applycal(vis=myms,
		gaintable=[ktab0,bptab0,ftab0],
		field=bpcal,
		gainfield=[bpcal,bpcal,bpcal],
		interp = ['nearest','nearest','linear'])


	applycal(vis=myms,
		gaintable=[ktab0,bptab0,ftab0],
		field=pcal,
		gainfield=[bpcal,bpcal,pcal],
		interp = ['nearest','nearest','linear'])


	applycal(vis=myms,
		gaintable=[ktab0,bptab0,ftab0],
		field=target,
		gainfield=[bpcal,bpcal,pcal],
		interp=['nearest','nearest','linear'])


if 4 in dosteps:


	split(vis=myms,
		outputvis=opms,
		field=target,
		datacolumn='corrected')
