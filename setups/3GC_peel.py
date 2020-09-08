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
    BIND = cfg.BIND
    OXKAT = cfg.OXKAT
    PARSETS = cfg.PARSETS
    TOOLS = cfg.TOOLS
    GAINTABLES = cfg.GAINTABLES
    IMAGES = cfg.IMAGES
    LOGS = cfg.LOGS
    SCRIPTS = cfg.SCRIPTS

    BINDPATH = '$PWD,'+CWD+','+BIND

    gen.setup_dir(LOGS)
    gen.setup_dir(SCRIPTS)
    gen.setup_dir(IMAGES)
    gen.setup_dir(GAINTABLES)


    # Get containers needed for this script

    CUBICAL_CONTAINER = gen.get_container(CONTAINER_PATH,cfg.CUBICAL_PATTERN)
    WSCLEAN_CONTAINER = gen.get_container(CONTAINER_PATH,cfg.WSCLEAN_PATTERN)
 

    # Set names of the run and kill files, open run file for writing

    submit_file = 'submit_3GC_peel_jobs.sh'

    f = open(submit_file,'w')
    f.write('#!/usr/bin/env bash\n')
    f.write('export SINGULARITY_BINDPATH='+BINDPATH+'\n')


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


        if not o.isdir(myms):

            print('------------------------------------------------------')
            print(gen.now()+myms+' not found, skipping '+targetname)

        else:
            
            filename_targetname = gen.scrub_target_name(targetname)

            code = gen.get_target_code(targetname)
            if code in codes:
                code += '_'+str(ii)
                ii += 1
            codes.append(code)


            mask0 = sorted(glob.glob(IMAGES+'/*'+filename_targetname+'*.mask1.fits'))
            if len(mask0) > 0:
                mask = mask0[0]
            else:
                mask = 'auto'


            print('------------------------------------------------------')
            print(gen.now()+'Target:     '+targetname)
            print(gen.now()+'MS:         '+myms)
            print(gen.now()+'Using mask: '+mask)

            f.write('\n# '+targetname+'\n')
        
            kill_file = SCRIPTS+'/kill_3GC_peel_jobs_'+filename_targetname+'.sh'


            prepeel_img_prefix = IMAGES+'/img_'+myms+'_prepeel'
            dir1_img_prefix = prepeel_img_prefix+'-'+cfg.CAL_3GC_PEEL_REGION.split('/')[-1].split('.')[0]


            # Initialise a list to hold all the job IDs

            id_list = []


            # ------------------------------------------------------------------------------
            # STEP 1: 
            # Masked wsclean on CORRECTED_DATA column with high (frequency) resolution


            id_wsclean = 'WSDMA'+code
            id_list.append(id_wsclean)

            syscall = 'singularity exec '+WSCLEAN_CONTAINER+' '
            syscall += gen.generate_syscall_wsclean(mslist=[myms],
                        imgname=prepeel_img_prefix,
                        datacol='CORRECTED_DATA',
                        briggs=-0.6,
                        chanout=cfg.CAL_3GC_PEEL_NCHAN,
                        bda=True,
                        mask=mask)

            run_command = gen.job_handler(syscall=syscall,
                        jobname=id_wsclean,
                        infrastructure=INFRASTRUCTURE,
                        slurm_config = cfg.SLURM_WSCLEAN,
                        pbs_config = cfg.PBS_WSCLEAN)


            f.write(run_command)


            # ------------------------------------------------------------------------------
            # STEP 2:
            # Split model images


            id_imsplit = 'IMSPL'+code
            id_list.append(id_imsplit)

            syscall = 'singularity exec '+CUBICAL_CONTAINER+' '
            syscall += 'python '+OXKAT+'/3GC_split_model_images.py '
            syscall += '--region '+cfg.CAL_3GC_PEEL_REGION+' '
            syscall += '--prefix '+prepeel_img_prefix+' '

            run_command = gen.job_handler(syscall=syscall,
                        jobname=id_imsplit,
                        infrastructure=INFRASTRUCTURE,
                        dependency=id_wsclean,
                        slurm_config = cfg.SLURM_WSCLEAN,
                        pbs_config = cfg.PBS_WSCLEAN)

            f.write(run_command)


            # ------------------------------------------------------------------------------
            # STEP 3:
            # Predict DIR1 model into MODEL_DATA


            id_predict1 = 'WS1PR'+code
            id_list.append(id_predict1)

            syscall = 'singularity exec '+WSCLEAN_CONTAINER+' '
            syscall += gen.generate_syscall_predict(msname=myms,imgbase=dir1_img_prefix,chanout=cfg.CAL_3GC_PEEL_NCHAN)

            run_command = gen.job_handler(syscall=syscall,
                        jobname=id_predict1,
                        infrastructure=INFRASTRUCTURE,
                        dependency=id_imsplit,
                        slurm_config = cfg.SLURM_WSCLEAN,
                        pbs_config = cfg.PBS_WSCLEAN)


            f.write(run_command)


            # ------------------------------------------------------------------------------
            # STEP 4:
            # Add extra data column


            id_addcol = 'ADCOL'+code
            id_list.append(id_addcol)

            syscall = 'singularity exec '+CUBICAL_CONTAINER+' '
            syscall += 'python '+TOOLS+'/add_MS_column.py '
            syscall += '--colname '+cfg.CAL_3GC_PEEL_DIR1COLNAME+' '
            syscall += myms

            run_command = gen.job_handler(syscall=syscall,
                        jobname=id_addcol,
                        infrastructure=INFRASTRUCTURE,
                        dependency=id_predict1)

            f.write(run_command)


            # ------------------------------------------------------------------------------
            # STEP 5:
            # Copy MODEL_DATA to new column


            id_copycol = 'CPCOL'+code
            id_list.append(id_copycol)

            syscall = 'singularity exec '+CUBICAL_CONTAINER+' '
            syscall += 'python '+TOOLS+'/copy_MS_column.py '
            syscall += '--fromcol MODEL_DATA '
            syscall += '--tocol '+cfg.CAL_3GC_PEEL_DIR1COLNAME+' '
            syscall += myms

            run_command = gen.job_handler(syscall=syscall,
                        jobname=id_copycol,
                        infrastructure=INFRASTRUCTURE,
                        dependency=id_addcol)

            f.write(run_command)


            # ------------------------------------------------------------------------------
            # STEP 6:
            # Predict full sky model into MODEL_DATA


            id_predict2 = 'WS2PR'+code
            id_list.append(id_predict2)

            syscall = 'singularity exec '+WSCLEAN_CONTAINER+' '
            syscall += gen.generate_syscall_predict(msname=myms,imgbase=prepeel_img_prefix,chanout=cfg.CAL_3GC_PEEL_NCHAN)

            run_command = gen.job_handler(syscall=syscall,
                        jobname=id_predict2,
                        infrastructure=INFRASTRUCTURE,
                        dependency=id_copycol,
                        slurm_config = cfg.SLURM_WSCLEAN,
                        pbs_config = cfg.PBS_WSCLEAN)


            f.write(run_command)


            # ------------------------------------------------------------------------------
            # STEP 7:
            # Run CubiCal


            id_peel = 'CL3GC'+code
            id_list.append(id_peel)


            syscall = 'singularity exec '+CUBICAL_CONTAINER+' '
            syscall += gen.generate_syscall_cubical(parset=cfg.CAL_3GC_PEEL_PARSET,myms=myms)

            run_command = gen.job_handler(syscall=syscall,
                        jobname=id_peel,
                        infrastructure=INFRASTRUCTURE,
                        dependency=id_predict2,
                        slurm_config = cfg.SLURM_WSCLEAN,
                        pbs_config = cfg.PBS_WSCLEAN)

            f.write(run_command)



            # ------------------------------------------------------------------------------


            if INFRASTRUCTURE == 'idia':
                kill = 'echo "scancel "$'+'" "$'.join(id_list)+' > '+kill_file+'\n'
                f.write(kill)
            elif INFRASTRUCTURE == 'chpc':
                kill = 'echo "qdel "$'+'" "$'.join(id_list)+' > '+kill_file+'\n'
                f.write(kill)

    f.close()


if __name__ == "__main__":


    main()
