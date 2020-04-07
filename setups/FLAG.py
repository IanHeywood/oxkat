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


    infrastructure, CONTAINER_PATH = gen.set_infrastructure(sys.argv)


    # Get paths from config and setup folders

    CWD = cfg.CWD
    OXKAT = cfg.OXKAT
    PARSETS = cfg.PARSETS
    TOOLS = cfg.TOOLS
    IMAGES = cfg.IMAGES
    LOGS = cfg.LOGS
    SCRIPTS = cfg.SCRIPTS

    gen.setup_dir(LOGS)
    gen.setup_dir(SCRIPTS)
    gen.setup_dir(IMAGES)


    # Get containers needed for this script

    CASA_CONTAINER = gen.get_container(CONTAINER_PATH,cfg.CASA_PATTERN)
    DDFACET_CONTAINER = gen.get_container(CONTAINER_PATH,cfg.DDFACET_PATTERN)
    TRICOLOUR_CONTAINER = gen.get_container(CONTAINER_PATH,cfg.TRICOLOUR_PATTERN)
    WSCLEAN_CONTAINER = gen.get_container(CONTAINER_PATH,cfg.WSCLEAN_PATTERN)


    # Get target information from project pickle

    with open('project_info.p','rb') as f:
        project_info = pickle.load(f,encoding = 'latin1')

    targets = project_info['target_list'] 
 

    # Set names of the run file, open for writing

    submit_file = 'submit_flag_jobs.sh'

    f = open(submit_file,'w')
    f.write('#!/usr/bin/env bash\n')


    # Loop over targets

    for target in targets:


        # Code for job names is last three characters of target name
    
        code = target[0][-3:].replace('-','_').replace('.','p')

    
        # Target MS
    
        myms = target[2].rstrip('/')

    
        # Image prefix

        imgname = IMAGES+'/img_'+myms+'_datablind'


        # Target-specific kill file
    
        kill_file = SCRIPTS+'/kill_flag_jobs_'+target[0].replace('+','p')+'.sh'

    
        # Initialise a list to hold all the job IDs

        id_list = []


        # ------------------------------------------------------------------------------
        # STEP 1: 
        # Run Tricolour on targets

        syscall = 'singularity exec '+TRICOLOUR_CONTAINER+' '
        syscall += gen.generate_syscall_tricolour(myms = myms,
                                config = PARSETS+'/target_flagging_1_narrow.yaml',
                                datacol = 'DATA',
                                fields = '0',
                                strategy = 'polarisation')

        id_tricolour = 'TRICO'+code
        id_list.append(id_tricolour)

        run_command  = gen.job_handler(syscall = syscall,
                                jobname = id_tricolour,
                                infrastructure = infrastructure,
                                slurm_config = cfg.SLURM_TRICOLOUR,
                                pbs_config = cfg.PBS_TRICOLOUR)

        f.write(run_command)


        # ------------------------------------------------------------------------------
        # STEP 2: 
        # wsclean with blind deconvolution


        syscall = 'singularity exec '+WSCLEAN_CONTAINER+' '
        syscall += gen.generate_syscall_wsclean(mslist = [myms],
                                imgname = imgname,
                                datacol = 'DATA',
                                bda = True,
                                mask = 'none')

        id_wsclean = 'WSCLN'+code
        id_list.append(id_wsclean)

        run_command = gen.job_handler(syscall = syscall,
                                jobname = id_wsclean,
                                infrastructure = infrastructure,
                                dependency = id_tricolour,
                                slurm_config = cfg.SLURM_WSCLEAN,
                                pbs_config = cfg.PBS_WSCLEAN)

        f.write(run_command)


        # ------------------------------------------------------------------------------
        # STEP 3:
        # Make a FITS mask 


        syscall = 'singularity exec '+DDFACET_CONTAINER+' '
        syscall += gen.generate_syscall_makemask(prefix = imgname,
                                zoompix = '')[0]

        id_makemask = 'MKMSK'+code
        id_list.append(id_makemask)

        run_command = gen.job_handler(syscall = syscall,
                                jobname = id_makemask,
                                infrastructure = infrastructure,
                                dependency = id_wsclean)

        f.write(run_command)

        # ------------------------------------------------------------------------------
        # STEP 4:
        # Backup the flag table 

        syscall = 'singularity exec '+CASA_CONTAINER+' '
        syscall += 'casa -c '+OXKAT+'/FLAG_casa_backup_flag_table.py --nologger --log2term --nogui '
        syscall += 'versionname=tricolour1 '

        id_saveflags = 'SAVFG'+code
        id_list.append(id_saveflags)

        run_command = gen.job_handler(syscall=syscall,
                    jobname=id_saveflags,
                    infrastructure=infrastructure,
                    dependency=id_wsclean)

        f.write(run_command+'\n')

        # ------------------------------------------------------------------------------


        if infrastructure in ['idia','chpc']:
            kill = 'echo "scancel "$'+'" "$'.join(id_list)+' > '+kill_file
            f.write(kill+'\n')


    f.close()


if __name__ == "__main__":


    main()