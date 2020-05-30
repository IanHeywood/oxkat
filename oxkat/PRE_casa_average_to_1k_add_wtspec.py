# ian.heywood@physics.ox.ac.uk

import glob


execfile('oxkat/config.py')

myfields = PRE_FIELDS
myoutputchans = int(PRE_NCHANS)
mytimebins = PRE_TIMEBIN


myms = glob.glob('*.ms')[0]
opms = myms.replace('.ms','_'+str(myoutputchans)+'ch.ms')


tb.open(myms+'/SPECTRAL_WINDOW')
nchan = tb.getcol('NUM_CHAN')[0]
tb.done()


mychanbin = int(nchan/myoutputchans)
if mychanbin == 1:
	mychanave = False
else:
	mychanave = True


mstransform(vis = myms,
	outputvis = opms,
	field = myfields,
	datacolumn = 'data',
	chanaverage = mychanave,
	chanbin = mychanbin,
	timeaverage = True,
	timebin = '8s',
	realmodelcol = True,
	usewtspectrum = True)


flagmanager(vis = opms, mode = 'save', versionname = 'observatory')


clearstat()
clearstat()