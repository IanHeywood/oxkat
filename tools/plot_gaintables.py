#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk


import glob
import os.path as o
import pickle
import subprocess
import sys
sys.path.append(o.abspath(o.join(o.dirname(sys.modules[__name__].__file__), "../")))


from oxkat import generate_jobs as gen


def main():


    GAINPLOTS = gen.GAINPLOTS
    gen.setup_dir(GAINPLOTS)


    caltabs = sorted(glob.glob('cal_*'))


    for caltab in caltabs:

        gaintype = caltab.split('.')[-1][0].upper()
        opfile = GAINPLOTS+'/'+caltab
        syscall = 'ragavi-gains -g '+gaintype+' -t '+caltab+' --htmlname='+opfile
        subprocess.run([syscall],shell=True)


if __name__ == "__main__":


    main()