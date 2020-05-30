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
    if len(sys.argv) > 2:
        exclude = sys.argv[2]
    else:
        exclude = ''

    caltabs = sorted([item for item in glob.glob(GAINTABLES+'/'+include) if not os.path.basename(item).endswith('flagversions')])
    if exclude != '':
        exclude = glob.glob(GAINTABLES+'/'+exclude)

    for caltab in caltabs:
        if caltab not in exclude:
            gaintype = caltab.split('.')[-1][0].upper()
            opfile = GAINPLOTS+'/'+caltab.split('/')[-1]
            if not os.path.isfile(opfile):
                syscall = 'ragavi-gains -g '+gaintype+' -t '+caltab+' --htmlname='+opfile
                subprocess.run([syscall],shell=True)
            else:
                print(opfile+' exists, skipping')

if __name__ == "__main__":


    main()