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

    mymms = glob.glob('*.mms')[0]
    subms_list = sorted(glob.glob(mymms+'/SUBMSS/*.ms'))

    USE_SINGULARITY = cfg.USE_SINGULARITY

    gen.preamble()
    print(gen.col()+'Prep spectral line MMS')
    gen.print_spacer()

    # ------------------------------------------------------------------------------
    #
    # Setup paths, required containers, infrastructure
    #
    # ------------------------------------------------------------------------------

    DATA = cfg.DATA

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
    TRICOLOUR_CONTAINER = gen.get_container(CONTAINER_PATH,cfg.TRICOLOUR_PATTERN,USE_SINGULARITY)


    # ------------------------------------------------------------------------------
    #
    # 1GC recipe definition
    #
    # ------------------------------------------------------------------------------


    code = gen.get_code(mymms)

    steps = []

    if cfg.BAND[0].upper() == 'L':


        step = {}
        step['step'] = 0
        step['comment'] = 'Run setjy for primary calibrator'
        step['dependency'] = None
        step['id'] = 'SETJY'+code
        syscall = CONTAINER_RUNNER+CASA_CONTAINER+' ' if USE_SINGULARITY else ''
        syscall += gen.generate_syscall_casa(casascript=cfg.OXKAT+'/1GC_04_casa_setjy.py',
                extra_args = 'myms='+mymms)
        step['syscall'] = syscall
        steps.append(step)

        i_loop_dependencies = []
        n = len(subms_list)

        for i in range(0,2*n,2): # Two steps in this sub-loop hence 2*n

            myms = subms_list[int(i/2)]
            code_i = gen.get_mms_code(myms)

            step = {}
            step['step'] = i+1 # One step prior to this sub-loop
            step['comment'] = 'Apply basic flagging steps to '+myms
            step['dependency'] = 0
            step['id'] = 'F'+code_i+'_'+code
            syscall = CONTAINER_RUNNER+CASA_CONTAINER+' ' if USE_SINGULARITY else ''
            syscall += gen.generate_syscall_casa(casascript=cfg.OXKAT+'/1GC_02_casa_basic_flags.py',
                    extra_args = 'myms='+myms)
            step['syscall'] = syscall
            steps.append(step)

            step = {}
            step['step'] = i+2
            step['comment'] = 'Run Tricolour on '+myms
            step['dependency'] = i+1
            step['id'] = 'T'+code+'_'+code_i
            step['slurm_config'] = cfg.SLURM_TRICOLOUR
            step['pbs_config'] = cfg.PBS_TRICOLOUR
            syscall = CONTAINER_RUNNER+TRICOLOUR_CONTAINER+' ' if USE_SINGULARITY else ''
            syscall += gen.generate_syscall_tricolour(myms = myms,
                        config = DATA+'/tricolour/target_flagging_1.yaml',
                        datacol = 'DATA',
                        strategy = 'polarisation')
            step['syscall'] = syscall
            steps.append(step)

            i_loop_dependencies.append(i+2)

        # DUMMY SETUP HERE JUST TO TEST DEPENDENCY CHAINS FOR NOW
        step = {}
        step['step'] = i_loop_dependencies[-1]+1
        step['comment'] = 'Generate full spectral resolution bandpass solutions'
        step['dependency'] = i_loop_dependencies
        step['id'] = 'BPASS'+code
        step['slurm_config'] = cfg.SLURM_WSCLEAN
        step['pbs_config'] = cfg.PBS_WSCLEAN
        syscall = CONTAINER_RUNNER+CASA_CONTAINER+' ' if USE_SINGULARITY else ''
        syscall += gen.generate_syscall_casa(casascript=cfg.OXKAT+'/1GC_casa_LINE_refcal_primary.py')
        step['syscall'] = syscall
        steps.append(step)



                       
#    elif cfg.BAND[0].upper() == 'U':


    # ------------------------------------------------------------------------------
    #
    # Write the run file and kill file based on the recipe
    #
    # ------------------------------------------------------------------------------


    submit_file = 'submit_line_prep_jobs.sh'
    kill_file = cfg.SCRIPTS+'/kill_line_prep_jobs.sh'

    f = open(submit_file,'w')
    f.write('#!/usr/bin/env bash\n')
    f.write('export SINGULARITY_BINDPATH='+cfg.BINDPATH+'\n')

    id_list = []

    for step in steps:

        step_id = step['id']
        id_list.append(step_id)
        step_dependency = step['dependency']
        if step_dependency is not None:
            if isinstance(step_dependency,list):
                dependency = ':'.join(steps[ii]['id'] for ii in step_dependency)
            else:
                dependency = steps[step_dependency]['id']
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
