#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk

# Continue cleaning a GC pointing


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


    INFRASTRUCTURE, CONTAINER_PATH = gen.set_infrastructure(sys.argv)


    # Get paths from config and setup folders

    CWD = cfg.CWD
    OXKAT = cfg.OXKAT
    PARSETS = cfg.PARSETS
    TOOLS = cfg.TOOLS
    GAINTABLES = cfg.GAINTABLES
    IMAGES = cfg.IMAGES
    LOGS = cfg.LOGS
    SCRIPTS = cfg.SCRIPTS


    gen.setup_dir(LOGS)
    gen.setup_dir(SCRIPTS)
    gen.setup_dir(IMAGES)


    # Get container needed for this script

    WSCLEAN_CONTAINER = gen.get_container(CONTAINER_PATH,cfg.WSCLEAN_PATTERN)
 

    # Set names of the run and kill files, open run file for writing

    submit_file = 'submit_2GC_GC_continue_clean_job.sh'

    f = open(submit_file,'w')
    f.write('#!/usr/bin/env bash\n')


    # Get target info from project_info.p

    project_info = pickle.load(open('project_info.p','rb'),encoding='latin1')

    targets = project_info['target_list'] 


    SLURM_WSCLEAN_MOD = cfg.SLURM_WSCLEAN
    SLURM_WSCLEAN_MOD['TIME'] = '18:00:00'

    PBS_WSCLEAN_MOD = cfg.PBS_WSCLEAN
    PBS_WSCLEAN_MOD['TIME'] = '18:00:00'


    # Loop over targets

    for target in targets:

        targetname = target[0]
        filename_targetname = gen.scrub_target_name(targetname)
        code = gen.get_target_code(targetname)
        myms = target[2].rstrip('/')

        print('------------------------------------------------------')
        print(gen.now()+'Target:     '+targetname)
        print(gen.now()+'MS:         '+myms)

    
        corr_img_prefix = IMAGES+'/img_'+myms+'_pcalmask'


        # ------------------------------------------------------------------------------
        # STEP 1: 
        # Continue wsclean on CORRECTED_DATA column with additional scale


        id_wsclean = 'WSCN3'+code

        syscall = 'singularity exec '+WSCLEAN_CONTAINER+' '
        syscall += gen.generate_syscall_wsclean(mslist=[myms],
                    imgname=corr_img_prefix,
                    continueclean=True,
                    datacol='CORRECTED_DATA',
                    briggs = -1.5,
                    multiscale = True,
                    scales = '0,3,9,18',
                    niter = 300000,
                    bda=False,
                    mask='none')

        run_command = gen.job_handler(syscall=syscall,
                    jobname=id_wsclean,
                    infrastructure=INFRASTRUCTURE,
                    slurm_config = SLURM_WSCLEAN_MOD,
                    pbs_config = PBS_WSCLEAN_MOD)


        f.write(run_command+'\n')


    f.close()


if __name__ == "__main__":


    main()