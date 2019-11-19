# ian.heywood@physics.ox.ac.uk


import pickle
import numpy


project_info = pickle.load(open('project_info.p','rb'))


myms = project_info['master_ms']
edge_flags = project_info['edge_flags']
nchan = project_info['nchan']
end_chan = int(nchan-edge_flags)


clearstat()
clearstat()


# First two are band-edges, last one is Galactic HI line
badfreqs = ['850~900MHz','1658~1800MHz','944~947MHz','1160~1310MHz','1476~1611MHz','1419.8~1421.3MHz']
for badfreq in badfreqs:
	badspw = '*:' + badfreq
	flagdata(vis=myms, mode='manual', spw=badspw)


flagdata(vis=myms,mode='quack',quackinterval=8.0,quackmode='beg')
# flagdata(vis=myms,mode='manual',spw='0:0~'+str(edge_flags))
# flagdata(vis=myms,mode='manual',spw='0:'+str(end_chan)+'~'+str(nchan))
flagdata(vis=myms,mode='manual',autocorr=True)
flagdata(vis=myms,mode='clip',clipzeros=True)
flagdata(vis=myms,mode='clip',clipminmax=[0.0,100.0])


flagmanager(vis=myms,mode='save',versionname='basic')


clearstat()
clearstat()
