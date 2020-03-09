# ian.heywood@physics.ox.ac.uk

import pickle


project_info = pickle.load(open('project_info.p','rb'))
myms = project_info['master_ms']
bpcal = project_info['primary'][1]
pcals = project_info['secondary']
targets = project_info['target_list'] 


code = myms.split('/')[-1].split('_')[0]

opms = code+'_calibrators.ms'


field_selection = [bpcal]
for pcal in pcals:
	field_selection.append(pcal[1])

field_selection = ','.join(sorted(field_selection))


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


#fixvis(vis=opms,reuse=False)