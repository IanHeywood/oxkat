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


    suffix = sys.argv[1]

    VISPLOTS = cfg.VISPLOTS
    gen.setup_dir(VISPLOTS)


    with open('project_info.json') as f:
        project_info = json.load(f)


    myms = project_info['working_ms']
    polcal = project_info['polcal_id']
    

    plots = ['--xaxis CORRECTED_DATA:real:XX,CORRECTED_DATA:real:YY --yaxis CORRECTED_DATA:imag:XX,CORRECTED_DATA:imag:YY',
        '--xaxis CORRECTED_DATA:real:XY,CORRECTED_DATA:real:YX --yaxis CORRECTED_DATA:imag:XY,CORRECTED_DATA:imag:YX',
        '--xaxis FREQ,FREQ,FREQ,FREQ --yaxis CORRECTED_DATA:amp:XX,CORRECTED_DATA:amp:XY,CORRECTED_DATA:amp:YX,CORRECTED_DATA:amp:YY',
        '--xaxis FREQ,FREQ,FREQ,FREQ --yaxis CORRECTED_DATA:phase:XX,CORRECTED_DATA:phase:XY,CORRECTED_DATA:phase:YX,CORRECTED_DATA:phase:YY',
        '--xaxis FREQ,FREQ,FREQ,FREQ --yaxis CORRECTED_DATA:amp:I,CORRECTED_DATA:amp:Q,CORRECTED_DATA:amp:U,CORRECTED_DATA:amp:V',
        '--xaxis FREQ,FREQ,FREQ,FREQ --yaxis CORRECTED_DATA:phase:I,CORRECTED_DATA:phase:Q,CORRECTED_DATA:phase:U,CORRECTED_DATA:phase:V']


    shadems_base = 'shadems --dir '+VISPLOTS+' '

    for plot in plots:
        syscall = shadems_base+' '+plot+' --colour-by ANTENNA1 --cnum 64 --field '+str(polcal)+' --suffix '+suffix+' '+myms
        subprocess.run([syscall],shell=True)


if __name__ == "__main__":


    main()
