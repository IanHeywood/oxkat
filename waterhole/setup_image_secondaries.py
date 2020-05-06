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


    INFRASTRUCTURE, CONTAINER_PATH = gen.set_infrastructure(sys.argv)


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

    WSCLEAN_CONTAINER = gen.get_container(CONTAINER_PATH,cfg.WSCLEAN_PATTERN)


    # Get target information from project pickle

    project_info = pickle.load(open('project_info.p','rb'),encoding='latin1')
    myms = project_info['master_ms']
    pcals = project_info['secondary']

    for pcal in pcals:
        fields.append(pcal[1])
    targets = project_info['target_list'] 
 

    # Set names of the run file, open for writing

    submit_file = 'submit_image-cal_jobs.sh'

    f = open(submit_file,'w')
    f.write('#!/usr/bin/env bash\n')

    kill_file = SCRIPTS+'/kill_image-cal_jobs.sh'


    codes = []
    ii = 1


    # Initialise a list to hold all the job IDs
    id_list = []


    # Loop over secondaries

    for pcal in pcals:

        pcalname = pcal[0]
        filename_pcalname = gen.scrub_target_name(pcalname)
        field = pcal[1]

        code = gen.get_target_code(pcalname)
        if code in codes:
            code += '_'+str(ii)
            ii += 1
        codes.append(code)

    
        # Image prefix

        img_prefix = IMAGES+'/img_'+myms+'_'+filename_pcalname+'_corrblind'
    

        # ------------------------------------------------------------------------------
        # STEP 1: 
        # wsclean with blind deconvolution

        syscall = 'singularity exec '+WSCLEAN_CONTAINER+' '
        syscall += gen.generate_syscall_wsclean(mslist = [myms],
                                imgname = img_prefix,
                                datacol = 'CORRECTED_DATA',
                                imsize = 8192,
                                niter = 100000,
                                gain = 0.2,
                                mgain = 0.9, 
                                bda = True,
                                mask = 'none')

        id_wsclean = 'WSCBL'+code
        id_list.append(id_wsclean)

        if len(id_list) > 0:
            dependency = id_list[-1]
        else:
            dependency = None

        run_command = gen.job_handler(syscall = syscall,
                                jobname = id_wsclean,
                                infrastructure = INFRASTRUCTURE,
                                dependency = dependency,
                                slurm_config = cfg.SLURM_WSCLEAN,
                                pbs_config = cfg.PBS_WSCLEAN)

        f.write(run_command)



        # ------------------------------------------------------------------------------


    if INFRASTRUCTURE in ['idia','chpc']:
        kill = 'echo "scancel "$'+'" "$'.join(id_list)+' > '+kill_file
        f.write(kill+'\n')
    f.write('\n')


    f.close()


    gen.make_executable(submit_file)


if __name__ == "__main__":


    main()