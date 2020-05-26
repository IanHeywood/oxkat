#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk


import os.path as o
import pickle
import subprocess
import sys
sys.path.append(o.abspath(o.join(o.dirname(sys.modules[__name__].__file__), "..")))


from oxkat import generate_jobs as gen
from oxkat import config as cfg


def main():


    VISPLOTS = cfg.VISPLOTS
    gen.setup_dir(VISPLOTS)


    project_info = pickle.load(open('project_info.p','rb'), encoding = 'latin1')
    myms = project_info['master_ms']
    bpcal = project_info['primary_id']
    pcals = project_info['secondary_ids']
    targets = project_info['target_ids'] 

    fields = [bpcal]
    for pcal in pcals:
        fields.append(pcal)

    plots = [('--xaxis CORRECTED_DATA:real:XX,CORRECTED_DATA:real:YY --yaxis CORRECTED_DATA:imag:XX,CORRECTED_DATA:imag:YY'),
#        ('--xaxis FREQ,FREQ --yaxis CORRECTED_DATA:amp:XX,CORRECTED_DATA:amp:YY --iter-scan --colour-by ANTENNA1')
        ('--xaxis FREQ,FREQ --yaxis CORRECTED_DATA:amp:XX,CORRECTED_DATA:amp:YY'),
        ('--xaxis UV,UV,UV,UV --yaxis CORRECTED_DATA:amp:XX,CORRECTED_DATA:amp:YY,CORRECTED_DATA:phase:XX,CORRECTED_DATA:phase:YY')]


    shadems_base = 'shadems --dir '+VISPLOTS+' '

    for field in fields:
        for plot in plots:
            syscall = shadems_base+' '+plot+' --field '+field+' '+myms
            subprocess.run([syscall],shell=True)


if __name__ == "__main__":


    main()