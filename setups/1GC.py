#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk


import glob
import json
import os.path as o
import sys
sys.path.append(o.abspath(o.join(o.dirname(sys.modules[__name__].__file__), "..")))


from oxkat import generate_jobs as gen
from oxkat import config as cfg


def main():

    USE_SINGULARITY = cfg.USE_SINGULARITY

    with open('project_info.json') as f:
        project_info = json.load(f)

    gen.preamble()

    # ------------------------------------------------------------------------------
    #
    # Print some summary info to let us know some important assumptions
    #
    # ------------------------------------------------------------------------------


    if cfg.PRE_FIELDS != '':
        print(gen.col()+'Field selection is '+cfg.PRE_FIELDS)
    else:
        print(gen.col()+'All fields selected')
    if cfg.PRE_SCANS != '':
        print(gen.col()+'Scan selection is '+cfg.PRE_SCANS)
    else:
        print(gen.col()+'All scans selected')

    primary_name = project_info['primary_name']
    print(gen.col()+f'Using primary calibrator {primary_name}')

    dopol = cfg.CAL_1GC_DOPOL
    if not dopol:
        print(gen.col()+'Polarisation cal disabled as per config file')
    else:
        polcal_tag = project_info['polcal_tag']
        if polcal_tag == 'None':
            print(gen.col()+'No polarisation calibrator found in this MS')
            dopol = False
        else:
            print(gen.col()+f'Using polarisation calibrator {polcal_tag}')

    gen.print_spacer()
    print(gen.col()+'1GC (referenced calibration) setup')
    gen.print_spacer()

    if float(project_info['integration_time'][0]) < 3.0:
        print(gen.col('Heads up!')+'These are 2 sec data, check for removal of bad scans')
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


    ASTROPY_CONTAINER = gen.get_container(CONTAINER_PATH,cfg.ASTROPY_PATTERN,USE_SINGULARITY)
    CASA_CONTAINER = gen.get_container(CONTAINER_PATH,cfg.CASA_PATTERN,USE_SINGULARITY)
    RAGAVI_CONTAINER = gen.get_container(CONTAINER_PATH,cfg.RAGAVI_PATTERN,USE_SINGULARITY)
    SHADEMS_CONTAINER = gen.get_container(CONTAINER_PATH,cfg.SHADEMS_PATTERN,USE_SINGULARITY)
    TRICOLOUR_CONTAINER = gen.get_container(CONTAINER_PATH,cfg.TRICOLOUR_PATTERN,USE_SINGULARITY)


    # ------------------------------------------------------------------------------
    #
    # 1GC recipe definition
    #
    # ------------------------------------------------------------------------------


    myms = project_info['master_ms']
    working_ms = project_info['working_ms']
    master_scan_list = project_info['master_scan_list']
    master_field_list = project_info['master_field_list']
    target_ids = project_info['target_ids']
    user_scans = cfg.PRE_SCANS
    code = gen.get_code(myms)
    target_subms_list = gen.generate_target_subms_list(working_ms,master_scan_list,master_field_list,user_scans,target_ids)
    steps = []


    step = {}
    step['step'] = 0
    step['comment'] = 'Split and average master MS'
    step['dependency'] = None
    step['id'] = 'SPPRE'+code
    syscall = CONTAINER_RUNNER+CASA_CONTAINER+' ' if USE_SINGULARITY else ''
    syscall += gen.generate_syscall_casa(casascript=cfg.OXKAT+'/PRE_casa_average_ms.py')
    step['syscall'] = syscall
    steps.append(step)


    # This can be parallelised with subMS

    step = {}
    step['step'] = 1
    step['comment'] = 'Correct parallactic angle of working MS'
    step['dependency'] = 0
    step['id'] = 'PACOR'+code
    syscall = CONTAINER_RUNNER+ASTROPY_CONTAINER+' ' if USE_SINGULARITY else ''
    syscall += 'python3 '+cfg.OXKAT+'/PRE_correct_parang.py'
    step['syscall'] = syscall
    steps.append(step)


    step = {}
    step['step'] = 2
    step['comment'] = 'Apply basic flagging steps to all fields'
    step['dependency'] = 1
    step['id'] = 'FGBAS'+code
    syscall = CONTAINER_RUNNER+CASA_CONTAINER+' ' if USE_SINGULARITY else ''
    syscall += gen.generate_syscall_casa(casascript=cfg.OXKAT+'/1GC_02_casa_basic_flags.py')
    step['syscall'] = syscall
    steps.append(step)


    step = {}
    step['step'] = 3
    step['comment'] = 'Run auto-flaggers on calibrators'
    step['dependency'] = 2
    step['id'] = 'FGCAL'+code
    syscall = CONTAINER_RUNNER+CASA_CONTAINER+' ' if USE_SINGULARITY else ''
    syscall += gen.generate_syscall_casa(casascript=cfg.OXKAT+'/1GC_05_casa_autoflag_cals_DATA.py')
    step['syscall'] = syscall
    steps.append(step)


    step = {}
    step['step'] = 4
    step['comment'] = 'Generate reference calibration solutions and apply to target(s)'
    step['dependency'] = 3
    step['id'] = 'CL1GC'+code
    syscall = CONTAINER_RUNNER+CASA_CONTAINER+' ' if USE_SINGULARITY else ''
    syscall += gen.generate_syscall_casa(casascript=cfg.OXKAT+'/1GC_casa_refcal.py')
    step['syscall'] = syscall
    steps.append(step)


    step = {}
    step['step'] = 5
    step['comment'] = 'Plot the gain solutions'
    step['dependency'] = 4
    step['id'] = 'PLTAB'+code
    syscall = CONTAINER_RUNNER+RAGAVI_CONTAINER+' ' if USE_SINGULARITY else ''
    syscall += 'python3 '+cfg.OXKAT+'/PLOT_gaintables.py B0,B1,G0,G1,G2,K0,K1,K2,K3,flux2,flux3'
    step['syscall'] = syscall
    steps.append(step)


    loop_dependencies = []
    n_steps1 = len(target_subms_list)
    d = n_steps1 - 1 # d for delta, loop offset for subsequent step numbers
                     # use d+= ... for additional MMS loops

    for i in range(0,n_steps1):

        subms = target_subms_list[i]
        code_i = gen.get_mms_code(subms)

        step = {}

        step['step'] = 6+i
        step['comment'] = 'Run Tricolour on '+subms
        step['dependency'] = 4
        step['id'] = 'T'+code_i+'_'+code
        step['slurm_config'] = cfg.SLURM_TRICOLOUR
        step['pbs_config'] = cfg.PBS_TRICOLOUR
        syscall = CONTAINER_RUNNER+TRICOLOUR_CONTAINER+' ' if USE_SINGULARITY else ''
        syscall += gen.generate_syscall_tricolour(myms = subms,
                    config = cfg.DATA+'/tricolour/target_flagging_1.yaml',
                    datacol = 'CORRECTED_DATA',
                    strategy = 'polarisation')
        step['syscall'] = syscall
        steps.append(step)

        loop_dependencies.append(6+i)


    step = {}
    step['step'] = 7+d
    step['comment'] = 'Split the corrected target data'
    step['dependency'] = loop_dependencies #[x+6 for x in loop_dependencies]
    step['id'] = 'SPTRG'+code
    syscall = CONTAINER_RUNNER+CASA_CONTAINER+' ' if USE_SINGULARITY else ''
    syscall += gen.generate_syscall_casa(casascript=cfg.OXKAT+'/1GC_09_casa_split_targets.py')
    step['syscall'] = syscall
    steps.append(step)


    step = {}
    step['step'] = 8+d
    step['comment'] = 'Plot the corrected calibrator visibilities'
    step['dependency'] = 7+d
    step['id'] = 'PLVIS'+code
    syscall = CONTAINER_RUNNER+SHADEMS_CONTAINER+' ' if USE_SINGULARITY else ''
    syscall += 'python3 '+cfg.OXKAT+'/1GC_10_plot_visibilities.py'
    step['syscall'] = syscall
    steps.append(step)


    step = {}
    step['step'] = 9+d
    step['comment'] = 'Plot the corrected polarisation calibrator visibilities (pre-polcal)'
    step['dependency'] = 8+d
    step['id'] = 'PLVIS'+code
    syscall = CONTAINER_RUNNER+SHADEMS_CONTAINER+' ' if USE_SINGULARITY else ''
    syscall += 'python3 '+cfg.OXKAT+'/1GC_12_plot_polcal_visibilities.py nopolcal'
    step['syscall'] = syscall
    steps.append(step)


    if dopol:


        step = {}
        step['step'] = 10+d
        step['comment'] = 'Perform basic polarisation calibration'
        step['dependency'] = 9+d
        step['id'] = 'POLAR'+code
        syscall = CONTAINER_RUNNER+CASA_CONTAINER+' ' if USE_SINGULARITY else ''
        syscall += gen.generate_syscall_casa(casascript=cfg.OXKAT+'/1GC_11_casa_polcal.py')
        step['syscall'] = syscall
        steps.append(step)


        step = {}
        step['step'] = 11+d
        step['comment'] = 'Plot the polarisation gain solutions'
        step['dependency'] = 10+d
        step['id'] = 'PLTAB'+code
        syscall = CONTAINER_RUNNER+RAGAVI_CONTAINER+' ' if USE_SINGULARITY else ''
        syscall += 'python3 '+cfg.OXKAT+'/PLOT_gaintables.py KX,Xf,D,Df,Df_preflag'
        step['syscall'] = syscall
        steps.append(step)


        step = {}
        step['step'] = 12+d
        step['comment'] = 'Plot the corrected polarisation calibrator visibilities (post-polcal)'
        step['dependency'] = 10+d
        step['id'] = 'PLVIS'+code
        syscall = CONTAINER_RUNNER+SHADEMS_CONTAINER+' ' if USE_SINGULARITY else ''
        syscall += 'python3 '+cfg.OXKAT+'/1GC_12_plot_polcal_visibilities.py polcal'
        step['syscall'] = syscall
        steps.append(step)


    # ------------------------------------------------------------------------------
    #
    # Write the run file and kill file based on the recipe
    #
    # ------------------------------------------------------------------------------


    submit_file = 'submit_1GC_jobs.sh'
    kill_file = cfg.SCRIPTS+'/kill_1GC_jobs.sh'
    gen.step_handler(steps,submit_file,kill_file,INFRASTRUCTURE)
    gen.print_spacer()
    print(gen.col('Run file')+submit_file)
    gen.print_spacer()


    # ------------------------------------------------------------------------------



if __name__ == "__main__":


    main()
