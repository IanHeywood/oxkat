# ian.heywood@physics.ox.ac.uk


execfile('oxkat/casa_read_project_info.py',globals())
execfile('oxkat/config.py',globals())

if PRE_FIELDS != '':
    target_names = user_targets

for i in range(0,len(target_names)):

    target_name = target_names[i]
    target_id = targets[i]
    nscans = str(master_field_list.count(target_id))
    print('Target '+target_name+' has FIELD_ID '+target_id+' and '+nscans+' scans')

    opms = ''

    for mm in target_ms:
        if target_name in mm:
            opms = mm

    if opms != '':

        mstransform(vis=myms,
            outputvis=opms,
            field=target_id,
            usewtspectrum=True,
            createmms=True,
            separationaxis='scan',
            numsubms=nscans,
            realmodelcol=True,
            datacolumn='corrected')

        if SAVE_FLAGS:
            flagmanager(vis=opms,
                mode='save',
                versionname='post-1GC')

    else:

        print('Target/MS mismatch in project info for '+target+', please check.')
