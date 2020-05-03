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
 

    # Set names of the run and kill files, open run file for writing

    submit_file = 'submit_2GC_jobs.sh'

    f = open(submit_file,'w')
    f.write('#!/usr/bin/env bash\n')


    # Get target info from project_info.p

    project_info = pickle.load(open('project_info.p','rb'),encoding='latin1')

    targets = project_info['target_list'] 


    # Loop over targets

    codes = []
    ii = 1

    for target in targets:

        targetname = target[0]
        filename_targetname = gen.scrub_target_name(targetname)
        myms = target[2].rstrip('/')


        code = gen.get_target_code(targetname)
        if code in codes:
            code += '_'+str(ii)
            ii += 1
        codes.append(code)


        mask0 = sorted(glob.glob(IMAGES+'/*'+filename_targetname+'*.mask0.fits'))
        if len(mask0) > 0:
            mask = mask0[0]
        else:
            mask = 'auto'


        print('------------------------------------------------------')
        print(gen.now()+'Target:     '+targetname)
        print(gen.now()+'MS:         '+myms)
        print(gen.now()+'Using mask: '+mask)

        f.write('# '+targetname+'\n')
    
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
                    multiscale = True,
                    scales = '0,3,9',
                    niter = 250000,
                    datacol='DATA',
                    bda=True,
                    mask=mask)

        run_command = gen.job_handler(syscall=syscall,
                    jobname=id_wsclean1,
                    infrastructure=INFRASTRUCTURE,
                    slurm_config = cfg.SLURM_WSCLEAN,
                    pbs_config = cfg.PBS_WSCLEAN)


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
                    extra_args='mslist='+myms)

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
                    multiscale = True,
                    scales = '0,3,9',
                    niter = 250000,
                    datacol='CORRECTED_DATA',
                    bda=True,
                    mask=mask)

        run_command = gen.job_handler(syscall=syscall,
                    jobname=id_wsclean2,
                    infrastructure=INFRASTRUCTURE,
                    dependency=id_selfcal,
                    slurm_config = cfg.SLURM_WSCLEAN,
                    pbs_config = cfg.PBS_WSCLEAN)


        f.write(run_command+'\n')


        # ------------------------------------------------------------------------------
        # STEP 5:
        # Make a FITS mask 

        syscall = 'singularity exec '+DDFACET_CONTAINER+' '
        syscall += gen.generate_syscall_makemask(restoredimage = corr_img_prefix+'-MFS-image.fits',
                                suffix = 'mask1',
                                thresh = 5.5,
                                zoompix = cfg.DDF_NPIX)[0]

        id_makemask = 'MASK1'+code
        id_list.append(id_makemask)

        run_command = gen.job_handler(syscall = syscall,
                                jobname = id_makemask,
                                infrastructure = INFRASTRUCTURE,
                                dependency = id_wsclean2)

        f.write(run_command+'\n')


        # ------------------------------------------------------------------------------
        # STEP 6:
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

        f.write('# ----------------- \n\n')

    f.close()


if __name__ == "__main__":


    main()
