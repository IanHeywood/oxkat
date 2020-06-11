#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk

# 2GC script modified for Galactic Centre pointings
#
# - Expects manually-thresholded mask in IMAGES folder
#   repo at: https://github.com/IanHeywood/masks
#
# - Multiscale and deeper clean enabled with robust = -1.5
#
# - Walltimes bumped up accordingly
#
# - Harsher inner uv cut for phase-only selfcal
#
# - Final MakeMask step excluded because this should be done manually for these fields


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
    gen.setup_dir(GAINTABLES)


    # Get containers needed for this script

    CASA_CONTAINER = gen.get_container(CONTAINER_PATH,cfg.CASA_PATTERN)
    DDFACET_CONTAINER = gen.get_container(CONTAINER_PATH,cfg.DDFACET_PATTERN)
    TRICOLOUR_CONTAINER = gen.get_container(CONTAINER_PATH,cfg.TRICOLOUR_PATTERN)
    WSCLEAN_CONTAINER = gen.get_container(CONTAINER_PATH,cfg.WSCLEAN_PATTERN)
 

    # Bump up the walltimes

    SLURM_WSCLEAN_MOD = cfg.SLURM_WSCLEAN
    SLURM_WSCLEAN_MOD['TIME'] = '18:00:00'

    PBS_WSCLEAN_MOD = cfg.PBS_WSCLEAN
    PBS_WSCLEAN_MOD['TIME'] = '18:00:00'


    # Set names of the run file, open for writing

    submit_file = 'submit_2GC_jobs.sh'

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
        myms = target[2].rstrip('/')
        mask0 = sorted(glob.glob(IMAGES+'/*'+filename_targetname+'*.mask.fits'))

        print('------------------------------------------------------')
        print(gen.now()+'Target:     '+targetname)
        print(gen.now()+'MS:         '+myms)

        if len(mask0) > 0:
            mask = mask0[0]
        else:
            mask = 'auto'

        print(gen.now()+'Using mask: '+mask)

    
        kill_file = SCRIPTS+'/kill_2GC_jobs_'+filename_targetname+'.sh'


        data_img_prefix = IMAGES+'/img_'+myms+'_datamask'
        corr_img_prefix = IMAGES+'/img_'+myms+'_pcalmask'


        # Initialise a list to hold all the job IDs

        id_list = []


        # ------------------------------------------------------------------------------
        # STEP 1: 
        # Masked wsclean on DATA column


        id_wsclean1 = 'WSDMA'+code
        id_list.append(id_wsclean1)

        syscall = 'singularity exec '+WSCLEAN_CONTAINER+' '
        syscall += gen.generate_syscall_wsclean(mslist=[myms],
                    imgname=data_img_prefix,
                    briggs = -1.5,
                    multiscale = True,
                    scales = '0,3,9',
                    niter = 300000,
                    datacol='DATA',
                    bda=True,
                    mask=mask)

        run_command = gen.job_handler(syscall=syscall,
                    jobname=id_wsclean1,
                    infrastructure=INFRASTRUCTURE,
                    slurm_config = SLURM_WSCLEAN_MOD,
                    pbs_config = PBS_WSCLEAN_MOD)


        f.write(run_command+'\n')


        # ------------------------------------------------------------------------------
        # STEP 2:
        # Predict MODEL_DATA


        id_predict1 = 'WSDPR'+code
        id_list.append(id_predict1)

        syscall = 'singularity exec '+WSCLEAN_CONTAINER+' '
        syscall += gen.generate_syscall_predict(msname=myms,imgbase=data_img_prefix)

        run_command = gen.job_handler(syscall=syscall,
                    jobname=id_predict1,
                    infrastructure=INFRASTRUCTURE,
                    dependency=id_wsclean1,
                    slurm_config = cfg.SLURM_WSCLEAN,
                    pbs_config = cfg.PBS_WSCLEAN)


        f.write(run_command+'\n')


        # ------------------------------------------------------------------------------
        # STEP 3:
        # Self-calibrate phases then amplitudes


        id_selfcal = 'CLSLF'+code
        id_list.append(id_selfcal)

        casalog = LOGS+'/casa_2GC_'+id_selfcal+'.log'

        syscall = 'singularity exec '+CASA_CONTAINER+' '
        syscall += gen.generate_syscall_casa(casascript=OXKAT+'/2GC_casa_selfcal_target_amp_phases.py',
                    casalogfile=casalog,
                    extra_args='mslist='+myms+' uvmin=300')

        run_command = gen.job_handler(syscall=syscall,
                    jobname=id_selfcal,
                    infrastructure=INFRASTRUCTURE,
                    dependency=id_predict1)

        f.write(run_command+'\n')


        # ------------------------------------------------------------------------------
        # STEP 4:
        # Masked wsclean on CORRECTED_DATA column


        id_wsclean2 = 'WSCMA'+code
        id_list.append(id_wsclean2)

        syscall = 'singularity exec '+WSCLEAN_CONTAINER+' '
        syscall += gen.generate_syscall_wsclean(mslist=[myms],
                    imgname=corr_img_prefix,
                    datacol='CORRECTED_DATA',
                    briggs = -1.5,
                    multiscale = True,
                    scales = '0,3,9',
                    niter = 300000,
                    bda=True,
                    mask=mask)

        run_command = gen.job_handler(syscall=syscall,
                    jobname=id_wsclean2,
                    infrastructure=INFRASTRUCTURE,
                    dependency=id_selfcal,
                    slurm_config = SLURM_WSCLEAN_MOD,
                    pbs_config = PBS_WSCLEAN_MOD)


        f.write(run_command+'\n')


        # ------------------------------------------------------------------------------
        # STEP 5:
        # Predict MODEL_DATA


        id_predict2 = 'WSCPR'+code
        id_list.append(id_predict2)

        syscall = 'singularity exec '+WSCLEAN_CONTAINER+' '
        syscall += gen.generate_syscall_predict(msname=myms,imgbase=corr_img_prefix)

        run_command = gen.job_handler(syscall=syscall,
                    jobname=id_predict2,
                    infrastructure=INFRASTRUCTURE,
                    dependency=id_wsclean2,
                    slurm_config = cfg.SLURM_WSCLEAN,
                    pbs_config = cfg.PBS_WSCLEAN)


        f.write(run_command+'\n')


        # ------------------------------------------------------------------------------


        if INFRASTRUCTURE in ['idia','chpc']:
            kill = 'echo "scancel "$'+'" "$'.join(id_list)+' > '+kill_file
            f.write(kill+'\n')


    f.close()


if __name__ == "__main__":


    main()