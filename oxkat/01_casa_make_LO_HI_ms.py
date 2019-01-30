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
edge_flags = project_info['edge_flags']


tb.open(myms+'/SPECTRAL_WINDOW')
ms_freqs = tb.getcol('CHAN_FREQ')


clipfactor = 4096.0/float(len(ms_freqs))
lowclip = int(1280.0/clipfactor)


mid_chan = int(len(ms_freqs)/2.0)
end_chan = int(len(ms_freqs))-edge_flags


loms = project_info['lo_ms']


mstransform(vis=myms,
	outputvis=loms,
	datacolumn='data',
	spw='0:'+str(edge_flags)+'~'+str(lowclip),
	chanaverage=False,
	timeaverage=False,
	realmodelcol=True,
	usewtspectrum=True)


hims = project_info['hi_ms']


mstransform(vis=myms,
        outputvis=hims,
        datacolumn='data',
        spw='0:'+str(mid_chan)+'~'+str(end_chan),
        chanaverage=False,
        timeaverage=False,
        realmodelcol=True,
        usewtspectrum=True)


if not os.path.isdir('LO'):
	os.mkdir('LO')
if not os.path.isdir('HI'):
	os.mkdir('HI')


shutil.move(loms,'LO/'+loms)
shutil.move(hims,'HI/'+hims)
shutil.copy('project_info.p','LO/project_info.p')
shutil.copy('project_info.p','HI/project_info.p')
