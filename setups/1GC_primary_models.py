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


    gen.setup_dir(cfg.LOGS)
    gen.setup_dir(cfg.SCRIPTS)
    gen.setup_dir(cfg.GAINTABLES)


    INFRASTRUCTURE, CONTAINER_PATH = gen.set_infrastructure(sys.argv)
    if CONTAINER_PATH is not None:
        CONTAINER_RUNNER='singularity exec '
    else:
        CONTAINER_RUNNER=''

    # Get containers needed for this script

    CASA_CONTAINER = gen.get_container(CONTAINER_PATH,cfg.CASA_PATTERN)
    RAGAVI_CONTAINER = gen.get_container(CONTAINER_PATH,cfg.RAGAVI_PATTERN)
    SHADEMS_CONTAINER = gen.get_container(CONTAINER_PATH,cfg.SHADEMS_PATTERN)
    MEQTREES_CONTAINER = gen.get_container(CONTAINER_PATH,cfg.MEQTREES_PATTERN)

 
    # Set names of the run and kill files, open run file for writing

    submit_file = 'submit_1GC_jobs.sh'
    kill_file = cfg.SCRIPTS+'/kill_1GC_jobs.sh'

    f = open(submit_file,'w')
    f.write('#!/usr/bin/env bash\n')
    f.write('export SINGULARITY_BINDPATH='+cfg.BINDPATH+'\n')


    # Get the MS name

    original_ms = glob.glob('*.ms')[0]
    code = gen.get_code(original_ms)
    myms = original_ms.replace('.ms','_'+str(cfg.PRE_NCHANS)+'ch.ms')


    # ------------------------------------------------------------------------------


    steps = []

    step = {}
    step['step'] = 0
    step['comment'] = 'Split and average master MS'
    step['dependency'] = None
    step['id'] = 'SPPRE'+code
    syscall = CONTAINER_RUNNER+CASA_CONTAINER+' '
    syscall += gen.generate_syscall_casa(casascript=cfg.OXKAT+'/PRE_casa_average_to_1k_add_wtspec.py')
    step['syscall'] = syscall
    steps.append(step)


    step = {}
    step['step'] = 1
    step['comment'] = 'Run setup script to generate project_info pickle'
    step['dependency'] = 0
    step['id'] = 'SETUP'+code
    syscall = CONTAINER_RUNNER+MEQTREES_CONTAINER+' python '+cfg.OXKAT+'/1GC_00_setup.py '+myms
    step['syscall'] = syscall
    steps.append(step)


    step = {}
    step['step'] = 2
    step['comment'] = 'Rephase primary calibrator visibilties in-case of open-time offset problems'
    step['dependency'] = 1
    step['id'] = 'UVFIX'+code
    syscall = CONTAINER_RUNNER+CASA_CONTAINER+' '
    syscall += gen.generate_syscall_casa(casascript=cfg.OXKAT+'/1GC_01_casa_rephase_primary_calibrator.py')
    step['syscall'] = syscall
    steps.append(step)


    step = {}
    step['step'] = 3
    step['comment'] = 'Apply basic flagging steps to all fields'
    step['dependency'] = 2
    step['id'] = 'FGBAS'+code
    syscall = CONTAINER_RUNNER+CASA_CONTAINER+' '
    syscall += gen.generate_syscall_casa(casascript=cfg.OXKAT+'/1GC_02_casa_basic_flags.py')
    step['syscall'] = syscall
    steps.append(step)


    step = {}
    step['step'] = 4
    step['comment'] = 'Run auto-flaggers on primary calibrators'
    step['dependency'] = 3
    step['id'] = 'FGCAL'+code
    syscall = CONTAINER_RUNNER+CASA_CONTAINER+' '
    syscall += gen.generate_syscall_casa(casascript=cfg.OXKAT+'/1GC_03_casa_autoflag_cals_DATA.py')
    step['syscall'] = syscall
    steps.append(step)


    step = {}
    step['step'] = 5
    step['comment'] = 'Split off calibrator MS with 8 SPWs'
    step['dependency'] = 4
    step['id'] = 'SPCAL'+code
    syscall = CONTAINER_RUNNER+CASA_CONTAINER+' '
    syscall += gen.generate_syscall_casa(casascript=cfg.OXKAT+'/1GC_04_casa_split_calibrators.py')
    step['syscall'] = syscall
    steps.append(step)


    step = {}
    step['step'] = 6
    step['comment'] = 'Fit for intrinsic model of secondary calibrator'
    step['dependency'] = 5
    step['id'] = 'CLMOD'+code
    syscall = CONTAINER_RUNNER+CASA_CONTAINER+' '
    syscall += gen.generate_syscall_casa(casascript=cfg.OXKAT+'/1GC_05_casa_get_secondary_model.py')
    step['syscall'] = syscall
    steps.append(step)


    step = {}
    step['step'] = 7
    step['comment'] = 'Generate reference calibration solutions and apply to target(s)'
    step['dependency'] = 6
    step['id'] = 'CL1GC'+code
    syscall = CONTAINER_RUNNER+CASA_CONTAINER+' '
    syscall += gen.generate_syscall_casa(casascript=cfg.OXKAT+'/1GC_06_casa_refcal_using_secondary_model.py')
    step['syscall'] = syscall
    steps.append(step)


    step = {}
    step['step'] = 8
    step['comment'] = 'Plot the gain solutions'
    step['dependency'] = 7
    step['id'] = 'PLTAB'+code
    syscall = CONTAINER_RUNNER+RAGAVI_CONTAINER+' python3 '+cfg.OXKAT+'/PLOT_gaintables.py cal_1GC_* cal_1GC_*calibrators.ms*'
    step['syscall'] = syscall
    steps.append(step)


    step = {}
    step['step'] = 9
    step['comment'] = 'Split the corrected target data'
    step['dependency'] = 7
    step['id'] = 'PLTAB'+code
    syscall = CONTAINER_RUNNER+CASA_CONTAINER+' '
    syscall += gen.generate_syscall_casa(casascript=cfg.OXKAT+'/1GC_07_casa_split_targets.py')
    step['syscall'] = syscall
    steps.append(step)


    step = {}
    step['step'] = 10
    step['comment'] = 'Plot the corrected calibrator visibilities'
    step['dependency'] = 9
    step['id'] = 'PLVIS'+code
    syscall = CONTAINER_RUNNER+SHADEMS_CONTAINER+' python3 '+cfg.OXKAT+'/1GC_08_plot_visibilities.py'
    syscall += gen.generate_syscall_casa(casascript=cfg.OXKAT+'/1GC_07_casa_split_targets.py')
    step['syscall'] = syscall
    steps.append(step)

    # ------------------------------------------------------------------------------


    id_list = []

    for step in steps:

        step_id = step['id']
        id_list.append(step_id)
        if step['dependency'] is not None:
            dependency = steps[step['dependency']]['id']
        syscall = step['syscall']
        if step['slurm_config'] in step.keys():
            slurm_config = step['slurm_config']
        if step['pbs_config'] in step.keys():
            pbs_config = step['pbs_config']
        comment = step['comment']

        run_command = gen.job_handler(syscall = syscall,
                        jobname = id_wsclean,
                        infrastructure = INFRASTRUCTURE,
                        dependency = id_tricolour,
                        slurm_config = cfg.SLURM_WSCLEAN,
                        pbs_config = cfg.PBS_WSCLEAN)


        f.write('\n# '+comment+'\n')
        f.write(run_command)


    if INFRASTRUCTURE == 'idia' or INFRASTRUCTURE == 'hippo':
        kill = 'echo "scancel "$'+'" "$'.join(id_list)+' > '+kill_file+'\n'
        f.write(kill)
    elif INFRASTRUCTURE == 'chpc':
        kill = 'echo "qdel "$'+'" "$'.join(id_list)+' > '+kill_file+'\n'
        f.write(kill)
    

    f.close()


    gen.make_executable(submit_file)


if __name__ == "__main__":


    main()
