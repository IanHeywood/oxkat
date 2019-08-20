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
    TRICOLOUR_CONTAINER = gen.TRICOLOUR_CONTAINER
 

    submit_file = 'submit_1GC_jobs.sh'
    kill_file = 'kill_1GC_jobs.sh'


    gen.setup_dir(SCRIPTS)
    gen.setup_dir(LOGS)


    f = open(submit_file,'w')


    myms = glob.glob('*pol.ms')[0]
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
                jobname=code+'setup',
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
                jobname=code+'basic',
                logfile=logfile,
                syscall=syscall)


    job_id_basic = 'BASIC_'+code
    syscall = job_id_basic+"=`sbatch -d afterok:${"+job_id_info+"} "+slurmfile+" | awk '{print $4}'`"
    f.write(syscall+'\n')


    # ------------------------------------------------------------------------------
    # Autoflagger on calibrators 1


    slurmfile = SCRIPTS+'/slurm_tricolour_cals_1_'+code+'.sh'
    logfile = LOGS+'/slurm_tricolour_cals_1_'+code+'.log'

    runfile = SCRIPTS+'/run_tricolour_1.sh'

    syscall = 'singularity exec '+CUBICAL_CONTAINER+' '
    syscall += gen.generate_syscall_tricolour(myms=myms,datacol='DATA',fields='cals',fs='polarisation',runfile=runfile)+'\n'
    syscall += 'singularity exec '+TRICOLOUR_CONTAINER+' '+runfile+'\n'

    gen.write_slurm(opfile=slurmfile,
                jobname=code+'tric1',
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
                jobname=code+'rcal1',
                logfile=logfile,
                syscall=syscall)


    job_id_refcal1 = 'REFCAL1_'+code
    syscall = job_id_refcal1+"=`sbatch -d afterok:${"+job_id_flag1+"} "+slurmfile+" | awk '{print $4}'`"
    f.write(syscall+'\n')


    # ------------------------------------------------------------------------------
    # Autoflagger on calibrators 2


    slurmfile = SCRIPTS+'/slurm_tricolour_cals_2_'+code+'.sh'
    logfile = LOGS+'/slurm_tricolour_cals_2_'+code+'.log'

    runfile = SCRIPTS+'/run_tricolour_2.sh'

    syscall = 'singularity exec '+CUBICAL_CONTAINER+' '
    syscall += gen.generate_syscall_tricolour(myms=myms,datacol='DATA',fields='cals',fs='polarisation',runfile=runfile)+'\n'
    syscall += 'singularity exec '+TRICOLOUR_CONTAINER+' '+runfile+'\n'

    gen.write_slurm(opfile=slurmfile,
                jobname=code+'tric2',
                logfile=logfile,
                syscall=syscall)


    job_id_flag2 = 'FLAG2_'+code
    syscall = job_id_flag2+"=`sbatch -d afterok:${"+job_id_refcal1+"} "+slurmfile+" | awk '{print $4}'`"
    f.write(syscall+'\n')


    # ------------------------------------------------------------------------------
    # Full reference calibration 


    slurmfile = SCRIPTS+'/slurm_refcal-all_'+code+'.sh'
    logfile = LOGS+'/slurm_refcal-all_'+code+'.log'


    gen.write_slurm(opfile=slurmfile,
                jobname=code+'rcal2',
                logfile=logfile,
                syscall='singularity exec '+CASA_CONTAINER+' casa -c '+OXKAT+'/casa_reference_cal_full.py --nologger --log2term --nogui')


    job_id_refcal2 = 'REFCAL2_'+code
    syscall = job_id_refcal2+"=`sbatch -d afterok:${"+job_id_flag2+"} "+slurmfile+" | awk '{print $4}'`"
    f.write(syscall+'\n')


    # ------------------------------------------------------------------------------
    # Autoflagger on targets


    slurmfile = SCRIPTS+'/slurm_tricolour_targets_'+code+'.sh'
    logfile = LOGS+'/slurm_tricolour_targets_'+code+'.log'

    runfile = SCRIPTS+'/run_tricolour_3.sh'

    syscall = 'singularity exec '+CUBICAL_CONTAINER+' '
    syscall += gen.generate_syscall_tricolour(myms=myms,datacol='CORRECTED_DATA',fields='targets',fs='polarisation',runfile=runfile)+'\n'
    syscall += 'singularity exec '+TRICOLOUR_CONTAINER+' '+runfile+'\n'

    gen.write_slurm(opfile=slurmfile,
                jobname=code+'tric3',
                logfile=logfile,
                syscall=syscall)


    job_id_flag3 = 'FLAG_'+code
    syscall = job_id_flag3+"=`sbatch -d afterok:${"+job_id_refcal2+"} "+slurmfile+" | awk '{print $4}'`"
    f.write(syscall+'\n')


    # ------------------------------------------------------------------------------
    # Split targets


    slurmfile = SCRIPTS+'/slurm_split_targets_'+code+'.sh'
    logfile = LOGS+'/slurm_split_targets_'+code+'.log'


    gen.write_slurm(opfile=slurmfile,
                jobname=code+'split',
                logfile=logfile,
                syscall='singularity exec '+CASA_CONTAINER+' casa -c '+OXKAT+'/casa_split_targets.py --nologger --log2term --nogui')


    job_id_split = 'SPLIT_'+code
    syscall = job_id_split+"=`sbatch -d afterok:${"+job_id_flag3+"} "+slurmfile+" | awk '{print $4}'`"
    f.write(syscall+'\n')


    # ------------------------------------------------------------------------------

    kill = 'echo "scancel "$'+job_id_avg+'" "$'+job_id_info+'" "$'+job_id_basic+'" "$'+job_id_refcal1+'" "$'+job_id_flag1+'" "$'+job_id_refcal2+'" "$'+job_id_flag2+'" "$'+job_id_split+' > '+kill_file

    f.write(kill+'\n')

    f.close()


if __name__ == "__main__":


    main()