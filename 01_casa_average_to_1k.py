# ianh@astro.ox.ac.uk

import glob

myms = glob.glob('*.ms')
opms = myms.replace('.ms','_wtspec.ms')

spw_table = table(myms+'/SPECTRAL_WINDOW',ack=False)
nchan = spw_table.getcol('NUM_CHAN')[0]
spw_table.close()

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
