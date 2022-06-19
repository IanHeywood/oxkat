#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk


import json
import os.path as o
import subprocess
import sys
sys.path.append(o.abspath(o.join(o.dirname(sys.modules[__name__].__file__), "..")))


from oxkat import generate_jobs as gen
from oxkat import config as cfg



def main():


    VISPLOTS = cfg.VISPLOTS
    gen.setup_dir(VISPLOTS)


    with open('project_info.json') as f:
        project_info = json.load(f)


    myms = project_info['working_ms']
    bpcal = project_info['primary_id']
    pcals = project_info['secondary_ids']
    targets = project_info['target_ids'] 

    if cfg.PRE_FIELDS != '':
        from oxkat import user_field_handler as ufh
        pcals = ufh.user_pcal_ids

    fields = [bpcal]
    for pcal in pcals:
        fields.append(pcal)

    plots = ['--xaxis CORRECTED_DATA:real:XX,CORRECTED_DATA:real:YY --yaxis CORRECTED_DATA:imag:XX,CORRECTED_DATA:imag:YY',
        '--xaxis FREQ,FREQ --yaxis CORRECTED_DATA:amp:XX,CORRECTED_DATA:amp:YY',
        '--xaxis FREQ,FREQ --yaxis CORRECTED_DATA:phase:XX,CORRECTED_DATA:phase:YY',
        '--xaxis UV,UV,UV,UV --yaxis CORRECTED_DATA:amp:XX,CORRECTED_DATA:amp:YY,CORRECTED_DATA:phase:XX,CORRECTED_DATA:phase:YY']

    colour_by = ['--colour-by ANTENNA1 --cnum 64',
        '--colour-by SCAN_NUMBER --cnum 48 ']

#    shadems_base = 'shadems --profile --dir '+VISPLOTS+' '
    shadems_base = 'shadems --dir '+VISPLOTS+' '

    for field in fields:
        for plot in plots:
            for col in colour_by:
                syscall = shadems_base+' '+plot+' '+col+' --field '+str(field)+' '+myms
                subprocess.run([syscall],shell=True)


if __name__ == "__main__":


    main()
