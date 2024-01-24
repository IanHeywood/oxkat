 # ian.heywood@physics.ox.ac.uk

import glob
import numpy

execfile('oxkat/config.py')
execfile('oxkat/casa_read_project_info.py')

myfields = PRE_FIELDS
myscans = PRE_SCANS
myoutputchans = int(PRE_NCHANS)
mytimebin = PRE_TIMEBIN


#master_ms = glob.glob('*.ms')[0]
opms = master_ms.replace('.ms','_'+str(myoutputchans)+'ch.ms')


tb.open(master_ms+'/SPECTRAL_WINDOW')
nchan = tb.getcol('NUM_CHAN')[0]
tb.done()

if myscans == '':
	tb.open(master_ms)
	numsubs = len(numpy.unique(tb.getcol('SCAN_NUMBER')))
	print('Creating '+str(numsubs)+' sub MS based on number of scans in master MS')
else:
	numsubs = len(myscans.split(','))
	print('Creating '+str(numsubs)+' sub MS based on user-specified scan selection')


mychanbin = int(nchan/myoutputchans)
if mychanbin <= 1:
	mychanave = False
else:
	mychanave = True

if mytimebin == '':
	mytimeave = False
else:
	mytimeave = True

mstransform(vis = master_ms,
	outputvis = opms,
	field = myfields,
	scan = myscans,
	createmms = True,
	separationaxis = 'scan',
	numsubms = numsubs,
	datacolumn = 'data',
	chanaverage = mychanave,
	chanbin = mychanbin,
	timeaverage = mytimeave,
	timebin = mytimebin,
	realmodelcol = True,
	usewtspectrum = True)

if SAVE_FLAGS:
	flagmanager(vis = opms, mode = 'save', versionname = 'observatory')

clearcal(vis = opms, addmodel = True)


# *** THIS IS NOW HANDLED AT THE SETUP STAGE
# write out subms map
# print('Writing sub-MS map')
# subms_map = opms+'/subms_map.txt'
# f = open(subms_map,'w')
# submss = sorted(glob.glob(opms+'/SUBMSS/*.ms'))
# for subms in submss:
# 	tb.open(subms)
# 	srcid = str(numpy.unique(tb.getcol('FIELD_ID')).item())
# 	opstr = subms+' '+srcid+' '
# 	if srcid in target:
# 		opstr += 'TARGET'
# 	elif srcid in pcals:
# 		opstr += 'PCAL'
# 	elif srcid == bpcal:
# 		opstr += 'PRIMARY'
# 	elif srcid == polcal:
# 		opstr += 'POLCAL'
# 	print(opstr)
# 	opstr += '\n'
# 	f.writelines(opstr)
# 	tb.done()
# f.close()


# Zero receptor angle in case polcal is happening
print('Zeroing receptor angles in '+opms)
tb.open(opms+'/FEED',nomodify=False)
receptor_angles = tb.getcol('RECEPTOR_ANGLE')
receptor_angles[...] = 0.0
tb.putcol('RECEPTOR_ANGLE',receptor_angles)
tb.flush()
tb.done()


clearstat()
clearstat()
