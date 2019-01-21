#!/usr/bin/env python
# ianh@astro.ox.ac.uk


import sys
from oxkat import generate_jobs as gen


def main():
    
    
    CWD = gen.CWD
    OXKAT = gen.OXKAT
    SCRIPTS = gen.SCRIPTS
    LOGS = gen.LOGS
    PARSETS = gen.PARSETS
    CASA_CONTAINER = gen.CASA_CONTAINER
    WSCLEAN_CONTAINER = gen.WSCLEAN_CONTAINER
    CUBICAL_CONTAINER = gen.CUBICAL_CONTAINER

    
    submit_file = sys.argv[1]
    prefix = sys.argv[2]


    gen.setup_scripts_dir()


    f = open(submit_file,'w')


    mslist = glob.glob(CWD+'/*.ms')

    # ---------------------------------------------------------


    jobname = prefix+'d'
    runfile = SCRIPTS+'/run_wsclean_data.sh'
    slurmfile = SCRIPTS+'/slurm_wsclean_data.sh'
    logfile = slurmfile.replace('.sh','.log')


    job_id_imgdata = 'WS_D_'+prefix


    gen.write_runfile_wsclean(mslist=mslist,imgname='img_'+prefix+'_databda',datacol='DATA',opfile=runfile,bda=True)
    gen.write_slurm(jobname,logfile,WSCLEAN_CONTAINER,runfile,slurmfile)


    syscall = job_id_imgdata+"=`sbatch"
    syscall += ' '+slurmfile+" | awk '{print $4}'`"
    f.write(syscall)


    # ---------------------------------------------------------


    cubical_dependencies = []


    for myms in mslist:


        code = gen.get_code(myms)


        runfile = SCRIPTS+'/run_predict_'+code+'.sh'
        slurmfile = SCRIPTS+'/slurm_predict_'+code+'.sh'
        logfile = slurmfile.replace('.sh','.log')
        gen.write_runfile_predict(myms,'img_'+prefix+'_databda',runfile)
        gen.write_slurm(code+'pdct',logfile,WSCLEAN_CONTAINER,runfile,slurmfile)


        job_id_predict = 'PREDICT_'+code


        syscall = job_id_predict+"=`sbatch "
        syscall += "-d afterok:${"+job_id_imgdata+"} "
        syscall += slurmfile+" | awk '{print $4}'`"
        f.write(syscall+'\n')


        jobname = code+'cbcl'
        runfile = SCRIPTS+'/run_cubical_'+code+'.sh'
        slurmfile = SCRIPTS+'/slurm_cubical_'+code+'.sh'
        logfile = slurmfile.replace('.sh','.log')
        job_id_cubical = 'CUBICAL_'+code


        cubical_dependencies.append(':$'+job_id_cubical)


        gen.write_runfile_cubical(PARSETS+'/phasecal.parset',myms,'pcal',runfile)
        gen.write_slurm(jobname,logfile,CUBICAL_CONTAINER,runfile,slurmfile)


        syscall = job_id_cubical+"=`sbatch "
        syscall += "-d afterok:${"+job_id_predict+"} "
        syscall += slurmfile+" | awk '{print $4}'`"
        f.write(syscall+'\n')


    # ---------------------------------------------------------


    jobname = prefix+'p'
    runfile = SCRIPTS+'/run_wsclean_pcal.sh'
    slurmfile = SCRIPTS+'/slurm_wsclean_pcal.sh'
    logfile = slurmfile.replace('.sh','.log')


    gen.write_runfile_wsclean(mslist=mslist,imgname='img_'+prefix+'_pcalbda',datacol='CORRECTED_DATA',opfile=runfile,bda=True)
    gen.write_slurm(jobname,logfile,WSCLEAN_CONTAINER,runfile,slurmfile)


    job_id = 'WS_P_'+prefix
    

    syscall = job_id+"=`sbatch -d afterok"
    for cubical_id in cubical_dependencies:
        syscall += cubical_id
    syscall += ' '+slurmfile+" | awk '{print $4}'`"
    f.write(syscall+'\n')


    f.close()


if __name__ == "__main__":


    main()
