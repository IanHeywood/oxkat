# ian.heywood@physics.ox.ac.uk


import pickle
import numpy


project_info = pickle.load(open('project_info.p','rb'))


master_ms = project_info['master_ms']
code = master_ms.split('/')[-1].split('_')[0]

myms = code+'_calibrators.ms'


clearstat()
clearstat()


# ------------------------------------------------------------------------
# Frequency ranges to flag over all baselines

bandfreqs = ['850~880MHz', # Lower band edge
	'1658~1800MHz', # Upper bandpass edge
	'1419.8~1421.3MHz'] # Galactic HI

myspw = ''
for badfreq in badfreqs:
	myspw += '*:'+badfreq+','
myspw = myspw.rstrip(',')

flagdata(vis = myms, 
	mode = 'manual', 
	spw = myspw)


# ------------------------------------------------------------------------
# Frequency ranges to flag over a subset of baselines
# From the MeerKAT Cookbook
# https://github.com/ska-sa/MeerKAT-Cookbook/blob/master/casa/L-band%20RFI%20frequency%20flagging.ipynb

badfreqs = ['900MHz~915MHz', # GSM and aviation
	'925MHz~960MHz',				
	'1080MHz~1095MHz',
	'1565MHz~1585MHz', # GPS
	'1217MHz~1237MHz',
	'1375MHz~1387MHz',
	'1166MHz~1186MHz',
	'1592MHz~1610MHz', # GLONASS
	'1242MHz~1249MHz',
	'1191MHz~1217MHz', # Galileo
	'1260MHz~1300MHz',
	'1453MHz~1490MHz', # Afristar
	'1616MHz~1626MHZ', # Iridium
	'1526MHz~1554MHz', # Inmarsat
	'1600MHz'] # Alkantpan

myspw = ''
for badfreq in badfreqs:
	myspw += '*:'+badfreq+','
myspw = myspw.rstrip(',')

flagdata(vis = myms,
	mode = 'manual',
	spw = myspw,
	uvrange = '<600')


# ------------------------------------------------------------------------
# Clipping, quacking, zeros, autos
# Note that clip will always flag NaN/Inf values even with a range 

flagdata(vis = myms,
	mode = 'quack',
	quackinterval = 8.0,
	quackmode = 'beg')

flagdata(vis = myms,
	mode = 'manual',
	autocorr = True)

flagdata(vis = myms,
	mode = 'clip',
	clipzeros = True)

flagdata(vis = myms,
	mode = 'clip',
	clipminmax = [0.0,100.0])


# ------------------------------------------------------------------------
# Run autoflaggers

flagdata(vis=myms,datacolumn='data',mode='tfcrop')
flagdata(vis=myms,datacolumn='data',mode='rflag')


# ------------------------------------------------------------------------
# Save the flags

flagmanager(vis=myms,mode='save',versionname='basic')


clearstat()
clearstat()
