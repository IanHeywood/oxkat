# ianh@astro.ox.ac.uk


import glob
import numpy



myms = glob.glob('*.ms')[0]


tb.open(myms+'/SPECTRAL_WINDOW')
ms_freqs = tb.getcol('CHAN_FREQ')
tb.done()


edge_flags = 120
n_chan = len(ms_freqs)
end_chan = int(n_chan-edge_flags)


badfreqs = [ '944~947MHz','1160~1310MHz','1476~1611MHz','1670~1700MHz']

for badfreq in badfreqs:
	badspw = '0:' + badfreq
	flagdata(vis=myms, mode='manual', spw=badspw)


flagdata(vis=myms,mode='manual',spw='0:0~'+str(edge_flags))

flagdata(vis=myms,mode='manual',spw='0:'+str(end_chan)+'~'+str(n_chan))

flagdata(vis=myms,mode='manual',autocorr=True)

flagdata(vis=myms,mode='clip',clipzeros=True)

flagdata(vis=myms,mode='clip',clipminmax=[0.0,50.0])

flagdata(vis=myms,mode='tfcrop')

flagdata(vis=myms,mode='extend',growaround=True,flagneartime=True,flagnearfreq=True,growtime=90.0,growfreq=90.0)
