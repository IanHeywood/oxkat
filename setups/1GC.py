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
    LOGS = cfg.LOGS
    SCRIPTS = cfg.SCRIPTS

    gen.setup_dir(LOGS)
    gen.setup_dir(SCRIPTS)


    # Get containers needed for this script

    CASA_CONTAINER = gen.get_container(CONTAINER_PATH,cfg.CASA_PATTERN)
    RAGAVI_CONTAINER = gen.get_container(CONTAINER_PATH,cfg.RAGAVI_PATTERN)

 
    # Set names of the run and kill files, open run file for writing

    submit_file = 'submit_1GC_jobs.sh'
    kill_file = SCRIPTS+'/kill_1GC_jobs.sh'

    f = open(submit_file,'w')
    f.write('#!/usr/bin/env bash\n')


    # Get the MS name

    original_ms = glob.glob('*.ms')[0]
    code = gen.get_code(original_ms)
    myms = original_ms.replace('.ms','_wtspec.ms')


    # Initialise a list to hold all the job IDs

    id_list = []


    # ------------------------------------------------------------------------------
    # Pre-processing:
    # Duplicate orignal MS, average to 1k channels if required


    syscall = 'singularity exec '+CASA_CONTAINER+' '
    syscall += 'casa -c '+OXKAT+'/PRE_casa_average_to_1k_add_wtspec.py --nologger --log2term --nogui\n'

    id_average = 'AVRGE'+code
    id_list.append(id_average)

    run_command = gen.job_handler(syscall=syscall,
                jobname=id_average,
                infrastructure=infrastructure)

    f.write(run_command+'\n')


    # ------------------------------------------------------------------------------
    # STEP 0:
    # Examine MS and store relevant deductions in project_info.p                           
                   

    syscall = 'singularity exec '+RAGAVI_CONTAINER+' '
    syscall += 'python '+OXKAT+'/1GC_00_setup.py '+myms+'\n'

    id_setup = 'INFO_'+code
    id_list.append(id_setup)

    run_command = gen.job_handler(syscall=syscall,
                jobname=id_setup,
                infrastructure=infrastructure,
                dependency=id_average)

    f.write(run_command+'\n')


    # ------------------------------------------------------------------------------
    # STEP 1:
    # Rephase the primary calibrators to correct positions
                                    

    syscall = 'singularity exec '+CASA_CONTAINER+' '
    syscall += 'casa -c '+OXKAT+'/1GC_01_casa_rephase_primary_calibrator.py --nologger --log2term --nogui\n'

    id_fixvis = 'UVFIX'+code
    id_list.append(id_fixvis)

    run_command = gen.job_handler(syscall=syscall,
                jobname=id_fixvis,
                infrastructure=infrastructure,
                dependency=id_setup)

    f.write(run_command+'\n')


    # ------------------------------------------------------------------------------
    # STEP 2:
    # Apply basic flagging steps to all fields
                                    

    syscall = 'singularity exec '+CASA_CONTAINER+' '
    syscall += 'casa -c '+OXKAT+'/1GC_02_casa_basic_flags.py --nologger --log2term --nogui\n'

    id_basic = 'BASIC'+code
    id_list.append(id_basic)

    run_command = gen.job_handler(syscall=syscall,
                jobname=id_basic,
                infrastructure=infrastructure,
                dependency=id_fixvis)

    f.write(run_command+'\n')


    # ------------------------------------------------------------------------------
    # STEP 3:
    # Run auto-flaggers on calibrators


    syscall = 'singularity exec '+CASA_CONTAINER+' '
    syscall += 'casa -c '+OXKAT+'/1GC_03_casa_autoflag_cals_DATA.py --nologger --log2term --nogui\n'

    id_autoflagcals = 'FLG_C'+code
    id_list.append(id_autoflagcals)

    run_command = gen.job_handler(syscall=syscall,
                jobname=id_autoflagcals,
                infrastructure=infrastructure,
                dependency=id_basic)

    f.write(run_command+'\n')


    # ------------------------------------------------------------------------------
    # STEP 4:
    # Split calibrators into a MS with 8 spectral windows
                                              

    syscall = 'singularity exec '+CASA_CONTAINER+' '
    syscall += 'casa -c '+OXKAT+'/1GC_04_casa_split_calibrators.py --nologger --log2term --nogui\n'

    id_splitcals = 'SPLCL'+code
    id_list.append(id_splitcals)

    run_command = gen.job_handler(syscall=syscall,
                jobname=id_splitcals,
                infrastructure=infrastructure,
                dependency=id_autoflagcals)

    f.write(run_command+'\n')


    # ------------------------------------------------------------------------------
    # STEP 5:
    # Derive an intrinsic spectral model for the secondary calibrator                              
                                                       

    syscall = 'singularity exec '+CASA_CONTAINER+' '
    syscall += 'casa -c '+OXKAT+'/1GC_05_casa_get_secondary_model.py --nologger --log2term --nogui\n'

    id_secondarymodel = 'MODEL'+code
    id_list.append(id_secondarymodel)

    run_command = gen.job_handler(syscall=syscall,
                jobname=id_secondarymodel,
                infrastructure=infrastructure,
                dependency=id_splitcals)

    f.write(run_command+'\n')


    # ------------------------------------------------------------------------------
    # STEP 6: (1GC)
    # Perform reference calibration steps and apply to target(s)
                                               

    syscall = 'singularity exec '+CASA_CONTAINER+' '
    syscall += 'casa -c '+OXKAT+'/1GC_06_casa_refcal_using_secondary_model.py --nologger --log2term --nogui\n'

    id_1GC = 'ONEGC'+code
    id_list.append(id_1GC)

    run_command = gen.job_handler(syscall=syscall,
                jobname=id_1GC,
                infrastructure=infrastructure,
                dependency=id_secondarymodel)

    f.write(run_command+'\n')


    # ------------------------------------------------------------------------------
    # STEP 7: 
    # Make gain table plots
                                         

    syscall = 'singularity exec '+RAGAVI_CONTAINER+' '
    syscall += 'python3 '+OXKAT+'/1GC_07_plot_gaintables.py\n'

    id_gainplots = 'GPLOT'+code
    id_list.append(id_gainplots)

    run_command = gen.job_handler(syscall=syscall,
                jobname=id_gainplots,
                infrastructure=infrastructure,
                dependency=id_1GC)

    f.write(run_command+'\n')


    # ------------------------------------------------------------------------------
    # STEP 8:
    # Split the corrected target data into individual Measurement Sets
                               

    syscall = 'singularity exec '+CASA_CONTAINER+' '
    syscall += 'casa -c '+OXKAT+'/1GC_08_casa_split_targets.py --nologger --log2term --nogui\n'

    id_splittargets = 'SPLTG'+code
    id_list.append(id_splittargets)

    run_command = gen.job_handler(syscall=syscall,
                jobname=id_splittargets,
                infrastructure=infrastructure,
                dependency=id_1GC)

    f.write(run_command+'\n')


    # ------------------------------------------------------------------------------


    if infrastructure in ['idia','chpc']:
        kill = 'echo "scancel "$'+'" "$'.join(id_list)+' > '+kill_file
        f.write(kill+'\n')
    

    f.close()


    gen.make_executable(submit_file)
    gen.make_executable(kill_file)


if __name__ == "__main__":


    main()