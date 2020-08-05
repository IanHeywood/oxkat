#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk

# Generate a cube for spectral index work


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
 

    # Bump up the walltimes

    SLURM_WSCLEAN_MOD = cfg.SLURM_WSCLEAN
    SLURM_WSCLEAN_MOD['TIME'] = '36:00:00'

    PBS_WSCLEAN_MOD = cfg.PBS_WSCLEAN
    PBS_WSCLEAN_MOD['WALLTIME'] = '36:00:00'


    # Set names of the run file, open for writing

    submit_file = 'submit_2GC_make_cube.sh'

    f = open(submit_file,'w')
    f.write('#!/usr/bin/env bash\n')


    # Get target info from project_info.p

    project_info = pickle.load(open('project_info.p','rb'),encoding='latin1')

    target_ids = project_info['target_ids'] 
    target_names = project_info['target_names']
    target_ms = project_info['target_ms']

    # Loop over targets

    codes = []
    ii = 1


    for tt in range(0,len(target_ids)):


        targetname = target_names[tt]
        myms = target_ms[tt]
        filename_targetname = gen.scrub_target_name(targetname)
        code = gen.get_target_code(targetname)
        mask0 = sorted(glob.glob(IMAGES+'/*'+filename_targetname+'*.mask.fits'))

        print('------------------------------------------------------')
        print(gen.now()+'Target:     '+targetname)
        print(gen.now()+'MS:         '+myms)

        if len(mask0) > 0:
            mask = mask0[0]
        else:
            mask = 'auto'

        print(gen.now()+'Using mask: '+mask)

    
        cube_prefix = IMAGES+'/img_'+myms+'_subbands'


        # ------------------------------------------------------------------------------
        # STEP 1: 
        # Continue wsclean on CORRECTED_DATA column with additional scale


        id_wsclean = 'WCUBE'+code

        syscall = 'singularity exec '+WSCLEAN_CONTAINER+' '
        syscall += gen.generate_syscall_wsclean(mslist=[myms],
                    imgname=cube_prefix,
                    datacol='CORRECTED_DATA',
                    sourcelist = False,
                    chanout = 16,
                    briggs = -1.5,
                    multiscale = True,
                    scales = '0,3,9',
                    minuvl = 164,
                    tapergaussian = 8,
                    joinchannels = False,
                    fitspectralpol = 0,
                    niter = 500000,
                    bda = True,
                    mask = mask)

        run_command = gen.job_handler(syscall=syscall,
                    jobname=id_wsclean,
                    infrastructure=INFRASTRUCTURE,
                    slurm_config = SLURM_WSCLEAN_MOD,
                    pbs_config = PBS_WSCLEAN_MOD)


        f.write(run_command+'\n')


    f.close()


if __name__ == "__main__":


    main()
