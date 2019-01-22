#!/usr/bin/env python
# ianh@astro.ox.ac.uk


from pyrap.tables import table
import numpy
import sys
import glob
import pickle
from astropy.coordinates import SkyCoord


def calcsep(ra0,dec0,ra1,dec1):
    c1 = SkyCoord(ra0+'deg',dec0+'deg',frame='fk5')
    c2 = SkyCoord(ra1+'deg',dec0+'deg',frame='fk5')
    sep = c1.separartion(c2)
    return sep.value


myms = sys.argv[1].rstrip('/')


# Positions and labels for the preferred primary calibrators

cals = [('1934',294.85427795833334,-63.71267375),
    ('0408',62.084911833333344,-65.75252238888889)]


# Last three digits of the SB ID, for slurm queue labels, etc.
code = myms.split('/')[-1].split('_')[0][-3:]


# LO and HI Measurement Sets (might ditch this..)
loms = myms.replace('.ms','_LO_wtspec.ms')
hims = hims = myms.replace('.ms','_HI_wtspec.ms')


# Get the number of channels
spw_table = table(myms+'/SPECTRAL_WINDOW',ack=False)
nchan = spw_table.getcol('NUM_CHAN')[0]
spw_table.close()


# Set the number of edge flags scaled by the number of channels
# Set the channels over which to solve for delays
edge_flags = int(120*nchan/4096)
k0 = int(2120*nchan/4096)
k1 = int(3120*nchan/4096)


project_info = {'primary':['0','0'],
    'secondary':['1','1'],
    'target':['2','2'],
    'primary_name':'UNKNOWN',
    'ref_ant':'-1',
    'master_ms':myms,
    'lo_ms':loms,
    'hi_ms':hims,
    'nchan':nchan,
    'edge_flags':edge_flags,
    'k0':k0,
    'k1':k1,
    'code':code}


outpick = 'project_info.p'
ref_pool = ['m000','m001','m002','m003','m004','m006']


state_tab = table(myms+'/STATE',ack=False)
modes = state_tab.getcol('OBS_MODE')
state_tab.close()


for i in range(0,len(modes)):
    if modes[i] == 'TARGET':
        target_state = i
    if 'BANDPASS' in modes[i]:
        primary_state = i
    if 'PHASE' in modes[i]:
        secondary_state = i


field_tab = table(myms+'/FIELD',ack=False)
names = field_tab.getcol('NAME')
dirs = field_tab.getcol('REFERENCE_DIR')
field_tab.close()


main_tab = table(myms,ack=False)
for i in range(0,len(names)):
    sub_tab = main_tab.query(query='FIELD_ID=='+str(i))
    state = numpy.unique(sub_tab.getcol('STATE_ID'))
    if state == primary_state:
        project_info['primary'] = [names[i],str(i)]
        primary_dir = dirs[i][0,:]*180.0/numpy.pi
        for cal in cals:
            sep = calcsep(primary_dir[0],primary_dir[1],cal[1],cal[2])
            if sep < 1e-4 and project_info['primary_name'] == 'UNKNOWN':
                project_info['primary_name'] = cal[0]
    if state == secondary_state:
        project_info['secondary'] = [names[i],str(i)]
    if state == target_state:
        project_info['target'] = [names[i],str(i)]


dx = abs(numpy.array((cals[0][1],cals[1][1])) - primary_dir[0])
dy = abs(numpy.array((cals[0][2],cals[1][2])) - primary_dir[1])
idx = numpy.where(dx==numpy.min(dx))[0][0]
project_info['primary_name'] = cals[idx][0]


ant_tab = table(myms+'/ANTENNA',ack=False)
ant_names = ant_tab.getcol('NAME')
ant_names = [a.lower() for a in ant_names]
ant_tab.close()


pc_list = numpy.ones(len(ref_pool))*100.0
idx_list = numpy.zeros(len(ref_pool),dtype=numpy.int8)
primary_id = project_info['primary'][1]


for i in range(0,len(ref_pool)):
    ant = ref_pool[i]
    try:
        idx = ant_names.index(ant)
        sub_tab = main_tab.query(query='ANTENNA1=='+str(idx)+' && FIELD_ID=='+str(primary_id))
        flags = sub_tab.getcol('FLAG')
        vals,counts = numpy.unique(flags,return_counts=True)
        if len(vals) == 1 and vals == True:
            flag_pc = 100.0
        elif len(vals) == 1 and vals == False:
            flag_pc = 0.0
        else:
            flag_pc = 100.*round(float(counts[1])/float(numpy.sum(counts)),2)
        pc_list[i] = flag_pc
        idx_list[i] = idx
    except:
        continue


ref_idx = idx_list[numpy.where(pc_list==(numpy.min(pc_list)))][0]
project_info['ref_ant'] = str(ref_idx)

for item in project_info:
    print item,project_info[item]


pickle.dump(project_info,open(outpick,'wb'))
