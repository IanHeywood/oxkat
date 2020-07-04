#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk


import glob
import numpy
import os.path as o
import pickle
import sys
import time

from astropy.coordinates import SkyCoord
from pyrap.tables import table

sys.path.append(o.abspath(o.join(o.dirname(sys.modules[__name__].__file__), "..")))
from oxkat import config as cfg


def myprint(msg):

    """ Print a message with a timestamp """

    stamp = time.strftime('[%Y-%m-%d %H:%M:%S]:')
    print(stamp+' '+msg)
    return stamp


def get_dummy():

    """ Returns dummy project_info dictionary to set up its structure"""

    project_info = {'master_ms':'myms.ms',
        'nchan':4096,
        'ref_ant':['-1'],
        'primary_name':'1934-638',
        'primary_id':0,
        'primary_tag':'1934',
        'secondary_names':['mysecondary'],
        'secondary_ids':[1],
        'secondary_dirs':[(180.5,-56.0)],
        'target_names':['mytarget'],
        'target_ids':[2],
        'target_dirs':[(180.0,-56.8)],
        'target_cal_map':[0],
        'target_ms':['mytarget.ms']}

    return project_info


def calcsep(ra0,dec0,ra1,dec1):

    """ Returns angular separation between ra0,dec0 and ra1,dec1 in degrees"""

    c1 = SkyCoord(str(ra0)+'deg',str(dec0)+'deg',frame='fk5')
    c2 = SkyCoord(str(ra1)+'deg',str(dec1)+'deg',frame='fk5')
    sep = c1.separation(c2)
    return sep.value


def get_refant(myms,field_id):

    """ Sorts a list of antennas in order of increasing flagged percentages based on field_id """

    ant_names = get_antnames(myms)
    main_tab = table(myms,ack='False')
    
    ref_pool = cfg.CAL_1GC_REF_POOL
    
    pc_list = []
    idx_list = []

    main_tab = table(myms,ack=False)
    field_id = 0
    for i in range(0,len(ref_pool)):
        ant = ref_pool[i]
        if ant in ant_names:
            idx = ant_names.index(ant)
            mytaql = 'ANTENNA1=={idx} || ANTENNA2=={idx} && FIELD_ID=={field_id}'.format(**locals())
            sub_tab = main_tab.query(query=mytaql)
            flags = sub_tab.getcol('FLAG')
            vals,counts = numpy.unique(flags,return_counts=True)
            if len(vals) == 1 and vals == True:
                flag_pc = 100.0
            elif len(vals) == 1 and vals == False:
                flag_pc = 0.0
            else:
                flag_pc = 100.*round(float(counts[1])/float(numpy.sum(counts)),8)
            if flag_pc < 80.0:
                pc_list.append(flag_pc)
                idx_list.append(str(idx))
            myprint('Antenna '+str(idx)+':'+ant+' is '+str(round(flag_pc,2))+chr(37)+' flagged')
    pc_list = numpy.array(pc_list)
    idx_list = numpy.array(idx_list)

    ref_idx = idx_list[numpy.where(pc_list==(numpy.min(pc_list)))][0]

    ranked_list = [x for _,x in sorted(zip(pc_list,idx_list))]
    ranked_list = ','.join(ranked_list)

    return ranked_list


def get_nchan(myms):

    """ Returns the number of channels in myms.
    Only works for data with a single SPW
    """

    spw_table = table(myms+'/SPECTRAL_WINDOW',ack=False)
    nchan = spw_table.getcol('NUM_CHAN')[0]
    spw_table.close()
    myprint('MS has '+str(nchan)+' channels')
    return nchan


def get_antnames(myms):

    """ Returns a list of the antenna names in myms """

    ant_tab = table(myms+'/ANTENNA',ack=False)
    ant_names = ant_tab.getcol('NAME')
    ant_names = [a.lower() for a in ant_names]
    ant_tab.close()
    return ant_names


def get_fields(myms):

    """ Returns lists of directions, names and integer source IDs
    from the FIELD table of myms
    """

    field_tab = table(myms+'/FIELD',ack=False)
    field_dirs = field_tab.getcol('REFERENCE_DIR')*180.0/numpy.pi
    field_names = field_tab.getcol('NAME')
    field_ids = field_tab.getcol('SOURCE_ID')
    field_tab.close()
    return field_dirs,field_names,field_ids


def get_states(myms,
                primary_intent,
                secondary_intent,
                target_intent):

    """ Provide the partial string matches for primary, secondary and target scan
    intents and the corresponding integer STATE_IDs are extracted from the STATE
    table, along with any UNKNOWN states.
    """

    state_tab = table(myms+'/STATE',ack=False)
    modes = state_tab.getcol('OBS_MODE')
    state_tab.close()

    for i in range(0,len(modes)):
        if modes[i] == target_intent:
            target_state = i
        if primary_intent in modes[i]:
            primary_state = i
        if secondary_intent in modes[i]:
            secondary_state = i
        if modes[i] == 'UNKNOWN':
            unknown_state = i

    return primary_state, secondary_state, target_state, unknown_state


def get_primary_candidates(myms,
                primary_state,
                unknown_state,
                field_dirs,
                field_names,
                field_ids):

    """ Automatically identify primary calibrator candidates from myms """

    candidate_ids = []
    candidate_names = []
    candidate_dirs = []

    main_tab = table(myms,ack=False)
    for i in range(0,len(field_ids)):
        field_dir = field_dirs[i]
        field_name = field_names[i]
        field_id = field_ids[i]
        sub_tab = main_tab.query(query='FIELD_ID=='+str(field_id))
        states = numpy.unique(sub_tab.getcol('STATE_ID'))
        for state in states:
            if state == primary_state or state == unknown_state:
                candidate_dirs.append(field_dir)
                candidate_names.append(field_name)
                candidate_ids.append(field_id)
        sub_tab.close()
    main_tab.close()

    return candidate_dirs, candidate_names, candidate_ids


def get_secondaries(myms,
                secondary_state,
                field_dirs,
                field_names,
                field_ids):

    """ Automatically identify secondary calibrators from myms """

    secondary_ids = []
    secondary_names = []
    secondary_dirs = []

    main_tab = table(myms,ack=False)
    for i in range(0,len(field_ids)):
        field_dir = field_dirs[i]
        field_name = field_names[i]
        field_id = field_ids[i]
        sub_tab = main_tab.query(query='FIELD_ID=='+str(field_id))
        states = numpy.unique(sub_tab.getcol('STATE_ID'))
        for state in states:
            if state == secondary_state:
                secondary_dirs.append(field_dir)
                secondary_names.append(field_name)
                secondary_ids.append(field_id)
        sub_tab.close()
    main_tab.close()

    return secondary_dirs, secondary_names, secondary_ids


def get_targets(myms,
                target_state,
                field_dirs,
                field_names,
                field_ids):

    """ Automatically identify secondary calibrators from myms"""

    target_ids = []
    target_names = []
    target_dirs = []

    main_tab = table(myms,ack=False)
    for i in range(0,len(field_ids)):
        field_dir = field_dirs[i]
        field_name = field_names[i]
        field_id = field_ids[i]
        sub_tab = main_tab.query(query='FIELD_ID=='+str(field_id))
        states = numpy.unique(sub_tab.getcol('STATE_ID'))
        for state in states:
            if state == target_state:
                target_dirs.append(field_dir)
                target_names.append(field_name)
                target_ids.append(field_id)
        sub_tab.close()
    main_tab.close()

    return target_dirs, target_names, target_ids


def get_primary_tag(candidate_dirs,
                candidate_names,
                candidate_ids):

    """ Use a positional match to identify whether a source is 1934 or 0408 
    from a list of candidates
    """

    # Tags and positions for the preferred primary calibrators
    preferred_cals = [('1934',294.85427795833334,-63.71267375),
        ('0408',62.084911833333344,-65.75252238888889)]

    print(candidate_names)

    primary_tag = ''

    for i in range(0,len(candidate_dirs)):
        candidate_dir = candidate_dirs[i][0]
        candidate_name = candidate_names[i]
        candidate_id = candidate_ids[i]

        for cal in preferred_cals:
            primary_sep = calcsep(candidate_dir[0],candidate_dir[1],cal[1],cal[2])
            if primary_sep < 3e-3:
                primary_name = candidate_name
                primary_id = candidate_id
                primary_tag = cal[0]

    if primary_tag == '':
        myprint('Automated processing only works when the primary calibrator is PKS B1934-638 or PKS 0408-645.')
        sys.exit()

    return primary_name,primary_id,primary_tag,primary_sep


def target_cal_pairs(target_dirs,target_names,target_ids,
                secondary_dirs,secondary_names,secondary_ids):

    # The target_cal_map is a list of secondary field IDs of length target_ids
    # It links a specific secondary to a specific target
    target_cal_map = []
    target_cal_separations = []

    for i in range(0,len(target_dirs)):
        ra_target = target_dirs[i][0][0]
        dec_target = target_dirs[i][0][1]
        separations = []
        for j in range(0,len(secondary_dirs)):
            ra_cal = secondary_dirs[j][0][0]
            dec_cal = secondary_dirs[j][0][1]
            separations.append(calcsep(ra_target,dec_target,ra_cal,dec_cal))
        separations = numpy.array(separations)
        secondary_index = numpy.where(separations == numpy.min(separations))[0][0]

        target_cal_map.append(secondary_ids[secondary_index])
        target_cal_separations.append(round(separations[secondary_index],3))

    return target_cal_map,target_cal_separations



def target_ms_list(myms,target_names):

    """ Return a list of MS names derived from target_names """

    target_ms = []
    for target in target_names:
        ms_name = myms.replace('.ms','_'+target.replace(' ','_')+'.ms')
        target_ms.append(ms_name)

    return target_ms


def main():

    myms = sys.argv[1].rstrip('/')

    myprint('Examining '+myms)
    myprint('Please wait...')

    outpick = 'project_info.p'


    project_info = get_dummy()


    CAL_1GC_PRIMARY = cfg.CAL_1GC_PRIMARY
    CAL_1GC_SECONDARIES = cfg.CAL_1GC_SECONDARIES
    CAL_1GC_TARGETS = cfg.CAL_1GC_TARGETS

    CAL_1GC_REF_ANT = cfg.CAL_1GC_REF_ANT

    CAL_1GC_PRIMARY_INTENT = cfg.CAL_1GC_PRIMARY_INTENT
    CAL_1GC_SECONDARY_INTENT = cfg.CAL_1GC_SECONDARY_INTENT
    CAL_1GC_TARGET_INTENT = cfg.CAL_1GC_TARGET_INTENT


    # ------------------------------------------------------------------------------
    #
    # FIELD INFO

    field_dirs, field_names, field_ids = get_fields(myms)


    # ------------------------------------------------------------------------------
    #
    # NUMBER OF CHANNELS

    nchan = get_nchan(myms)


    # ------------------------------------------------------------------------------
    #
    # STATE IDs

    primary_state, secondary_state, target_state, unknown_state = get_states(myms,
                                                            CAL_1GC_PRIMARY_INTENT,
                                                            CAL_1GC_SECONDARY_INTENT,
                                                            CAL_1GC_TARGET_INTENT)


    # ------------------------------------------------------------------------------
    #
    # PRIMARY CALIBRATOR

    if CAL_1GC_PRIMARY != 'auto':
        candidate_ids = [int(x) for x in CAL_1GC_PRIMARY.split(',')]
        candidate_names = [field_names[i] for i in candidate_ids]
        candidate_dirs = [field_dirs[i][0] for i in candidate_ids]
    else:
        candidate_dirs, candidate_names, candidate_ids = get_primary_candidates(myms,
                                                            primary_state,
                                                            unknown_state,
                                                            field_dirs,
                                                            field_names,
                                                            field_ids)

    primary_name, primary_id, primary_tag, primary_sep = get_primary_tag(candidate_dirs, candidate_names, candidate_ids)

    myprint('Primary calibrator:    '+str(primary_id)+': '+primary_name)
    myprint('                       '+str(round((primary_sep/3600.0),4))+'" from nominal position')
    myprint('')


    # ------------------------------------------------------------------------------
    #
    # REFERENCE ANTENNAS

    if CAL_1GC_REF_ANT == 'auto':
        ref_ant = get_refant(myms,primary_id)
        myprint('Ranked reference antenna ordering: '+str(ref_ant))
    else:
        ref_ant = CAL_1GC_REF_ANT
        myprint('User requested reference antenna ordering: '+str(ref_ant))


    # ------------------------------------------------------------------------------
    #
    # SECONDARY CALIBRATORS

    if CAL_1GC_SECONDARIES != 'auto':
        secondary_ids = [int(x) for x in CAL_1GC_SECONDARIES.split(',')]
        secondary_ids = list(dict.fromkeys(secondary_ids)) # 
        secondary_names = [field_names[i] for i in secondary_ids]
        secondary_dirs = [field_dirs[i] for i in secondary_ids]
    else:
        secondary_dirs, secondary_names, secondary_ids = get_secondaries(myms,
                                                            secondary_state,
                                                            field_dirs,
                                                            field_names,
                                                            field_ids)


    # ------------------------------------------------------------------------------
    #
    # TARGETS

    if CAL_1GC_TARGETS != 'auto':
        target_ids = [int(x) for x in CAL_1GC_TARGETS.split(',')]
        target_names = [field_names[i] for i in target_ids]
        target_dirs = [field_dirs[i][0] for i in target_ids]
    else:
        target_dirs, target_names, target_ids = get_targets(myms,
                                                            target_state,
                                                            field_dirs,
                                                            field_names,
                                                            field_ids)


    # ------------------------------------------------------------------------------
    #
    # MATCH TARGET-CAL PAIRS BASED ON SEPARATION

    if CAL_1GC_SECONDARIES == 'auto':
        target_cal_map,target_cal_separations = target_cal_pairs(target_dirs,target_names,target_ids,
                                                    secondary_dirs,secondary_names,secondary_ids)
    else:
        target_cal_map = [int(x) for x in CAL_1GC_SECONDARIES.split(',')]
        if len(target_cal_map) != len(target_dirs) and len(target_cal_map) > 1:
            myprint('Target-secondary mapping is ambiguous, reverting to auto')
            target_cal_map,target_cal_separations = target_cal_pairs(target_dirs,target_names,target_ids,
                                                    secondary_dirs,secondary_names,secondary_ids)
        elif len(target_cal_map) == 1:
            myprint('User requested field '+str(target_cal_map)+' as secondary calibrator for all targets')
            target_cal_map = target_cal_map * len(target_dirs)


    # ------------------------------------------------------------------------------
    #
    # GENERATE LIST OF TARGET MS NAMES

    target_ms = target_ms_list(myms,target_names)


    # ------------------------------------------------------------------------------
    #
    # PRINT FIELD SUMMARY


    myprint('')

    myprint('Target                   Secondary                Separation')
    for i in range(0,len(target_dirs)):
        targ = str(target_ids[i])+': '+target_names[i]
        j = target_cal_map[i]
        k = secondary_ids.index(j)
        pcal = str(secondary_ids[k])+': '+secondary_names[k]

        # Re-calculate separations in case of user-specified pairings that don't invoke 
        # the automatic calculation
        ra_target = target_dirs[i][0][0]
        dec_target = target_dirs[i][0][1]
        separations = []
        ra_cal = secondary_dirs[k][0][0]
        dec_cal = secondary_dirs[k][0][1]
        sep = round(calcsep(ra_target,dec_target,ra_cal,dec_cal),3)
        sep = str(sep)+' deg'

        myprint('%-24s %-24s %-9s' % (targ, pcal, sep))
    
    myprint('')

    myprint('Target                   Eventual MS name')
    for i in range(0,len(target_dirs)):
        targ = str(target_ids[i])+': '+target_names[i]
        myprint('%-24s %-50s' % (targ, target_ms[i]))
    
    myprint('')
    myprint('Writing '+outpick)

    project_info['master_ms'] = myms
    project_info['nchan'] = nchan
    project_info['ref_ant'] = ref_ant
    project_info['primary_name'] = primary_name
    project_info['primary_id'] = primary_id
    project_info['primary_tag'] = primary_tag
    project_info['secondary_names'] = secondary_names
    project_info['secondary_ids'] = secondary_ids
    project_info['secondary_dirs'] = secondary_dirs
    project_info['target_names'] = target_names
    project_info['target_dirs'] = target_dirs
    project_info['target_ids'] = target_ids
    project_info['target_cal_map'] = target_cal_map
    project_info['target_ms'] = target_ms

    pickle.dump(project_info,open(outpick,'wb'),protocol=2)

    myprint('Done')


if __name__ == "__main__":


    main()
