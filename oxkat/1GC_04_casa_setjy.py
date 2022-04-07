# ian.heywood@physics.ox.ac.uk


import glob
import shutil
import time


execfile('oxkat/casa_read_project_info.py')
execfile('oxkat/config.py')


args = sys.argv
for item in sys.argv:
    parts = item.split('=')
    if parts[0] == 'myms':
        myms = parts[1]


tb.open(myms)
colnames = tb.colnames()
tb.done()



# ------- Setjy models


if primary_tag == '1934':
    setjy(vis=myms,
        field=bpcal_name,
        standard='Stevens-Reynolds 2016',
        scalebychan=True,
        usescratch=True)
    
    
elif primary_tag == '0408':
    bpcal_mod = CAL_1GC_0408_MODEL
    setjy(vis=myms,
        field=bpcal_name,
        standard='manual',
        fluxdensity=bpcal_mod[0],
        spix=bpcal_mod[1],
        reffreq=bpcal_mod[2],
        scalebychan=True,
        usescratch=True)


elif primary_tag == 'other':
    setjy(vis=myms,
        field=bpcal_name,
        standard='Perley-Butler 2013',
        scalebychan=True,
        usescratch=True)
