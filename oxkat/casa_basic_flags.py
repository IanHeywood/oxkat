# ian.heywood@physics.ox.ac.uk


import pickle
import numpy


project_info = pickle.load(open('project_info.p','rb'))


myms = project_info['master_ms']


clearstat()
clearstat()


# Band-edges, Galactic HI line
band_edges = ['850~900MHz','1658~1800MHz','1419.8~1421.3MHz']
for badfreq in band_edges:
	badspw = '*:' + badfreq
	flagdata(vis=myms, mode='manual', spw=badspw)


# Satellites etc. (apply baseline cut)
badfreqs = ['944~947MHz','1160~1310MHz','1476~1611MHz']
for badfreq in badfreqs:
	badspw = '*:' + badfreq
	flagdata(vis=myms, mode='manual', spw=badspw,uvrange='<600')


flagdata(vis=myms,mode='quack',quackinterval=8.0,quackmode='beg')
flagdata(vis=myms,mode='manual',autocorr=True)
flagdata(vis=myms,mode='clip',clipzeros=True)
flagdata(vis=myms,mode='clip',clipminmax=[0.0,100.0])


flagmanager(vis=myms,mode='save',versionname='basic')


clearstat()
clearstat()
