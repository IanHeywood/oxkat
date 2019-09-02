# ian.heywood@physics.ox.ac.uk

import glob

myms = glob.glob('*.ms')[0]
opms = myms.replace('.MS','.ms')
opms = myms.replace('.ms','_SPW_wtspec.ms')

tb.open(myms+'/SPECTRAL_WINDOW')
nchan = tb.getcol('NUM_CHAN')[0]
tb.done()

mychanbin = int(nchan/1024)
if mychanbin == 1:
	mychanave = False
else:
	mychanave = True

mstransform(vis=myms,
	outputvis=opms,
	datacolumn='data',
	chanaverage=mychanave,
	chanbin=mychanbin,
	regridms=True,
	mode='channel_b',
	nspw=8,
	timeaverage=True,
	timebin='8s',
	realmodelcol=True,
	usewtspectrum=True)

flagmanager(vis=opms,mode='save',versionname='observatory')