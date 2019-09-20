#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk


import numpy
import sys
import glob
import pickle
from pyrap.tables import table
from astropy.coordinates import SkyCoord



def calcsep(ra0,dec0,ra1,dec1):
    c1 = SkyCoord(str(ra0)+'deg',str(dec0)+'deg',frame='fk5')
    c2 = SkyCoord(str(ra1)+'deg',str(dec0)+'deg',frame='fk5')
    sep = c1.separation(c2)
    return sep.value


def get_nchan(myms):
    spw_table = table(myms+'/SPECTRAL_WINDOW',ack=False)
    nchan = spw_table.getcol('NUM_CHAN')[0]
    spw_table.close()
    return nchan


def get_antnames(myms):
    ant_tab = table(myms+'/ANTENNA',ack=False)
    ant_names = ant_tab.getcol('NAME')
    ant_names = [a.lower() for a in ant_names]
    ant_tab.close()
    return ant_names


def get_field_info(myms,
                target='TARGET',
                primary='BANDPASS',
                secondary='PHASE'):


    # Tags and positions for the preferred primary calibrators
    cals = [('1934',294.85427795833334,-63.71267375),
        ('0408',62.084911833333344,-65.75252238888889)]


    state_tab = table(myms+'/STATE',ack=False)
    modes = state_tab.getcol('OBS_MODE')
    state_tab.close()


    for i in range(0,len(modes)):
        if modes[i] == target:
            target_state = i
        if primary in modes[i]:
            primary_state = i
        if secondary in modes[i]:
            secondary_state = i
        if modes[i] == 'UNKNOWN':
            unknown_state = i


    print 'Target state:',target_state
    print 'Primary state:',primary_state
    print 'Secondary state:',secondary_state


    field_tab = table(myms+'/FIELD',ack=False)
    names = field_tab.getcol('NAME')
    dirs = field_tab.getcol('REFERENCE_DIR')
    field_tab.close()


    primary_candidates = []
    secondary_fields = []
    target_list = []


    main_tab = table(myms,ack=False)
    for i in range(0,len(names)):
        sub_tab = main_tab.query(query='FIELD_ID=='+str(i))
        state = numpy.unique(sub_tab.getcol('STATE_ID'))
        print i,names[i],state
        if state == primary_state or state == unknown_state:
            primary_dir = dirs[i][0,:]*180.0/numpy.pi
            primary_candidates.append((names[i],str(i),primary_dir))
        if state == secondary_state:
            secondary_dir = dirs[i][0,:]*180.0/numpy.pi
            secondary_fields.append((names[i],str(i),secondary_dir))

    print('primary_fields:',primary_candidates)

    for primary_candidate in primary_candidates:
        primary_dir = primary_candidate[2]
        for cal in cals:
            sep = calcsep(primary_dir[0],primary_dir[1],cal[1],cal[2])
            if sep < 1e-4: # and project_info['primary_name'] == 'UNKNOWN':
                primary_field = (primary_candidate[0],primary_candidate[1])
                primary_tag = cal[0]


    for i in range(0,len(names)):
        sub_tab = main_tab.query(query='FIELD_ID=='+str(i))
        state = numpy.unique(sub_tab.getcol('STATE_ID'))
        if state == target_state:
            target_ms = myms.replace('.ms','_'+names[i].replace('+','p')+'.ms')
            target_dir =  dirs[i][0,:]*180.0/numpy.pi
            seps = []
            for secondary_field in secondary_fields:
                secondary_dir = secondary_field[2]
                sep = calcsep(target_dir[0],target_dir[1],secondary_dir[0],secondary_dir[1])
                seps.append(sep)
            seps = numpy.array(seps)
            secondary_idx = numpy.where(seps==numpy.min(seps))[0][0]


            target_list.append((names[i],str(i),target_ms,secondary_idx))
#            project_info['target'] = [names[i],str(i)]


    return primary_field,primary_tag,secondary_fields,target_list


def get_refant(myms,field_id):

    ant_names = get_antnames(myms)

    ref_pool = ['m000','m001','m002','m003','m004','m006']
    pc_list = numpy.ones(len(ref_pool))*100.0
    idx_list = numpy.zeros(len(ref_pool),dtype=numpy.int8)


    for i in range(0,len(ref_pool)):
        ant = ref_pool[i]
        try:
            idx = ant_names.index(ant)
            sub_tab = main_tab.query(query='ANTENNA1=='+str(idx)+' && FIELD_ID=='+str(field_id))
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

    return ref_idx


def main():


    myms = sys.argv[1].rstrip('/')


    outpick = 'project_info.p'


    # Setup template dictionary populated with dummy values

    project_info = {'primary':['0','0'],
        'primary_tag':'UNKNOWN',
        'secondary':['1','1'],
        'target_list':['2','2'],
        'ref_ant':'-1',
        'master_ms':myms,
        'nchan':4096,
        'edge_flags':120,
        'k0':2120,
        'k1':3120}


    nchan = get_nchan(myms)
    ant_names = get_antnames(myms)
    primary_field,primary_tag,secondary_field,target_list = get_field_info(myms)
    ref_ant = get_refant(myms,primary_field[1])
    project_info['primary'] = primary_field
    project_info['primary_tag'] = primary_tag
    project_info['secondary'] = secondary_field
    project_info['target_list'] = target_list 
    project_info['ref_ant'] = str(ref_ant)
    project_info['nchan'] = nchan
    edge_flags = int(120*nchan/4096)
    project_info['edge_flags'] = edge_flags
    k0 = int(2120*nchan/4096)
    k1 = int(3120*nchan/4096)
    project_info['k0'] = k0
    project_info['k1'] = k1


    pickle.dump(project_info,open(outpick,'wb'))
    

    print(project_info)

    print('')
    print('Here is what I have assumed about your fields:')
    print('')
    print('Primary calibrator:  '+primary_field[0])
    print('')
    for i in range(0,len(target_list)):
        print('Target '+str(i)+':            '+target_list[i][0])
        print('Associated with: '+secondary_field[target_list[i][3]][0])
        print('')

if __name__ == "__main__":


    main()
