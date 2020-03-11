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


    CWD = cfg.CWD
    OXKAT = cfg.OXKAT
    PARSETS = cfg.PARSETS
    SCRIPTS = cfg.SCRIPTS
    TOOLS = cfg.TOOLS
    LOGS = cfg.LOGS


    if len(sys.argv) == 1:
        print('Please specify infrastructure (idia / chpc / node)')
        sys.exit()

    if sys.argv[1].lower() == 'idia':
        infrastructure = 'idia'
        CONTAINER_PATH = cfg.IDIA_CONTAINER_PATH
    elif sys.argv[1].lower() == 'chpc':
        infrastructure = 'chpc'
        CONTAINER_PATH = cfg.CHPC_CONTAINER_PATH
    elif sys.argv[1].lower() == 'node':
        CONTAINER_PATH = cfg.NODE_CONTAINER_PATH
        infrastructure = 'node'


    CASA_CONTAINER = gen.get_container(CONTAINER_PATH,cfg.CASA_PATTERN)
    RAGAVI_CONTAINER = gen.get_container(CONTAINER_PATH,cfg.RAGAVI_PATTERN)

 
    submit_file = 'submit_1GC_jobs.sh'
    kill_file = 'kill_1GC_jobs.sh'


    gen.setup_dir(SCRIPTS)
    gen.setup_dir(LOGS)


    f = open(submit_file,'w')
    f.write('#!/usr/bin/env bash\n')


    myms = glob.glob('*.ms')[0]
    code = gen.get_code(myms)
    myms = myms.replace('.ms','_wtspec.ms')


    id_list = []


    # ------------------------------------------------------------------------------
    # Average MS to 1k channels and add weight spectrum column


    syscall = 'singularity exec '+CASA_CONTAINER+' '
    syscall += 'casa -c '+OXKAT+'/casa_average_to_1k_add_wtspec.py --nologger --log2term --nogui\n'

    id_average = 'AVRGE'+code
    id_list.append(id_average)

    run_command = gen.job_handler(syscall=syscall,
                jobname=id_average,
                infrastructure=infrastructure)

    f.write(run_command+'\n')


    # ------------------------------------------------------------------------------
    # Run setup script


    syscall = 'singularity exec '+RAGAVI_CONTAINER+' '
    syscall += 'python '+OXKAT+'/00_setup.py '+myms+'\n'

    id_setup = 'INFO_'+code
    id_list.append(id_setup)

    run_command = gen.job_handler(syscall=syscall,
                jobname=id_setup,
                infrastructure=infrastructure,
                dependency=id_average)

    f.write(run_command+'\n')


    # ------------------------------------------------------------------------------
    # Run basic flags


    syscall = 'singularity exec '+CASA_CONTAINER+' '
    syscall += 'casa -c '+OXKAT+'/casa_basic_flags.py --nologger --log2term --nogui\n'

    id_basic = 'BASIC'+code
    id_list.append(id_basic)

    run_command = gen.job_handler(syscall=syscall,
                jobname=id_basic,
                infrastructure=infrastructure,
                dependency=id_setup)

    f.write(run_command+'\n')


    # ------------------------------------------------------------------------------
    # Autoflagger on calibrators (DATA)


    syscall = 'singularity exec '+CASA_CONTAINER+' '
    syscall += 'casa -c '+OXKAT+'/casa_autoflag_cals_data.py --nologger --log2term --nogui\n'

    id_autoflagcals = 'CALFG'+code
    id_list.append(id_autoflagcals)

    run_command = gen.job_handler(syscall=syscall,
                jobname=id_autoflagcals,
                infrastructure=infrastructure,
                dependency=id_basic)

    f.write(run_command+'\n')


    # ------------------------------------------------------------------------------
    # Split calibrators 


    syscall = 'singularity exec '+CASA_CONTAINER+' '
    syscall += 'casa -c '+OXKAT+'/casa_split_calibrators.py --nologger --log2term --nogui\n'

    id_splitcals = 'SPLCL'+code
    id_list.append(id_splitcals)

    run_command = gen.job_handler(syscall=syscall,
                jobname=id_splitcals,
                infrastructure=infrastructure,
                dependency=id_autoflagcals)

    f.write(run_command+'\n')


    # ------------------------------------------------------------------------------
    # Get secondary model 


    syscall = 'singularity exec '+CASA_CONTAINER+' '
    syscall += 'casa -c '+OXKAT+'/casa_get_secondary_model.py --nologger --log2term --nogui\n'

    id_secondarymodel = 'MODEL'+code
    id_list.append(id_secondarymodel)

    run_command = gen.job_handler(syscall=syscall,
                jobname=id_secondarymodel,
                infrastructure=infrastructure,
                dependency=id_splitcals)

    f.write(run_command+'\n')


    # ------------------------------------------------------------------------------
    # 1GC using secondary model 


    syscall = 'singularity exec '+CASA_CONTAINER+' '
    syscall += 'casa -c '+OXKAT+'/casa_1GC_using_secondary_model.py --nologger --log2term --nogui\n'

    id_1GC = '1GC__'+code
    id_list.append(id_1GC)

    run_command = gen.job_handler(syscall=syscall,
                jobname=id_1GC,
                infrastructure=infrastructure,
                dependency=id_secondarymodel)

    f.write(run_command+'\n')


    # ------------------------------------------------------------------------------
    # Plot calibration tables 


    syscall = 'singularity exec '+RAGAVI_CONTAINER+' '
    syscall += 'python3 '+TOOLS+'/plot_gaintables.py\n'

    id_gainplots = 'GAINS'+code
    id_list.append(id_gainplots)

    run_command = gen.job_handler(syscall=syscall,
                jobname=id_gainplots,
                infrastructure=infrastructure,
                dependency=id_1GC)

    f.write(run_command+'\n')


    # ------------------------------------------------------------------------------
    # Autoflagger on targets

    syscall = 'singularity exec '+CASA_CONTAINER+' '
    syscall += 'casa -c '+OXKAT+'/casa_autoflag_targets_corrected.py --nologger --log2term --nogui\n'

    id_autoflagtargets = 'TARFG'+code
    id_list.append(id_autoflagtargets)

    run_command = gen.job_handler(syscall=syscall,
                jobname=id_autoflagtargets,
                infrastructure=infrastructure,
                dependency=id_1GC)

    f.write(run_command+'\n')


    # ------------------------------------------------------------------------------
    # Split targets

    syscall = 'singularity exec '+CASA_CONTAINER+' '
    syscall += 'casa -c '+OXKAT+'/casa_split_targets.py --nologger --log2term --nogui\n'

    id_splittargets = 'SPLTG'+code
    id_list.append(id_splittargets)

    run_command = gen.job_handler(syscall=syscall,
                jobname=id_splittargets,
                infrastructure=infrastructure,
                dependency=id_autoflagtargets)

    f.write(run_command+'\n')


    # ------------------------------------------------------------------------------


    if infrastructure in ['idia','chpc']:
        kill = 'echo "scancel "$'+'" "$'.join(id_list)+'" > '+kill_file
        f.write(kill+'\n')
    

    f.close()


if __name__ == "__main__":


    main()