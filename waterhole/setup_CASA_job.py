#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk


import glob
import os.path as o
import pickle
import sys
sys.path.append(o.abspath(o.join(o.dirname(sys.modules[__name__].__file__), "..")))


from oxkat import generate_jobs as gen
from oxkat import config as cfg


def main():

    # ------------------------------------------------------------------------------
    # Setup


    if sys.argv[1].lower() == 'idia':
        infrastructure = 'idia'
        CONTAINER_PATH = cfg.IDIA_CONTAINER_PATH
    elif sys.argv[1].lower() == 'chpc':
        infrastructure = 'chpc'
        CONTAINER_PATH = cfg.CHPC_CONTAINER_PATH
    elif sys.argv[1].lower() == 'node':
        infrastructure = 'node'
        CONTAINER_PATH = cfg.NODE_CONTAINER_PATH


    # Get paths from config and setup folders

    CWD = cfg.CWD
    OXKAT = cfg.OXKAT
    PARSETS = cfg.PARSETS
    LOGS = cfg.LOGS
    SCRIPTS = cfg.SCRIPTS

    gen.setup_dir(LOGS)
    gen.setup_dir(SCRIPTS)


    # Get containers needed for this script

    CASA_CONTAINER = gen.get_container(CONTAINER_PATH,cfg.CASA_PATTERN)

 
    # Set names of the run and kill files, open run file for writing

    submit_file = 'submit_CASA_job.sh'


    f = open(submit_file,'w')
    f.write('#!/usr/bin/env bash\n')



    syscall = 'singularity exec '+CASA_CONTAINER+' '
    syscall += 'casa -c '+sys.argv[1]+' --nologger --log2term --nogui\n'

    id_average = 'CASA'

    run_command = gen.job_handler(syscall=syscall,
                jobname=id_average,
                infrastructure=infrastructure)

    f.write(run_command+'\n')

    

    f.close()


if __name__ == "__main__":


    main()