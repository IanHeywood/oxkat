#!/usr/bin/env python
# ianh@astro.ox.ac.uk


import sys
import glob
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
    

    gen.setup_scripts_dir()


    f = open(submit_file,'w')


    mslist = glob.glob(CWD+'/*GC*.ms')


    prefix = mslist[0].split('_')[-1].split('.')[0]


    # ---------------------------------------------------------


    jobname = prefix+'d'
    runfile = SCRIPTS+'/run_wsclean_data.sh'
    slurmfile = SCRIPTS+'/slurm_wsclean_data.sh'
    logfile = slurmfile.replace('.sh','.log')


    job_id_imgdata = 'WS_D_'+prefix


    gen.write_runfile_wsclean(mslist=mslist,imgname='img_'+prefix+'_databda',datacol='DATA',opfile=runfile,bda=True,multiscale=True,imsize=12000,scales='0,3,9,27',niter=100000)
    gen.write_slurm(jobname,logfile,WSCLEAN_CONTAINER,runfile,slurmfile)


    syscall = job_id_imgdata+"=`sbatch"
    syscall += ' '+slurmfile+" | awk '{print $4}'`"
    f.write(syscall+'\n')



    f.close()


if __name__ == "__main__":


    main()
