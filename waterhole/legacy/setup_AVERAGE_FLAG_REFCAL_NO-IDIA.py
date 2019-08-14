#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk


import sys
import glob
from oxkat import generate_jobs as gen


def main():


    CWD = gen.CWD
    OXKAT = gen.OXKAT
    SCRIPTS = gen.SCRIPTS
    LOGS = gen.LOGS
    PARSETS = gen.PARSETS


    submit_file = sys.argv[1]


    gen.setup_scripts_dir()


    f = open(submit_file,'w')


    myms = glob.glob('*.ms')[0]
    code = gen.get_code(myms)
    myms = myms.replace('.ms','_wtspec.ms')


    cmd = 'casa -c '+OXKAT+'/01_casa_average_to_1k.py --nologger --log2term --nogui'
    f.write(cmd+'\n')

    cmd = 'python '+OXKAT+'/00_setup.py '+myms
    f.write(cmd+'\n')

    cmd = 'casa -c '+OXKAT+'/01_casa_hardmask_and_flag.py --nologger --log2term --nogui'
    f.write(cmd+'\n')

    cmd = 'casa -c '+OXKAT+'/02_casa_refcal.py --nologger --log2term --nogui'
    f.write(cmd+'\n')


    f.close()


if __name__ == "__main__":


    main()
