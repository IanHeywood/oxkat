#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk


import glob
import os
import os.path as o
import pickle
import subprocess
import sys
sys.path.append(o.abspath(o.join(o.dirname(sys.modules[__name__].__file__), "..")))


from oxkat import generate_jobs as gen
from oxkat import config as cfg


def main():


    GAINPLOTS = gen.GAINPLOTS
    gen.setup_dir(GAINPLOTS)


    caltabs = sorted([item for item in glob.glob('cal_*') if not os.path.basename(item).endswith('flagversions')])


    for caltab in caltabs:

        gaintype = caltab.split('.')[-1][0].upper()
        opfile = GAINPLOTS+'/'+caltab
        if not os.path.isfile(opfile):
            syscall = 'ragavi-gains -g '+gaintype+' -t '+caltab+' --htmlname='+opfile
            subprocess.run([syscall],shell=True)
        else:
            print(opfile+' exists, skipping')

if __name__ == "__main__":


    main()