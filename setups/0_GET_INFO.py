#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk


import glob
import os.path as o
import sys
sys.path.append(o.abspath(o.join(o.dirname(sys.modules[__name__].__file__), "..")))


from oxkat import generate_jobs as gen
from oxkat import config as cfg

def main():

    USE_SINGULARITY = cfg.USE_SINGULARITY

    gen.preamble()
    gen.print_spacer()
    print(gen.col()+'Setting up job to examine master MS')
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
   

    # ------------------------------------------------------------------------------
    #
    # 1GC recipe definition
    #
    # ------------------------------------------------------------------------------


    myms = glob.glob('*.ms')
    if len(myms) == 0:
        print(gen.col()+'No MS found in current directory, please check')
        gen.print_spacer()
        sys.exit()

    myms = myms[0]
    code = gen.get_code(myms)

    steps = []


    step = {}
    step['step'] = 0
    step['comment'] = 'Run setup script to generate project_info json file'
    step['dependency'] = None
    step['id'] = 'INFO_'+code
    syscall = CONTAINER_RUNNER+ASTROPY_CONTAINER+' ' if USE_SINGULARITY else ''
    syscall += ' python3 '+cfg.TOOLS+'/ms_info.py '+myms+'\n'
    syscall += CONTAINER_RUNNER+ASTROPY_CONTAINER+' ' if USE_SINGULARITY else ''
    syscall += ' python3 '+cfg.TOOLS+'/scan_times.py '+myms+'\n'
    syscall += CONTAINER_RUNNER+ASTROPY_CONTAINER+' ' if USE_SINGULARITY else ''
    syscall += ' python3 '+cfg.TOOLS+'/find_sun.py '+myms+'\n'
    syscall += CONTAINER_RUNNER+ASTROPY_CONTAINER+' ' if USE_SINGULARITY else ''
    syscall += ' python3 '+cfg.OXKAT+'/1GC_00_setup.py '+myms
    step['syscall'] = syscall
    steps.append(step)



    # ------------------------------------------------------------------------------
    #
    # Write the run file and kill file based on the recipe
    #
    # ------------------------------------------------------------------------------


    submit_file = 'submit_info_job.sh'
    kill_file = cfg.SCRIPTS+'/kill_info_job.sh'

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