# ianh@astro.ox.ac.uk

import glob

myms = glob.glob('*.ms')[0]
opms = myms.replace('.ms','_wtspec.ms')

tb.open(myms+'/SPECTRAL_WINDOW',ack=False)
tb.getcol('NUM_CHAN')[0]
tb.done()

mychanbin = int(nchan/1024)

mstransform(vis=myms,
	outputvis=opms,
	datacolumn='data',
	chanaverage=True,
	chanbin=mychanbin,
	timeaverage=True,
	timebin='8s',
	realmodelcol=True,
	usewtspectrum=True)
