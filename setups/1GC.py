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
    GAINTABLES = cfg.GAINTABLES
    LOGS = cfg.LOGS
    SCRIPTS = cfg.SCRIPTS

    gen.setup_dir(LOGS)
    gen.setup_dir(SCRIPTS)
    gen.setup_dir(GAINTABLES)


    # Get containers needed for this script

    CASA_CONTAINER = gen.get_container(CONTAINER_PATH,cfg.CASA_PATTERN)
    RAGAVI_CONTAINER = gen.get_container(CONTAINER_PATH,cfg.RAGAVI_PATTERN)
    SHADEMS_CONTAINER = gen.get_container(CONTAINER_PATH,cfg.SHADEMS_PATTERN)
    TRICOLOUR_CONTAINER = gen.get_container(CONTAINER_PATH,cfg.TRICOLOUR_PATTERN)

 
    # Set names of the run and kill files, open run file for writing

    submit_file = 'submit_1GC_jobs.sh'
    kill_file = SCRIPTS+'/kill_1GC_jobs.sh'

    f = open(submit_file,'w')
    f.write('#!/usr/bin/env bash\n')


    # Get the MS name

    original_ms = glob.glob('*.ms')[0]
    code = gen.get_code(original_ms)
    myms = original_ms.replace('.ms','_'+str(cfg.PRE_NCHANS)+'ch.ms')


    # Initialise a list to hold all the job IDs

    id_list = []


    # ------------------------------------------------------------------------------
    # Pre-processing:
    # Duplicate orignal MS, average to 1k channels if required


    id_average = 'SPPRE'+code
    id_list.append(id_average)

    casalog = LOGS+'/casa_1GC_'+id_average+'.log'

    syscall = 'singularity exec '+CASA_CONTAINER+' '
    syscall += gen.generate_syscall_casa(casascript=OXKAT+'/PRE_casa_average_to_1k_add_wtspec.py',
                casalogfile=casalog)

    run_command = gen.job_handler(syscall=syscall,
                jobname=id_average,
                infrastructure=INFRASTRUCTURE)

    f.write(run_command)


    # ------------------------------------------------------------------------------
    # STEP 0:
    # Examine MS and store relevant deductions in project_info.p                           
                   

    id_setup = 'SETUP'+code
    id_list.append(id_setup)

    syscall = 'singularity exec '+TRICOLOUR_CONTAINER+' '
    syscall += 'python '+OXKAT+'/1GC_00_setup.py '+myms

    run_command = gen.job_handler(syscall=syscall,
                jobname=id_setup,
                infrastructure=INFRASTRUCTURE,
                dependency=id_average)

    f.write(run_command)


    # ------------------------------------------------------------------------------
    # STEP 1:
    # Rephase the primary calibrators to correct positions
                                    

    id_fixvis = 'UVFIX'+code
    id_list.append(id_fixvis)

    casalog = LOGS+'/casa_1GC_'+id_fixvis+'.log'

    syscall = 'singularity exec '+CASA_CONTAINER+' '
    syscall += gen.generate_syscall_casa(casascript=OXKAT+'/1GC_01_casa_rephase_primary_calibrator.py',
                casalogfile=casalog)

    run_command = gen.job_handler(syscall=syscall,
                jobname=id_fixvis,
                infrastructure=INFRASTRUCTURE,
                dependency=id_setup)

    f.write(run_command)


    # ------------------------------------------------------------------------------
    # STEP 2:
    # Apply basic flagging steps to all fields
                                    

    id_basic = 'FGBAS'+code
    id_list.append(id_basic)

    casalog = LOGS+'/casa_1GC_'+id_basic+'.log'

    syscall = 'singularity exec '+CASA_CONTAINER+' '
    syscall += gen.generate_syscall_casa(casascript=OXKAT+'/1GC_02_casa_basic_flags.py',
                casalogfile=casalog)

    run_command = gen.job_handler(syscall=syscall,
                jobname=id_basic,
                infrastructure=INFRASTRUCTURE,
                dependency=id_fixvis)

    f.write(run_command)


    # ------------------------------------------------------------------------------
    # STEP 3:
    # Run auto-flaggers on calibrators


    id_autoflagcals = 'FGCAL'+code
    id_list.append(id_autoflagcals)

    casalog = LOGS+'/casa_1GC_'+id_autoflagcals+'.log'

    syscall = 'singularity exec '+CASA_CONTAINER+' '
    syscall += gen.generate_syscall_casa(casascript=OXKAT+'/1GC_03_casa_autoflag_cals_DATA.py',
                casalogfile=casalog)

    run_command = gen.job_handler(syscall=syscall,
                jobname=id_autoflagcals,
                infrastructure=INFRASTRUCTURE,
                dependency=id_basic)

    f.write(run_command)


    # ------------------------------------------------------------------------------
    # STEP 4:
    # Split calibrators into a MS with 8 spectral windows
                                              

    id_splitcals = 'SPCAL'+code
    id_list.append(id_splitcals)

    casalog = LOGS+'/casa_1GC_'+id_splitcals+'.log'

    syscall = 'singularity exec '+CASA_CONTAINER+' '
    syscall += gen.generate_syscall_casa(casascript=OXKAT+'/1GC_04_casa_split_calibrators.py',
                casalogfile=casalog)

    run_command = gen.job_handler(syscall=syscall,
                jobname=id_splitcals,
                infrastructure=INFRASTRUCTURE,
                dependency=id_autoflagcals)

    f.write(run_command)


    # ------------------------------------------------------------------------------
    # STEP 5:
    # Derive an intrinsic spectral model for the secondary calibrator                              
                                                       

    id_secondarymodel = 'CLMOD'+code
    id_list.append(id_secondarymodel)

    casalog = LOGS+'/casa_1GC_'+id_secondarymodel+'.log'

    syscall = 'singularity exec '+CASA_CONTAINER+' '
    syscall += gen.generate_syscall_casa(casascript=OXKAT+'/1GC_05_casa_get_secondary_model.py',
                casalogfile=casalog)

    run_command = gen.job_handler(syscall=syscall,
                jobname=id_secondarymodel,
                infrastructure=INFRASTRUCTURE,
                dependency=id_splitcals)

    f.write(run_command)


    # ------------------------------------------------------------------------------
    # STEP 6: (1GC)
    # Perform reference calibration steps and apply to target(s)
                                               
    id_1GC = 'CL1GC'+code
    id_list.append(id_1GC)

    casalog = LOGS+'/casa_1GC_'+id_1GC+'.log'

    syscall = 'singularity exec '+CASA_CONTAINER+' '
    syscall += gen.generate_syscall_casa(casascript=OXKAT+'/1GC_06_casa_refcal_using_secondary_model.py',
                casalogfile=casalog)

    run_command = gen.job_handler(syscall=syscall,
                jobname=id_1GC,
                infrastructure=INFRASTRUCTURE,
                dependency=id_secondarymodel)

    f.write(run_command)


    # ------------------------------------------------------------------------------
    # STEP 7: 
    # Make gain table plots
                                         

    id_gainplots = 'PLTAB'+code
    id_list.append(id_gainplots)

    syscall = 'singularity exec '+RAGAVI_CONTAINER+' '
    syscall += 'python3 '+OXKAT+'/PLOT_gaintables.py cal_1GC_* cal_1GC_*calibrators.ms*'

    run_command = gen.job_handler(syscall=syscall,
                jobname=id_gainplots,
                infrastructure=INFRASTRUCTURE,
                dependency=id_1GC)

    f.write(run_command)


    # ------------------------------------------------------------------------------
    # STEP 8:
    # Split the corrected target data into individual Measurement Sets
                               

    id_splittargets = 'SPTRG'+code
    id_list.append(id_splittargets)

    casalog = LOGS+'/casa_1GC_'+id_splittargets+'.log'

    syscall = 'singularity exec '+CASA_CONTAINER+' '
    syscall += gen.generate_syscall_casa(casascript=OXKAT+'/1GC_07_casa_split_targets.py',
                casalogfile=casalog)

    run_command = gen.job_handler(syscall=syscall,
                jobname=id_splittargets,
                infrastructure=INFRASTRUCTURE,
                dependency=id_1GC)

    f.write(run_command)


    # ------------------------------------------------------------------------------
    # STEP 9: 
    # Make visibility plots
                                         

    id_visplots = 'PLVIS'+code
    id_list.append(id_visplots)

    syscall = 'singularity exec '+SHADEMS_CONTAINER+' '
    syscall += 'python3 '+OXKAT+'/1GC_08_plot_visibilities.py'

    run_command = gen.job_handler(syscall=syscall,
                jobname=id_visplots,
                infrastructure=INFRASTRUCTURE,
                dependency=id_splittargets)

    f.write(run_command)


    # ------------------------------------------------------------------------------



    if INFRASTRUCTURE == 'idia':
        kill = 'echo "scancel "$'+'" "$'.join(id_list)+' > '+kill_file+'\n'
        f.write(kill)
    elif INFRASTRUCTURE == 'chpc':
        kill = 'echo "qdel "$'+'" "$'.join(id_list)+' > '+kill_file+'\n'
        f.write(kill)
    

    f.close()


    gen.make_executable(submit_file)


if __name__ == "__main__":


    main()