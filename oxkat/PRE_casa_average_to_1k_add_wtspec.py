 # ian.heywood@physics.ox.ac.uk

import glob


execfile('oxkat/config.py')
execfile('oxkat/casa_read_project_info.py')

myfields = PRE_FIELDS
myscans = PRE_SCANS
myoutputchans = int(PRE_NCHANS)
mytimebins = PRE_TIMEBIN


master_ms = glob.glob('*.ms')[0]
opms = master_ms.replace('.ms','_'+str(myoutputchans)+'ch.ms')


tb.open(master_ms+'/SPECTRAL_WINDOW')
nchan = tb.getcol('NUM_CHAN')[0]
tb.done()


mychanbin = int(nchan/myoutputchans)
if mychanbin <= 1:
	mychanave = False
else:
	mychanave = True


mstransform(vis = master_ms,
	outputvis = opms,
	field = myfields,
	scan = myscans,
	datacolumn = 'data',
	chanaverage = mychanave,
	chanbin = mychanbin,
	# timeaverage = True,
	# timebin = '8s',
	realmodelcol = True,
	usewtspectrum = True)


flagmanager(vis = opms, mode = 'save', versionname = 'observatory')

clearcal(vis = opms, addmodel = True)


clearstat()
clearstat()