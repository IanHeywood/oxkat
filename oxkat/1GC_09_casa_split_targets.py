# ian.heywood@physics.ox.ac.uk


execfile('oxkat/casa_read_project_info.py')
execfile('oxkat/config.py')

if PRE_FIELDS != '':
    targets = user_targets

for target in target_names:

    opms = ''

    for mm in target_ms:
        if target in mm:
            opms = mm

    if opms != '':

        mstransform(vis=myms,
            outputvis=opms,
            field=target,
            usewtspectrum=True,
            realmodelcol=True,
            datacolumn='corrected')

        if SAVE_FLAGS:
            flagmanager(vis=opms,
                mode='save',
                versionname='post-1GC')

    else:

        print('Target/MS mismatch in project info for '+target+', please check.')