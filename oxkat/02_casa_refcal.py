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
			scalebychan=True)
#			usescratch=True)
		
		
	elif primary_name == '0408':
		bpcal_mod = ([17.066,0.0,0.0,0.0],[-1.179],'1284MHz')
		setjy(vis=myms,
			field=bpcal,
			standard='manual',
			fluxdensity=bpcal_mod[0],
			spix=bpcal_mod[1],
			reffreq=bpcal_mod[2],
			scalebychan=True)
#			usescratch=True)


	# gaincal(vis=myms,
	# 	field=bpcal,
	# 	caltable=gtab0,
	# 	gaintype='G',
	# 	solint='int',
	# 	calmode='p',
	# 	minsnr=5)


	gaincal(vis=myms,
		field=bpcal,
		caltable=ktab0,
		refant = str(ref_ant),
#		spw = delayspw,
		gaintype = 'K',
		solint = 'inf',
		parang=False,
		combine = 'scan')


	bandpass(vis=myms,
		field=bpcal,
		caltable=bptab0,
		refant = str(ref_ant),
		solint='inf',
		combine='scan',
		solnorm=True,
		minblperant=4,
		bandtype='B',
		fillgaps=8,
		parang=False,
		gainfield=[bpcal],
		interp = ['nearest'],
		gaintable=[ktab0])


if 2 in dosteps:


	gaincal(vis=myms,
		field=bpcal,
		caltable=gtab1,
		refant = str(ref_ant),
		solint='5min',
		solnorm=False,
		combine='',
		minsnr=3,
		calmode='ap',
		parang=False,
		gaintable=[ktab0,bptab0],
		gainfield=[bpcal,bpcal],
		interp=['nearest','nearest'],
		append=False)

	gaincal(vis=myms,
		field=pcal,
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
		gaintable=[ktab0,bptab0],
		gainfield=[bpcal,bpcal],
		interp=['nearest','nearest'],
		append=True)



	fluxscale(vis=myms,
		caltable=gtab1,
		fluxtable=ftab0,
		reference=bpcal,
		append=False,
		transfer='')


if 3 in dosteps:


	applycal(vis=myms,
		gaintable=[ktab0,bptab0,ftab0],
		field=bpcal,
		calwt=False,
		parang=False,
		gainfield=[bpcal,bpcal,bpcal],
		interp = ['nearest','nearest','linear'])


	applycal(vis=myms,
		gaintable=[ktab0,bptab0,ftab0],
		field=pcal,
		calwt=False,
		parang=False,
		gainfield=[bpcal,bpcal,pcal],
		interp = ['nearest','nearest','linear'])


	applycal(vis=myms,
		gaintable=[ktab0,bptab0,ftab0],
		field=target,
		calwt=False	,
		parang=False,
		gainfield=[bpcal,bpcal,pcal],
		interp=['nearest','nearest','linear'])


if 4 in dosteps:


	split(vis=myms,
		outputvis=opms,
		field=target,
		datacolumn='corrected')
