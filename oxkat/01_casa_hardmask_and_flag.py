# ianh@astro.ox.ac.uk


import glob
import sys
import numpy
import os
import shutil
import pickle


project_info = pickle.load(open('project_info.p','rb'))


def ranges(nums):
    nums = sorted(set(nums))
    gaps = [[s, e] for s, e in zip(nums, nums[1:]) if s+1 < e]
    edges = iter(nums[:1] + sum(gaps, []) + nums[-1:])
    return list(zip(edges, edges))


myms = project_info['master_ms']
opms = myms.replace('.ms','_wtspec.ms')
edge_flags = project_info['edge_flags']
rfimask = 'labelled_rfimask.5jun17.pickle.npy'


if not os.path.isfile(rfimask):
	os.system('wget http://www-astro.physics.ox.ac.uk/~ianh/labelled_rfimask.5jun17.pickle.npy')


flags = numpy.load(rfimask)
ref_freqs = flags[1]['chans']
ref_flags = flags[0]['chans']

tb.open(myms+'/SPECTRAL_WINDOW')
ms_freqs = tb.getcol('CHAN_FREQ')
ms_flags = []


clipfactor = 4096.0/float(len(ms_freqs))
lowclip = int(1280.0/clipfactor)


for i in range(0,len(ms_freqs)-1):
	f0 = ms_freqs[i]
	f1 = ms_freqs[i+1]
	mask = (ref_freqs >= f0) & (ref_freqs < f1)
	temp = ref_flags[mask]
	if 1 in temp:
		ms_flags.append(i)


#pc = str(100.0*round(float(len(ms_flags))/float(len(ms_freqs)),2))
chanranges = ranges(ms_flags)


spwstr = '0:'
for i in range(0,len(chanranges)):
	tmpstr = str(chanranges[i][0])+'~'+str(chanranges[i][1])
	if i != (len(chanranges) - 1):
		tmpstr += ';'
	spwstr += tmpstr


mid_chan = int(len(ms_freqs)/2.0)
end_chan = int(len(ms_freqs))-edge_flags


flagdata(vis=myms,mode='manual',spw=spwstr)
flagdata(vis=myms,mode='manual',autocorr=True)
flagdata(vis=myms,mode='clip',clipzeros=True)
flagdata(vis=myms,mode='clip',clipminmax=[0.0,50.0])
flagdata(vis=myms,mode='tfcrop')
flagdata(vis=myms,mode='extend',growaround=True,flagneartime=True,flagnearfreq=True,growtime=90.0,growfreq=90.0)


mstransform(vis=myms,
	outputvis=opms,
	datacolumn='data',
	chanaverage=False,
	timeaverage=False,
	realmodelcol=True,
	usewtspectrum=True)


