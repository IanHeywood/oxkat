#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk


import glob
import os.path as o
import pickle
import sys
sys.path.append(o.abspath(o.join(o.dirname(sys.modules[__name__].__file__), "..")))


from oxkat import generate_jobs as gen


def main():


    CWD = gen.CWD
    OXKAT = gen.OXKAT
    PARSETS = gen.PARSETS
    SCRIPTS = gen.SCRIPTS
    TOOLS = gen.TOOLS
    LOGS = gen.LOGS
    CASA_CONTAINER = gen.CASA_CONTAINER
    RAGAVI_CONTAINER = gen.RAGAVI_CONTAINER
    DDFACET_CONTAINER = gen.DDFACET_CONTAINER
    XCASA_CONTAINER = gen.XCASA_CONTAINER
    XRAGAVI_CONTAINER = gen.XRAGAVI_CONTAINER
    XDDFACET_CONTAINER = gen.XDDFACET_CONTAINER
 

    submit_file = 'submit_1GC_jobs.sh'
    kill_file = 'kill_1GC_jobs.sh'
    run_file = 'run_1GC_jobs.sh'


    gen.setup_dir(SCRIPTS)
    gen.setup_dir(LOGS)


    f = open(submit_file,'w')
    g = open(run_file,'w')


    f.write('#!/usr/bin/env bash\n')
    g.write('#!/usr/bin/env bash\n')


    myms = glob.glob('*.ms')[0]
    code = gen.get_code(myms)
    myms = myms.replace('.ms','_wtspec.ms')


    # ------------------------------------------------------------------------------
    # Average MS to 1k channels and add weight spectrum column


    slurmfile = SCRIPTS+'/slurm_avg_'+code+'.sh'
    logfile = LOGS+'/slurm_avg_'+code+'.log'


    syscall = 'singularity exec '+CASA_CONTAINER+' '
    syscall += 'casa -c '+OXKAT+'/casa_average_to_1k_add_wtspec.py --nologger --log2term --nogui\n'


    gen.write_slurm(opfile=slurmfile,
                jobname=code+'avrge',
                logfile=logfile,
                syscall=syscall)


    syscall = syscall.replace(CASA_CONTAINER,XCASA_CONTAINER)
    g.write(syscall+'\n')


    job_id_avg = 'AVG_'+code
    syscall = job_id_avg+"=`sbatch "+slurmfile+" | awk '{print $4}'`"
    f.write(syscall+'\n')


    # ------------------------------------------------------------------------------
    # Run setup script


    slurmfile = SCRIPTS+'/slurm_setup_'+code+'.sh'
    logfile = LOGS+'/slurm_setup_'+code+'.log'


    syscall = 'singularity exec '+DDFACET_CONTAINER+' '
    syscall += 'python '+OXKAT+'/00_setup.py '+myms+'\n'


    gen.write_slurm(opfile=slurmfile,
                jobname=code+'setup',
                logfile=logfile,
                syscall=syscall)


    syscall = syscall.replace(DDFACET_CONTAINER,XDDFACET_CONTAINER)
    g.write(syscall+'\n')


    job_id_info = 'INFO_'+code
    syscall = job_id_info+"=`sbatch -d afterok:${"+job_id_avg+"} "+slurmfile+" | awk '{print $4}'`"
    f.write(syscall+'\n')


    # ------------------------------------------------------------------------------
    # Run basic flags


    slurmfile = SCRIPTS+'/slurm_basicflags_'+code+'.sh'
    logfile = LOGS+'/slurm_basicflags_'+code+'.log'


    syscall = 'singularity exec '+CASA_CONTAINER+' '
    syscall += 'casa -c '+OXKAT+'/casa_basic_flags.py --nologger --log2term --nogui\n'


    gen.write_slurm(opfile=slurmfile,
                jobname=code+'basic',
                logfile=logfile,
                syscall=syscall)


    syscall = syscall.replace(CASA_CONTAINER,XCASA_CONTAINER)
    g.write(syscall+'\n')


    job_id_basic = 'BASIC_'+code
    syscall = job_id_basic+"=`sbatch -d afterok:${"+job_id_info+"} "+slurmfile+" | awk '{print $4}'`"
    f.write(syscall+'\n')


    # ------------------------------------------------------------------------------
    # Autoflagger on calibrators (DATA)


    slurmfile = SCRIPTS+'/slurm_autoflag_cals_data_'+code+'.sh'
    logfile = LOGS+'/slurm_autoflag_cals_data_'+code+'.log'


    syscall = 'singularity exec '+CASA_CONTAINER+' '
    syscall += 'casa -c '+OXKAT+'/casa_autoflag_cals_data.py --nologger --log2term --nogui\n'


    gen.write_slurm(opfile=slurmfile,
                jobname=code+'flag1',
                logfile=logfile,
                syscall=syscall)


    syscall = syscall.replace(CASA_CONTAINER,XCASA_CONTAINER)
    g.write(syscall+'\n')


    job_id_flag1 = 'FLAG1_'+code
    syscall = job_id_flag1+"=`sbatch -d afterok:${"+job_id_basic+"} "+slurmfile+" | awk '{print $4}'`"
    f.write(syscall+'\n')


    # ------------------------------------------------------------------------------
    # Split calibrators 


    slurmfile = SCRIPTS+'/slurm_split_cals_'+code+'.sh'
    logfile = LOGS+'/slurm_split_cals_'+code+'.log'


    syscall = 'singularity exec '+CASA_CONTAINER+' '
    syscall += 'casa -c '+OXKAT+'/casa_split_calibrators.py --nologger --log2term --nogui\n'


    gen.write_slurm(opfile=slurmfile,
                jobname=code+'spcal',
                logfile=logfile,
                syscall=syscall)


    syscall = syscall.replace(CASA_CONTAINER,XCASA_CONTAINER)
    g.write(syscall+'\n')


    job_id_split_cals = 'SPLITCAL_'+code
    syscall = job_id_split_cals+"=`sbatch -d afterok:${"+job_id_flag1+"} "+slurmfile+" | awk '{print $4}'`"
    f.write(syscall+'\n')


    # ------------------------------------------------------------------------------
    # Get secondary model 


    slurmfile = SCRIPTS+'/slurm_secondary_model_'+code+'.sh'
    logfile = LOGS+'/slurm_secondary_model_'+code+'.log'


    syscall = 'singularity exec '+CASA_CONTAINER+' '
    syscall += 'casa -c '+OXKAT+'/casa_get_secondary_model.py --nologger --log2term --nogui\n'


    gen.write_slurm(opfile=slurmfile,
                jobname=code+'model',
                logfile=logfile,
                syscall=syscall)


    syscall = syscall.replace(CASA_CONTAINER,XCASA_CONTAINER)
    g.write(syscall+'\n')


    job_id_secondary_model = 'SECMODEL_'+code
    syscall = job_id_secondary_model+"=`sbatch -d afterok:${"+job_id_split_cals+"} "+slurmfile+" | awk '{print $4}'`"
    f.write(syscall+'\n')


    # ------------------------------------------------------------------------------
    # 1GC using secondary model 


    slurmfile = SCRIPTS+'/slurm_1GC_'+code+'.sh'
    logfile = LOGS+'/slurm_1GC_'+code+'.log'


    syscall = 'singularity exec '+CASA_CONTAINER+' '
    syscall += 'casa -c '+OXKAT+'/casa_1GC_using_secondary_model.py --nologger --log2term --nogui\n'


    gen.write_slurm(opfile=slurmfile,
                jobname=code+'__1GC',
                logfile=logfile,
                syscall=syscall)


    syscall = syscall.replace(CASA_CONTAINER,XCASA_CONTAINER)
    g.write(syscall+'\n')


    job_id_1GC = 'FIRSTGEN_'+code
    syscall = job_id_1GC+"=`sbatch -d afterok:${"+job_id_secondary_model+"} "+slurmfile+" | awk '{print $4}'`"
    f.write(syscall+'\n')


    # ------------------------------------------------------------------------------
    # Plot calibration tables 


    slurmfile = SCRIPTS+'/slurm_gainplot_'+code+'.sh'
    logfile = LOGS+'/slurm_gainplot_'+code+'.log'


    syscall = 'singularity exec '+RAGAVI_CONTAINER+' '
    syscall += 'python3 '+TOOLS+'/plot_gaintables.py\n'


    gen.write_slurm(opfile=slurmfile,
                jobname=code+'gplot',
                logfile=logfile,
                syscall=syscall)


    syscall = syscall.replace(RAGAVI_CONTAINER,XRAGAVI_CONTAINER)
    g.write(syscall+'\n')


    job_id_gainplot = 'GAINPLOT_'+code
    syscall = job_id_gainplot+"=`sbatch -d afterok:${"+job_id_1GC+"} "+slurmfile+" | awk '{print $4}'`"
    f.write(syscall+'\n')


    # ------------------------------------------------------------------------------
    # Autoflagger on targets


    slurmfile = SCRIPTS+'/slurm_autoflag_targets_'+code+'.sh'
    logfile = LOGS+'/slurm_autoflag_targets_'+code+'.log'


    syscall = 'singularity exec '+CASA_CONTAINER+' '
    syscall += 'casa -c '+OXKAT+'/casa_autoflag_targets_corrected.py --nologger --log2term --nogui\n'


    gen.write_slurm(opfile=slurmfile,
                jobname=code+'flag2',
                logfile=logfile,
                syscall=syscall)


    syscall = syscall.replace(CASA_CONTAINER,XCASA_CONTAINER)
    g.write(syscall+'\n')


    job_id_flag2 = 'FLAG2_'+code
    syscall = job_id_flag2+"=`sbatch -d afterok:${"+job_id_1GC+"} "+slurmfile+" | awk '{print $4}'`"
    f.write(syscall+'\n')


    # ------------------------------------------------------------------------------
    # Split targets


    slurmfile = SCRIPTS+'/slurm_split_targets_'+code+'.sh'
    logfile = LOGS+'/slurm_split_targets_'+code+'.log'


    syscall = 'singularity exec '+CASA_CONTAINER+' '
    syscall += 'casa -c '+OXKAT+'/casa_split_targets.py --nologger --log2term --nogui\n'


    gen.write_slurm(opfile=slurmfile,
                jobname=code+'split',
                logfile=logfile,
                syscall=syscall)


    syscall = syscall.replace(CASA_CONTAINER,XCASA_CONTAINER)
    g.write(syscall+'\n')


    job_id_split = 'SPLIT_'+code
    syscall = job_id_split+"=`sbatch -d afterok:${"+job_id_flag2+"} "+slurmfile+" | awk '{print $4}'`"
    f.write(syscall+'\n')


    # ------------------------------------------------------------------------------


    kill = 'echo "scancel "$'+job_id_avg+'" "$'+job_id_info+'" "$'+job_id_basic+'" "$'+job_id_flag1+'" "$'+job_id_split_cals+'" "$'+job_id_secondary_model+'" "$'+job_id_1GC+'" "$'+job_id_flag2+'" "$'+job_id_split+' > '+kill_file
    f.write(kill+'\n')
    

    f.close()
    g.close()


if __name__ == "__main__":


    main()