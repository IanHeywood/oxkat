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

    USE_SINGULARITY = cfg.USE_SINGULARITY

    if cfg.BAND[0].upper() == 'U':
        print(gen.col()+'Full-field primary models not available for UHF yet')
        gen.print_spacer()
        sys.exit()

    gen.preamble()
    print(gen.col()+'1GC (referenced calibration) setup')
    print(gen.col()+'Note that this recipe uses a full-field model for PKS B1934-638.')
    print(gen.col()+'This is somewhat experimental!')
    gen.print_spacer()

    # ------------------------------------------------------------------------------
    #
    # Setup paths, required containers, infrastructure
    #
    # ------------------------------------------------------------------------------


    gen.setup_dir(cfg.LOGS)
    gen.setup_dir(cfg.SCRIPTS)
    gen.setup_dir(cfg.GAINTABLES)


    INFRASTRUCTURE, CONTAINER_PATH = gen.set_infrastructure(sys.argv)
    if CONTAINER_PATH is not None:
        CONTAINER_RUNNER='singularity exec '
    else:
        CONTAINER_RUNNER=''


    CASA_CONTAINER = gen.get_container(CONTAINER_PATH,cfg.CASA_PATTERN,USE_SINGULARITY)
    MEQTREES_CONTAINER = gen.get_container(CONTAINER_PATH,cfg.MEQTREES_PATTERN,USE_SINGULARITY)
    RAGAVI_CONTAINER = gen.get_container(CONTAINER_PATH,cfg.RAGAVI_PATTERN,USE_SINGULARITY)
    SHADEMS_CONTAINER = gen.get_container(CONTAINER_PATH,cfg.SHADEMS_PATTERN,USE_SINGULARITY)
    WSCLEAN_CONTAINER = gen.get_container(CONTAINER_PATH,cfg.WSCLEAN_PATTERN,USE_SINGULARITY)


    # ------------------------------------------------------------------------------
    #
    # 1GC recipe definition
    #
    # ------------------------------------------------------------------------------


    original_ms = glob.glob('*.ms')[0]
    code = gen.get_code(original_ms)
    myms = original_ms.replace('.ms','_'+str(cfg.PRE_NCHANS)+'ch.ms')


    steps = []

    step = {}
    step['step'] = 0
    step['comment'] = 'Split and average master MS'
    step['dependency'] = None
    step['id'] = 'SPPRE'+code
    syscall = CONTAINER_RUNNER+CASA_CONTAINER+' ' if USE_SINGULARITY else ''
    syscall += gen.generate_syscall_casa(casascript=cfg.OXKAT+'/PRE_casa_average_to_1k_add_wtspec.py')
    step['syscall'] = syscall
    steps.append(step)


    step = {}
    step['step'] = 1
    step['comment'] = 'Run setup script to generate project_info pickle'
    step['dependency'] = 0
    step['id'] = 'SETUP'+code
    syscall = CONTAINER_RUNNER+MEQTREES_CONTAINER+' ' if USE_SINGULARITY else ''
    syscall += 'python '+cfg.OXKAT+'/1GC_00_setup.py '+myms
    step['syscall'] = syscall
    steps.append(step)


    step = {}
    step['step'] = 2
    step['comment'] = 'Rephase primary calibrator visibilties in case of open-time offset problems'
    step['dependency'] = 1
    step['id'] = 'UVFIX'+code
    syscall = CONTAINER_RUNNER+CASA_CONTAINER+' ' if USE_SINGULARITY else ''
    syscall += gen.generate_syscall_casa(casascript=cfg.OXKAT+'/1GC_01_casa_rephase_primary_calibrator.py')
    step['syscall'] = syscall
    steps.append(step)


    step = {}
    step['step'] = 3
    step['comment'] = 'Apply basic flagging steps to all fields'
    step['dependency'] = 2
    step['id'] = 'FGBAS'+code
    syscall = CONTAINER_RUNNER+CASA_CONTAINER+' ' if USE_SINGULARITY else ''
    syscall += gen.generate_syscall_casa(casascript=cfg.OXKAT+'/1GC_02_casa_basic_flags.py')
    step['syscall'] = syscall
    steps.append(step)


    # step = {}
    # step['step'] = 4
    # step['comment'] = 'Add CORRECTED_DATA and MODEL_DATA columns'
    # step['dependency'] = 3
    # step['id'] = 'ADCOL'+code
    # syscall = CONTAINER_RUNNER+MEQTREES_CONTAINER+' ' if USE_SINGULARITY else ''
    # syscall += 'python '+cfg.TOOLS+'/add_MS_column.py --colname CORRECTED_DATA,MODEL_DATA '+myms
    # step['syscall'] = syscall
    # steps.append(step)


    step = {}
    step['step'] = 4
    step['comment'] = 'Predict field sources for primary if required'
    step['dependency'] = 3 # change back to 4 if above step is required
    step['id'] = 'SETCC'+code
    step['slurm_config'] = cfg.SLURM_WSCLEAN
    step['pbs_config'] = cfg.PBS_WSCLEAN
    syscall = CONTAINER_RUNNER+WSCLEAN_CONTAINER+' ' if USE_SINGULARITY else ''
    syscall += 'python2 '+cfg.OXKAT+'/1GC_03_primary_cal_field_sources.py'
    step['syscall'] = syscall
    steps.append(step)


    step = {}
    step['step'] = 5
    step['comment'] = 'Copy MODEL_DATA to CORRECTED_DATA (temp storage for primary field sources)'
    step['dependency'] = 4
    step['id'] = 'CPCOL'+code
    syscall = CONTAINER_RUNNER+MEQTREES_CONTAINER+' ' if USE_SINGULARITY else ''
    syscall += 'python '+cfg.TOOLS+'/copy_MS_column.py --fromcol MODEL_DATA --tocol CORRECTED_DATA '+myms
    step['syscall'] = syscall
    steps.append(step)


    step = {}
    step['step'] = 6
    step['comment'] = 'Run setjy for primary calibrator'
    step['dependency'] = 5
    step['id'] = 'SETJY'+code
    syscall = CONTAINER_RUNNER+CASA_CONTAINER+' ' if USE_SINGULARITY else ''
    syscall += gen.generate_syscall_casa(casascript=cfg.OXKAT+'/1GC_04_casa_setjy.py')
    step['syscall'] = syscall
    steps.append(step)


    step = {}
    step['step'] = 7
    step['comment'] = 'Add field source model in CORRECTED_DATA to component model in MODEL_DATA'
    step['dependency'] = 6
    step['id'] = 'SMCOL'+code
    syscall = CONTAINER_RUNNER+MEQTREES_CONTAINER+' ' if USE_SINGULARITY else ''
    syscall += 'python '+cfg.TOOLS+'/sum_MS_columns.py --src CORRECTED_DATA --dest MODEL_DATA '+myms
    step['syscall'] = syscall
    steps.append(step)


    step = {}
    step['step'] = 8
    step['comment'] = 'Run auto-flaggers on calibrators'
    step['dependency'] = 7
    step['id'] = 'FGCAL'+code
    syscall = CONTAINER_RUNNER+CASA_CONTAINER+' ' if USE_SINGULARITY else ''
    syscall += gen.generate_syscall_casa(casascript=cfg.OXKAT+'/1GC_05_casa_autoflag_cals_DATA.py')
    step['syscall'] = syscall
    steps.append(step)


    step = {}
    step['step'] = 9
    step['comment'] = 'Split off calibrator MS with 8 SPWs'
    step['dependency'] = 8
    step['id'] = 'SPCAL'+code
    syscall = CONTAINER_RUNNER+CASA_CONTAINER+' ' if USE_SINGULARITY else ''
    syscall += gen.generate_syscall_casa(casascript=cfg.OXKAT+'/1GC_06_casa_split_calibrators.py')
    step['syscall'] = syscall
    steps.append(step)


    step = {}
    step['step'] = 10
    step['comment'] = 'Fit for intrinsic model of secondary calibrator'
    step['dependency'] = 9
    step['id'] = 'CLMOD'+code
    syscall = CONTAINER_RUNNER+CASA_CONTAINER+' ' if USE_SINGULARITY else ''
    syscall += gen.generate_syscall_casa(casascript=cfg.OXKAT+'/1GC_07_casa_get_secondary_model.py')
    step['syscall'] = syscall
    steps.append(step)


    step = {}
    step['step'] = 11
    step['comment'] = 'Generate reference calibration solutions and apply to target(s)'
    step['dependency'] = 10
    step['id'] = 'CL1GC'+code
    syscall = CONTAINER_RUNNER+CASA_CONTAINER+' ' if USE_SINGULARITY else ''
    syscall += gen.generate_syscall_casa(casascript=cfg.OXKAT+'/1GC_08_casa_refcal_using_secondary_model.py')
    step['syscall'] = syscall
    steps.append(step)


    step = {}
    step['step'] = 12
    step['comment'] = 'Plot the gain solutions'
    step['dependency'] = 11
    step['id'] = 'PLTAB'+code
    syscall = CONTAINER_RUNNER+RAGAVI_CONTAINER+' ' if USE_SINGULARITY else ''
    syscall += 'python3 '+cfg.OXKAT+'/PLOT_gaintables.py cal_1GC_* cal_1GC_*calibrators.ms*'
    step['syscall'] = syscall
    steps.append(step)


    step = {}
    step['step'] = 13
    step['comment'] = 'Split the corrected target data'
    step['dependency'] = 11
    step['id'] = 'SPTRG'+code
    syscall = CONTAINER_RUNNER+CASA_CONTAINER+' ' if USE_SINGULARITY else ''
    syscall += gen.generate_syscall_casa(casascript=cfg.OXKAT+'/1GC_09_casa_split_targets.py')
    step['syscall'] = syscall
    steps.append(step)


    step = {}
    step['step'] = 14
    step['comment'] = 'Plot the corrected calibrator visibilities'
    step['dependency'] = 13
    step['id'] = 'PLVIS'+code
    syscall = CONTAINER_RUNNER+SHADEMS_CONTAINER+' ' if USE_SINGULARITY else ''
    syscall += 'python3 '+cfg.OXKAT+'/1GC_10_plot_visibilities.py'
    step['syscall'] = syscall
    steps.append(step)



    # ------------------------------------------------------------------------------
    #
    # Write the run file and kill file based on the recipe
    #
    # ------------------------------------------------------------------------------

    submit_file = 'submit_1GC_jobs.sh'
    kill_file = cfg.SCRIPTS+'/kill_1GC_jobs.sh'

    f = open(submit_file,'w')
    f.write('#!/usr/bin/env bash\n')
    f.write('export SINGULARITY_BINDPATH='+cfg.BINDPATH+'\n')

    id_list = []

    for step in steps:

        step_id = step['id']
        id_list.append(step_id)
        if step['dependency'] is not None:
            dependency = steps[step['dependency']]['id']
        else:
            dependency = None
        syscall = step['syscall']
        if 'slurm_config' in step.keys():
            slurm_config = step['slurm_config']
        else:
            slurm_config = cfg.SLURM_DEFAULTS
        if 'pbs_config' in step.keys():
            pbs_config = step['pbs_config']
        else:
            pbs_config = cfg.PBS_DEFAULTS
        comment = step['comment']

        run_command = gen.job_handler(syscall = syscall,
                        jobname = step_id,
                        infrastructure = INFRASTRUCTURE,
                        dependency = dependency,
                        slurm_config = slurm_config,
                        pbs_config = pbs_config)


        f.write('\n# '+comment+'\n')
        f.write(run_command)


    if INFRASTRUCTURE == 'idia' or INFRASTRUCTURE == 'hippo':
        kill = '\necho "scancel "$'+'" "$'.join(id_list)+' > '+kill_file+'\n'
        f.write(kill)
    elif INFRASTRUCTURE == 'chpc':
        kill = '\necho "qdel "$'+'" "$'.join(id_list)+' > '+kill_file+'\n'
        f.write(kill)
    
    f.close()

    gen.make_executable(submit_file)

    gen.print_spacer()
    print(gen.col('Run file')+submit_file)
    gen.print_spacer()


    # ------------------------------------------------------------------------------



if __name__ == "__main__":


    main()
