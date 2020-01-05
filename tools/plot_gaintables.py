#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk


import glob
import os.path as o
import pickle
import sys
sys.path.append(o.abspath(o.join(o.dirname(sys.modules[__name__].__file__), "..")))


from oxkat import generate_jobs as gen




def main():

    RAGAVI_CONTAINER = gen.RAGAVI_CONTAINER
    GAINPLOTS = gen.GAINPLOTS

    setup_dir(GAINPLOTS)

#    dependency = sys.argv[1]

    caltabs = sorted(glob.glob('cal_*'))

    for caltab in caltabs:

        gaintype = caltab.split('.')[-1][0].upper()
        opfile = GAINPLOTS+'/'+caltab

        syscall = 'ragavi-gains -g '+gaintype+' -t '+caltab+' --htmlname='+opfile

        print syscall

if __name__ == "__main__":


    main()