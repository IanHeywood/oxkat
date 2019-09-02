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
    LOGS = gen.LOGS
    CASA_CONTAINER = gen.CASA_CONTAINER
    CUBICAL_CONTAINER = gen.CUBICAL_CONTAINER
 

    submit_file = 'submit_1GC_jobs.sh'
    kill_file = 'kill_1GC_jobs.sh'


    gen.setup_dir(SCRIPTS)
    gen.setup_dir(LOGS)


    f = open(submit_file,'w')


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
                jobname=code+'avSEC',
                logfile=logfile,
                syscall=syscall)


    job_id_avg = 'AVG_'+code
    syscall = job_id_avg+"=`sbatch "+slurmfile+" | awk '{print $4}'`"
    f.write(syscall+'\n')



    # ------------------------------------------------------------------------------
    # Run setup script


    slurmfile = SCRIPTS+'/slurm_setup_'+code+'.sh'
    logfile = LOGS+'/slurm_setup_'+code+'.log'


    syscall = 'singularity exec '+CUBICAL_CONTAINER+' '
    syscall += 'python '+OXKAT+'/00_setup.py '+myms+'\n'


    gen.write_slurm(opfile=slurmfile,
                jobname=code+'stSEC',
                logfile=logfile,
                syscall=syscall)


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
                jobname=code+'baSEC',
                logfile=logfile,
                syscall=syscall)


    job_id_basic = 'BASIC_'+code
    syscall = job_id_basic+"=`sbatch -d afterok:${"+job_id_info+"} "+slurmfile+" | awk '{print $4}'`"
    f.write(syscall+'\n')


    # ------------------------------------------------------------------------------
    # Autoflagger on calibrators (DATA)


    slurmfile = SCRIPTS+'/slurm_autoflag_cals_data_'+code+'.sh'
    logfile = LOGS+'/slurm_autoflag_cals_data_'+code+'.log'


    syscall = 'singularity exec '+CASA_CONTAINER+' '
    syscall += 'casa -c '+OXKAT+'/casa_tfcrop_cals_data.py --nologger --log2term --nogui\n'


    gen.write_slurm(opfile=slurmfile,
                jobname=code+'f1SEC',
                logfile=logfile,
                syscall=syscall)


    job_id_flag1 = 'FLAG1_'+code
    syscall = job_id_flag1+"=`sbatch -d afterok:${"+job_id_basic+"} "+slurmfile+" | awk '{print $4}'`"
    f.write(syscall+'\n')



    # ------------------------------------------------------------------------------
    # Reference calibration cals only


    slurmfile = SCRIPTS+'/slurm_refcal-cals_'+code+'.sh'
    logfile = LOGS+'/slurm_refcal-cals_'+code+'.log'


    syscall = 'singularity exec '+CASA_CONTAINER+' '
    syscall += 'casa -c '+OXKAT+'/casa_reference_cal_calzone.py --nologger --log2term --nogui\n'


    gen.write_slurm(opfile=slurmfile,
                jobname=code+'r1SEC',
                logfile=logfile,
                syscall=syscall)


    job_id_refcal1 = 'REFCAL1_'+code
    syscall = job_id_refcal1+"=`sbatch -d afterok:${"+job_id_flag1+"} "+slurmfile+" | awk '{print $4}'`"
    f.write(syscall+'\n')


    # ------------------------------------------------------------------------------
    # Autoflagger on calibrators (CORRECTED_DATA)


    slurmfile = SCRIPTS+'/slurm_autoflag_cals_corr_'+code+'.sh'
    logfile = LOGS+'/slurm_autoflag_cals_corr_'+code+'.log'


    syscall = 'singularity exec '+CASA_CONTAINER+' '
    syscall += 'casa -c '+OXKAT+'/casa_tfcrop_cals_corrected.py --nologger --log2term --nogui\n'


    gen.write_slurm(opfile=slurmfile,
                jobname=code+'f2SEC',
                logfile=logfile,
                syscall=syscall)


    job_id_flag2 = 'FLAG2_'+code
    syscall = job_id_flag2+"=`sbatch -d afterok:${"+job_id_refcal1+"} "+slurmfile+" | awk '{print $4}'`"
    f.write(syscall+'\n')


    # ------------------------------------------------------------------------------
    # Full reference calibration 


    slurmfile = SCRIPTS+'/slurm_refcal-all_'+code+'.sh'
    logfile = LOGS+'/slurm_refcal-all_'+code+'.log'


    syscall = 'singularity exec '+CASA_CONTAINER+' '
    syscall += 'casa -c '+OXKAT+'/casa_reference_cal_full_no_secondary.py --nologger --log2term --nogui\n'


    gen.write_slurm(opfile=slurmfile,
                jobname=code+'r2SEC',
                logfile=logfile,
                syscall=syscall)


    job_id_refcal2 = 'REFCAL2_'+code
    syscall = job_id_refcal2+"=`sbatch -d afterok:${"+job_id_flag2+"} "+slurmfile+" | awk '{print $4}'`"
    f.write(syscall+'\n')


    # ------------------------------------------------------------------------------
    # Autoflagger on targets


    slurmfile = SCRIPTS+'/slurm_autoflag_targets_'+code+'.sh'
    logfile = LOGS+'/slurm_autoflag_targets_'+code+'.log'


    syscall = 'singularity exec '+CASA_CONTAINER+' '
    syscall += 'casa -c '+OXKAT+'/casa_tfcrop_targets_corrected.py --nologger --log2term --nogui\n'


    gen.write_slurm(opfile=slurmfile,
                jobname=code+'f3SEC',
                logfile=logfile,
                syscall=syscall)


    job_id_flag3 = 'FLAG3_'+code
    syscall = job_id_flag3+"=`sbatch -d afterok:${"+job_id_refcal2+"} "+slurmfile+" | awk '{print $4}'`"
    f.write(syscall+'\n')


    # ------------------------------------------------------------------------------
    # Split targets


    slurmfile = SCRIPTS+'/slurm_split_targets_'+code+'.sh'
    logfile = LOGS+'/slurm_split_targets_'+code+'.log'


    syscall = 'singularity exec '+CASA_CONTAINER+' '
    syscall += 'casa -c '+OXKAT+'/casa_split_targets.py --nologger --log2term --nogui\n'


    gen.write_slurm(opfile=slurmfile,
                jobname=code+'spSEC',
                logfile=logfile,
                syscall=syscall)


    job_id_split = 'SPLIT_'+code
    syscall = job_id_split+"=`sbatch -d afterok:${"+job_id_flag3+"} "+slurmfile+" | awk '{print $4}'`"
    f.write(syscall+'\n')


    # ------------------------------------------------------------------------------

    kill = 'echo "scancel "$'+job_id_avg+'" "$'+job_id_info+'" "$'+job_id_basic+'" "$'+job_id_flag1+'" "$'+job_id_refcal1+'" "$'+job_id_flag2+'" "$'+job_id_refcal2+'" "$'+job_id_flag3+'" "$'+job_id_split+' > '+kill_file

    f.write(kill+'\n')

    f.close()


if __name__ == "__main__":


    main()