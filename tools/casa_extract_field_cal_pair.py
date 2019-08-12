# Find primary cal
# Find nearest secondary cal to each target
# Split a new MS containing primary and secondary-target pairs
# ian.heywood@physics.ox.ac.uk


import numpy
import glob
import sys


myms = glob.glob('*.ms')[0]


tb.open(myms+'/STATE')
modes = tb.getcol('OBS_MODE')
tb.close()


for i in range(0,len(modes)):
    if modes[i] == 'TARGET':
        target_state = i
    if 'BANDPASS' in modes[i]:
        primary_state = i
    if 'PHASE' in modes[i]:
        secondary_state = i


tb.open(myms+'/FIELD')
fld_names = tb.getcol('NAME')
dirs = tb.getcol('REFERENCE_DIR')
tb.close()


myprimary = 'J1939-6342'
myfield = 'GX_339-4'
mysecondary = 'J1744-5144'


opms = myms.replace('.ms','_'+myfield+'.ms')


mstransform(vis=myms,outputvis=opms,field=field_selections[i],usewtspectrum=True,datacolumn='data',realmodelcol=True,chanaverage=True,chanbin=4,timeaverage=False)
