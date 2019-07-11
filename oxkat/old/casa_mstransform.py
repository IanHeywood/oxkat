# ianh@astro.ox.ac.uk

import glob

myms = glob.glob('*.ms')[0]
opms = myms.replace('.ms','_wtspec.ms')

mstransform(vis=myms,
	outputvis=opms,
	datacolumn='data',
	chanaverage=False,
	chanbin=1,
	timeaverage=True,
	timebin='8s',
	realmodelcol=True,
	usewtspectrum=True)
