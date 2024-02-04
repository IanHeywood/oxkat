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


    GAINPLOTS = cfg.GAINPLOTS
    GAINTABLES = cfg.GAINTABLES
    gen.setup_dir(GAINPLOTS)

    include = sys.argv[1]
    include = include.split(',')
    if len(sys.argv) > 2:
        exclude = sys.argv[2]
        exclude = exclude.split(',')
    else:
        exclude = ['']

    exclude.append('.flagversions')

    for suffix in include:
        if suffix not in exclude:
            caltabs = glob.glob(GAINTABLES+'/*.'+suffix)
            for caltab in caltabs:
                htmlname = GAINPLOTS+'/'+caltab.split('/')[-1]+'.html'
                plotname = GAINPLOTS+'/'+caltab.split('/')[-1]+'.png'
                syscall = 'ragavi-gains -t '+caltab+' --htmlname '+htmlname+' --plotname '+plotname+' '
                if suffix in ['D','KX']:
                    syscall += '--xaxis antenna'
                subprocess.run([syscall],shell=True)



if __name__ == "__main__":


    main()