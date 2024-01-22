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

    gen.preamble()
    print(gen.col()+'1GC (referenced calibration) setup')
    gen.print_spacer()

    if cfg.PRE_FIELDS != '':
        print(gen.col('Field selection')+cfg.PRE_FIELDS)
    if cfg.PRE_SCANS != '':
        print(gen.col('Scan selection')+cfg.PRE_SCANS)
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
    OWLCAT_CONTAINER = gen.get_container(CONTAINER_PATH,cfg.OWLCAT_PATTERN,USE_SINGULARITY)
    RAGAVI_CONTAINER = gen.get_container(CONTAINER_PATH,cfg.RAGAVI_PATTERN,USE_SINGULARITY)
    SHADEMS_CONTAINER = gen.get_container(CONTAINER_PATH,cfg.SHADEMS_PATTERN,USE_SINGULARITY)


    # ------------------------------------------------------------------------------
    #
    # 1GC recipe definition
    #
    # ------------------------------------------------------------------------------


    with open('project_info.json') as f:
        project_info = json.load(f)

    myms = project_info['master_ms']
    master_scan_list = project_info['master_scan_list']
    master_field_list = project_info['master_field_list']
    target_ids = project_info['target_ids']
    user_scans = cfg.PRE_SCANS.split(',')
    code = gen.get_code(myms)

    target_subms_list = gen.generate_target_subms_list(myms,master_scan_list,master_field_list,user_scans,target_ids)

    print(target_subms_list)

    dopol = cfg.CAL_1GC_DOPOL
    if not dopol:
        print(gen.col('Polarisation cal disabled as per config file'))
    else:
        polcal_tag = project_info['polcal_tag']
        if polcal_tag == 'None':
            print(gen.col('No polarisation calibrator found in this MS'))
            dopol = False
        else:
            print(gen.col(f'Using polarisation calibrator {polcal_tag}'))

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


    step = {}
    step['step'] = 1
    step['comment'] = 'Correct parallactic angle of working MS'
    step['dependency'] = 0
    step['id'] = 'PACOR'+code
    syscall = CONTAINER_RUNNER+ASTROPY_CONTAINER+' ' if USE_SINGULARITY else ''
    syscall += gen.generate_syscall_casa(casascript=cfg.OXKAT+'/oxkat/PRE_correct_parang.py')
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
    syscall += 'python3 '+cfg.OXKAT+'/PLOT_gaintables.py cal_1GC_*'
    step['syscall'] = syscall
    steps.append(step)


    # FLAG TARGET SUBMS

    step = {}
    step['step'] = 6
    step['comment'] = 'Split the corrected target data'
    step['dependency'] = 3
    step['id'] = 'SPTRG'+code
    syscall = CONTAINER_RUNNER+CASA_CONTAINER+' ' if USE_SINGULARITY else ''
    syscall += gen.generate_syscall_casa(casascript=cfg.OXKAT+'/1GC_09_casa_split_targets.py')
    step['syscall'] = syscall
    steps.append(step)


    step = {}
    step['step'] = 6
    step['comment'] = 'Plot the corrected calibrator visibilities'
    step['dependency'] = 5
    step['id'] = 'PLVIS'+code
    syscall = CONTAINER_RUNNER+SHADEMS_CONTAINER+' ' if USE_SINGULARITY else ''
    syscall += 'python3 '+cfg.OXKAT+'/1GC_10_plot_visibilities.py'
    step['syscall'] = syscall
    steps.append(step)


    if dopol:
        step = {}
        step['step'] = 7
        step['comment'] = 'Perform basic polarisation calibration'
        step['dependency'] = 6
        step['id'] = 'POLAR'+code
        syscall = CONTAINER_RUNNER+CASA_CONTAINER+' ' if USE_SINGULARITY else ''
        syscall += 'python3 '+cfg.OXKAT+'/1GC_11_casa_polcal.py'
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