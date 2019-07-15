# Find primary cal
# Find nearest secondary cal to each target
# Split a new MS containing primary and secondary-target pairs
# ian.heywood@physics.ox.ac.uk


import numpy
import glob
import sys


myms = glob.glob('*.ms')[0]


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
pcals = []
bpcal = ''


tb.open(myms)
for i in range(0,len(fld_names)):
    sub_tab = tb.query(query='FIELD_ID=='+str(i))
    state = numpy.unique(sub_tab.getcol('STATE_ID'))
    if state == target_state:
        opms = myms.rstrip('/').replace('.ms',fld_names[i]+'.ms')
        targets.append((str(i),fld_names[i])) 
    elif state == primary_state:
        bpcal = str(i)
    elif state == secondary_state:
        pcals.append((str(i),fld_names[i]))
tb.done()


field_selections = []


for pcal in pcals:

	seps = []
	pcal_idx = pcal[0]

	ra_pcal = str(180.0*dirs[0][0][int(pcal_idx)]/numpy.pi)+'deg'
	dec_pcal = str(180.0*dirs[1][0][int(pcal_idx)]/numpy.pi)+'deg'


	dir_pcal = me.direction('J2000',ra_pcal,dec_pcal)


	for target in targets:
		targ_idx = target[0]
		ra_target = str(180.0*dirs[0][0][int(targ_idx)]/numpy.pi)+'deg'
		dec_target = str(180.0*dirs[1][0][int(targ_idx)]/numpy.pi)+'deg'

		dir_target = me.direction('J2000',ra_target,dec_target)

		seps.append(me.separation(dir_target,dir_pcal)['value'])

	seps = numpy.array(seps)

	targ_match = numpy.where((seps == numpy.min(seps))==True)[0][0]

	field_selections.append(bpcal+','+pcal_idx+','+str(targets[targ_match][0]))



for i in range(0,len(field_selections)):

	opms = myms.replace('.ms','_BLOCK'+str(i)+'.ms')

	mstransform(vis=myms,outputvis=opms,field=field_selections[i],usewtspectrum=True,datacolumn='data',realmodelcol=True,chanaverage=True,chanbin=4,timeaverage=False)
