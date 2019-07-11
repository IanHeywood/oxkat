# Basic hands-off 1GC CASA script for a MeerKAT MS with multiple targets
# Data should be flagged first, and this should be run from a path that contains 
# only the MS to be processed.
#
# ian.heywood@physics.ox.ac.uk
# 21.06.19


import numpy
import glob
import sys


myms = glob.glob('*.ms')[0]


gtab0 = 'cal_'+myms+'.G0'
ktab0 = 'cal_'+myms+'.K0'
bptab0 = 'cal_'+myms+'.B0'
gtab1 = 'cal_'+myms+'.G1'
ftab0 = 'cal_'+myms+'.flux0'


# 1 = setup models, solve for B and K
# 2 = solve for G
# 3 = apply solutions to cals and target(s)
# 4 = split each target into a single MS

dosteps = [1,2,3,4]


# ---------------------------------------------------------------------
# Identify calibrators and targets


tb.open(myms+'/STATE')
modes = tb.getcol('OBS_MODE')
tb.close()


for i in range(0,len(modes)):
    if modes[i] == 'TARGET':
        target_state = i
    if 'BANDPASS' in modes[i]:
        primary_state = i
    if 'PHASE' in modes[i]:
        secondary_state = i


tb.open(myms+'/FIELD')
fld_names = tb.getcol('NAME')
dirs = tb.getcol('REFERENCE_DIR')
tb.close()


targets = []
bpcal = ''
pcal = ''


tb.open(myms)
for i in range(0,len(fld_names)):
    sub_tab = tb.query(query='FIELD_ID=='+str(i))
    state = numpy.unique(sub_tab.getcol('STATE_ID'))
    if state == target_state:
        opms = myms.rstrip('/').replace('.ms',fld_names[i]+'.ms')
        targets.append((str(i),fld_names[i],opms)) 
    elif state == primary_state:
        bpcal = str(i)
    elif state == secondary_state:
        pcal = str(i)
tb.done()


if bpcal == '' or pcal == '':
	print 'Unable to identify one or more calibrators, maybe a problem with the STATE table or STATE_IDs.'
	print 'Suggest hacking the script to set them manually.'
	sys.exit()
else:
	print ''
	print 'Assuming:'
	print '   '+fld_names[int(bpcal)]+' (primary calibrator)'
	print '   '+fld_names[int(pcal)]+' (secondary calibrator)'
	for tt in targets:
		print '   '+tt[1]+' (target)'


# ---------------------------------------------------------------------
# Positional match for primary to select model for setjy later on


dir_1934 = me.direction('J2000','294.85427795833334deg','-63.71267375deg')
dir_0408 = me.direction('J2000','62.084911833333344deg','-65.752522	38888889deg')
cal_dirs = (dir_1934,dir_0408)


seps = []


ra_bpcal = str(180.0*dirs[0][0][int(bpcal)]/numpy.pi)+'deg'
dec_bpcal = str(180.0*dirs[1][0][int(bpcal)]/numpy.pi)+'deg'


dir_bpcal = me.direction('J2000',ra_bpcal,dec_bpcal)


for cal in cal_dirs:
	seps.append(me.separation(cal,dir_bpcal)['value'])


seps = numpy.array(seps)


idx = numpy.where((seps < 1e-3)==True)[0][0]


if idx == 0:
	primary_name = '1934'
elif idx == 1:
	primary_name = '0408'


# ---------------------------------------------------------------------
# Suggest a reference antenna from ref_pool
# This selects the one with the minimum number of flags in the primary scans


ref_pool = ['m000','m001','m002','m003','m004','m006']


tb.open(myms+'/ANTENNA')
ant_names = tb.getcol('NAME')
ant_names = [a.lower() for a in ant_names]
tb.close()


pc_list = numpy.ones(len(ref_pool))*100.0
idx_list = numpy.zeros(len(ref_pool),dtype=numpy.int8)


tb.open(myms)


for i in range(0,len(ref_pool)):
    ant = ref_pool[i]
    try:
        idx = ant_names.index(ant)
        sub_tab = tb.query(query='ANTENNA1=='+str(idx)+' && FIELD_ID=='+str(bpcal))
        flags = sub_tab.getcol('FLAG')
        vals,counts = numpy.unique(flags,return_counts=True)
        if len(vals) == 1 and vals == True:
            flag_pc = 100.0
        elif len(vals) == 1 and vals == False:
            flag_pc = 0.0
        else:
            flag_pc = 100.*round(float(counts[1])/float(numpy.sum(counts)),2)
        pc_list[i] = flag_pc
        idx_list[i] = idx
    except:
        continue


ref_idx = idx_list[numpy.where(pc_list==(numpy.min(pc_list)))][0]


print ''
print 'Using reference antenna',ref_pool[ref_idx]	
ref_ant = str(ref_idx)


# ---------------------------------------------------------------------
# Determine generally clean channel range for delay cal


tb.open(myms+'/SPECTRAL_WINDOW')
nchan = tb.getcol('NUM_CHAN')[0]
tb.done()


edge_flags = int(120*nchan/4096)
k0 = int(2120*nchan/4096)
k1 = int(3120*nchan/4096)
delayspw = '0:'+str(k0)+'~'+str(k1)


print ''
print 'Using channels',k0,'-',k1,'for delay calibration'


# ---------------------------------------------------------------------


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
		parang=False,
		gaintable=[gtab0],
		gainfield=[bpcal],
		interp=['nearest'],
		combine = 'scan')


	bandpass(vis=myms,
		field=bpcal,
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


	for targ in targets:

		target = targ[0]

		applycal(vis=myms,
			gaintable=[gtab0,ktab0,bptab0,ftab0],
			field=target,
			calwt=False,
			parang=False,
			gainfield=[bpcal,bpcal,bpcal,pcal],
			interp=['nearest','nearest','nearest','linear'])


if 4 in dosteps:

	for targ in targets:
		target = targ[0]
		opms = targ[2]

		mstransform(vis=myms,outputvis=opms,field=target,usewtspectrum=True,datacolumn='corrected')
