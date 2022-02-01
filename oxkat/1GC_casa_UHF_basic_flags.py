# ian.heywood@physics.ox.ac.uk
# UHF calibration is experimental


import numpy


execfile('oxkat/casa_read_project_info.py')


args = sys.argv
for item in sys.argv:
    parts = item.split('=')
    if parts[0] == 'myms':
        myms = parts[1]


clearstat()
clearstat()


# ------------------------------------------------------------------------
# Band edges

badfreqs = ['540~570MHz', '1010~1150MHz']

myspw = ''
for badfreq in badfreqs:
	myspw += '*:'+badfreq+','
myspw = myspw.rstrip(',')

flagdata(vis = myms, 
	mode = 'manual', 
	spw = myspw)



# ------------------------------------------------------------------------
# Clipping, quacking, zeros, autos
# Note that clip will always flag NaN/Inf values even with a range 

#flagdata(vis = myms,
#	mode = 'quack',
#	quackinterval = 8.0,
#	quackmode = 'beg')

flagdata(vis = myms,
	mode = 'manual',
	autocorr = True)

flagdata(vis = myms,
	mode = 'clip',
	clipzeros = True)

flagdata(vis = myms,
	mode = 'clip',
	clipminmax = [0.0,200.0])

# ------------------------------------------------------------------------
# Save the flags

flagmanager(vis = myms,
	mode = 'save',
	versionname = 'basic')


clearstat()
clearstat()
