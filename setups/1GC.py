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

    # Get paths from config and setup folders

    CWD = cfg.CWD
    OXKAT = cfg.OXKAT
    PARSETS = cfg.PARSETS
    SCRIPTS = cfg.SCRIPTS
    TOOLS = cfg.TOOLS
    LOGS = cfg.LOGS

    gen.setup_dir(SCRIPTS)
    gen.setup_dir(LOGS)


    # Set infrastructure and container path

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


    # Find containers needed for 1GC

    CASA_CONTAINER = gen.get_container(CONTAINER_PATH,cfg.CASA_PATTERN)
    RAGAVI_CONTAINER = gen.get_container(CONTAINER_PATH,cfg.RAGAVI_PATTERN)

 
    # Set names of the run and kill files, open run file for writing

    submit_file = 'submit_1GC_jobs.sh'
    kill_file = 'kill_1GC_jobs.sh'

    f = open(submit_file,'w')
    f.write('#!/usr/bin/env bash\n')


    # Get the MS name

    original_ms = glob.glob('*.ms')[0]
    code = gen.get_code(original_ms)
    myms = original_ms.replace('.ms','_wtspec.ms')


    # Initialise a list to hold all the job IDs

    id_list = []


    # ------------------------------------------------------------------------------
    # STEP 0:
    #  __  ___ _    _  ___                                    
    # / _|| o \ |  | ||_ _|                                   
    # \_ \|  _/ |_ | | | |                                    
    # |__/|_| |___||_| |_|                                    
    #                                                        
    #   _  _   _  _  __     _   _ _  ___  ___  _   __  ___ _  
    #  // / \ | \| ||  \   / \ | | || __|| o \/ \ / _|| __|\\ 
    # || | o || \\ || o ) | o || V || _| |   / o ( |_n| _|  ||
    # || |_n_||_|\_||__/  |_n_| \_/ |___||_|\\_n_|\__/|___| ||
    #  \\                                                  // 

    syscall = 'singularity exec '+CASA_CONTAINER+' '
    syscall += 'casa -c '+OXKAT+'/casa_average_to_1k_add_wtspec.py --nologger --log2term --nogui\n'

    id_average = 'AVRGE'+code
    id_list.append(id_average)

    run_command = gen.job_handler(syscall=syscall,
                jobname=id_average,
                infrastructure=infrastructure)

    f.write(run_command+'\n')


    # ------------------------------------------------------------------------------
    # STEP 1:
    #   __  ___  ___   ___ ___  _     _  ___ __  ___ 
    #  / _|| __||_ _| | o \ o \/ \   | || __/ _||_ _|
    # ( |_n| _|  | |  |  _/   ( o )n_| || _( (_  | | 
    #  \__/|___| |_|  |_| |_|\\\_/ \__/ |___\__| |_| 
    #                                               
    #  _  _  _  ___ _                                
    # | || \| || __/ \                               
    # | || \\ || _( o )                              
    # |_||_|\_||_| \_/                               
                   

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
    # STEP 2: Run basic flags
    #  ___  _   __  _  __                  
    # | o )/ \ / _|| |/ _|                 
    # | o \ o |\_ \| ( (_                  
    # |___/_n_||__/|_|\__|                 
    #                                     
    #  ___  _     _   __   __  _  _  _  __ 
    # | __|| |   / \ / _| / _|| || \| |/ _|
    # | _| | |_ | o ( |_n( |_n| || \\ ( |_n
    # |_|  |___||_n_|\__/ \__/|_||_|\_|\__/
                                    

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
    # STEP 3:
    #   _   _ _  ___ _  ___  _     _   __           
    #  / \ | | ||_ _/ \| __|| |   / \ / _|          
    # | o || U | | ( o ) _| | |_ | o ( |_n          
    # |_n_||___| |_|\_/|_|  |___||_n_|\__/          
    #                                              
    #   __   _   _    _  ___ ___  _  ___ _  ___  __ 
    #  / _| / \ | |  | || o ) o \/ \|_ _/ \| o \/ _|
    # ( (_ | o || |_ | || o \   / o || ( o )   /\_ \
    #  \__||_n_||___||_||___/_|\\_n_||_|\_/|_|\\|__/


    syscall = 'singularity exec '+CASA_CONTAINER+' '
    syscall += 'casa -c '+OXKAT+'/casa_autoflag_cals_data.py --nologger --log2term --nogui\n'

    id_autoflagcals = 'FLG_C'+code
    id_list.append(id_autoflagcals)

    run_command = gen.job_handler(syscall=syscall,
                jobname=id_autoflagcals,
                infrastructure=infrastructure,
                dependency=id_basic)

    f.write(run_command+'\n')


    # ------------------------------------------------------------------------------
    # STEP 4:
    #  __  ___ _    _  ___                          
    # / _|| o \ |  | ||_ _|                         
    # \_ \|  _/ |_ | | | |                          
    # |__/|_| |___||_| |_|                          
    #                                              
    #   __   _   _    _  ___ ___  _  ___ _  ___  __ 
    #  / _| / \ | |  | || o ) o \/ \|_ _/ \| o \/ _|
    # ( (_ | o || |_ | || o \   / o || ( o )   /\_ \
    #  \__||_n_||___||_||___/_|\\_n_||_|\_/|_|\\|__/
                                              

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
    # STEP 5:
    #   __  ___  ___   __  ___ __ _  _  _  __   _   ___ __ __
    #  / _|| __||_ _| / _|| __/ _/ \| \| ||  \ / \ | o \\ V /
    # ( |_n| _|  | |  \_ \| _( (( o ) \\ || o ) o ||   / \ / 
    #  \__/|___| |_|  |__/|___\__\_/|_|\_||__/|_n_||_|\\ |_| 
    #                                                       
    #  _   _  _  __  ___  _                                  
    # | \_/ |/ \|  \| __|| |                                 
    # | \_/ ( o ) o ) _| | |_                                
    # |_| |_|\_/|__/|___||___|                               
                                                       

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
    # STEP 6: (1GC)
    #  ___ ___  ___  ___  ___ ___  _  _  __  ___     
    # | o \ __|| __|| __|| o \ __|| \| |/ _|| __|    
    # |   / _| | _| | _| |   / _| | \\ ( (_ | _|     
    # |_|\\___||_|  |___||_|\\___||_|\_|\__||___|    
    #                                               
    #   __   _   _    _  ___ ___  _  ___  _  _  _  _ 
    #  / _| / \ | |  | || o ) o \/ \|_ _|| |/ \| \| |
    # ( (_ | o || |_ | || o \   / o || | | ( o ) \\ |
    #  \__||_n_||___||_||___/_|\\_n_||_| |_|\_/|_|\_|
                                               

    syscall = 'singularity exec '+CASA_CONTAINER+' '
    syscall += 'casa -c '+OXKAT+'/casa_1GC_using_secondary_model.py --nologger --log2term --nogui\n'

    id_1GC = 'ONEGC'+code
    id_list.append(id_1GC)

    run_command = gen.job_handler(syscall=syscall,
                jobname=id_1GC,
                infrastructure=infrastructure,
                dependency=id_secondarymodel)

    f.write(run_command+'\n')


    # ------------------------------------------------------------------------------
    # STEP 7: 
    #  ___ _   _ ___                           
    # | o \ | / \_ _|                          
    # |  _/ |( o ) |                           
    # |_| |___\_/|_|                           
    #                                        
    #   __   _   _   ___  _   ___ _    ___  __ 
    #  / _| / \ | | |_ _|/ \ | o ) |  | __|/ _|
    # ( (_ | o || |_ | || o || o \ |_ | _| \_ \
    #  \__||_n_||___||_||_n_||___/___||___||__/
                                         

    syscall = 'singularity exec '+RAGAVI_CONTAINER+' '
    syscall += 'python3 '+TOOLS+'/plot_gaintables.py\n'

    id_gainplots = 'GPLOT'+code
    id_list.append(id_gainplots)

    run_command = gen.job_handler(syscall=syscall,
                jobname=id_gainplots,
                infrastructure=infrastructure,
                dependency=id_1GC)

    f.write(run_command+'\n')


    # ------------------------------------------------------------------------------
    # STEP 8:
    #   _   _ _  ___ _  ___  _     _   __ 
    #  / \ | | ||_ _/ \| __|| |   / \ / _|
    # | o || U | | ( o ) _| | |_ | o ( |_n
    # |_n_||___| |_|\_/|_|  |___||_n_|\__/
    #                                    
    #  ___  _   ___  __  ___  ___ __      
    # |_ _|/ \ | o \/ _|| __||_ _/ _|     
    #  | || o ||   ( |_n| _|  | |\_ \     
    #  |_||_n_||_|\\\__/|___| |_||__/     
                                    

    syscall = 'singularity exec '+CASA_CONTAINER+' '
    syscall += 'casa -c '+OXKAT+'/casa_autoflag_targets_corrected.py --nologger --log2term --nogui\n'

    id_autoflagtargets = 'FLG_T'+code
    id_list.append(id_autoflagtargets)

    run_command = gen.job_handler(syscall=syscall,
                jobname=id_autoflagtargets,
                infrastructure=infrastructure,
                dependency=id_1GC)

    f.write(run_command+'\n')


    # ------------------------------------------------------------------------------
    # STEP 9:
    #  __  ___ _    _  ___           
    # / _|| o \ |  | ||_ _|          
    # \_ \|  _/ |_ | | | |           
    # |__/|_| |___||_| |_|           
    #                               
    #  ___  _   ___  __  ___  ___ __ 
    # |_ _|/ \ | o \/ _|| __||_ _/ _|
    #  | || o ||   ( |_n| _|  | |\_ \
    #  |_||_n_||_|\\\__/|___| |_||__/
                               

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
        kill = 'echo "scancel "$'+'" "$'.join(id_list)+' > '+kill_file
        f.write(kill+'\n')
    

    f.close()


if __name__ == "__main__":


    main()