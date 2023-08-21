#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk


import glob
import os
import os.path as o
import subprocess
import sys
sys.path.append(o.abspath(o.join(o.dirname(sys.modules[__name__].__file__), "..")))


from oxkat import generate_jobs as gen
from oxkat import config as cfg



def main():

    myms = sys.argv[1]
    solname = sys.argv[2]

    plotargs = ['--corr0 0 --corr1 0 --iterfreq',
                '--corr0 1 --corr1 1 --iterfreq',
                '--corr0 0 --corr1 0 --iterdir',
                '--corr0 1 --corr1 1 --iterdir',]

    TOOLS = cfg.TOOLS
    GAINPLOTS = cfg.GAINPLOTS
    gen.setup_dir(GAINPLOTS)

    kmstab = myms.rstrip('/')+'/killMS.'+solname+'.sols.npz'

    for plotarg in plotargs:
        syscall = 'python3 '+TOOLS+'/plot_killMS.py '+plotarg+' --outdir '+GAINPLOTS+' '+kmstab
        subprocess.run([syscall],shell=True)


if __name__ == "__main__":


    main()