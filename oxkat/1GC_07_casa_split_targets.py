# ian.heywood@physics.ox.ac.uk



execfile('oxkat/casa_read_project_info.py')


for i in range(0,len(targets)):
    target = targets[i]
    opms = target_ms[i]


    mstransform(vis=myms,
        outputvis=opms,
        field=target,
        usewtspectrum=True,
        realmodelcol=True,
        datacolumn='corrected')


    flagmanager(vis=opms,
        mode='save',
        versionname='post-1GC')
