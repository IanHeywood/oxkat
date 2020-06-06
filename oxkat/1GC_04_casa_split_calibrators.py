# ian.heywood@physics.ox.ac.uk


execfile('oxkat/casa_read_project_info.py')

myoutputchans = int(PRE_NCHANS)

code = myms.split('/')[-1].split('_')[0]

opms = code+'_calibrators.ms'


field_selection = [bpcal]
for pcal in pcals:
	field_selection.append(pcal)

field_selection = ','.join(sorted(field_selection))


tb.open(myms+'/SPECTRAL_WINDOW')
nchan = tb.getcol('NUM_CHAN')[0]
tb.done()


mychanbin = int(nchan/myoutputchans)
if mychanbin == 1:
	mychanave = False
else:
	mychanave = True


mstransform(vis=myms,
	outputvis=opms,
	field=field_selection,
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
