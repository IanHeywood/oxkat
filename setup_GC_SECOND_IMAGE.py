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
    thresh = sys.argv[2]
    

    gen.setup_scripts_dir()


    f = open(submit_file,'w')


    mslist = glob.glob(CWD+'/*GC*.ms')


    prefix = mslist[0].split('_')[-1].split('.')[0]


    # ---------------------------------------------------------

    # Run threshold script

    jobname = prefix+'th'
    slurmfile = SCRIPTS+'/slurm_make_threshold_mask.sh'
    logfile = slurmfile.replace('.sh','.log')


    job_id_threshmask = 'THRESH_'+prefix


    inp_fits = glob.glob('*-MFS-image.fits')[0]


    runfile = 'python '+OXKAT+'/make_threshold_mask.py '+inp_fits+' '+thresh


    gen.write_slurm(jobname,logfile,WSCLEAN_CONTAINER,runfile,slurmfile)


    syscall = job_id_threshmask+"=`sbatch"
    syscall += ' '+slurmfile+" | awk '{print $4}'`"
    f.write(syscall+'\n')



    # ---------------------------------------------------------

    # Re-image with mask

    jobname = prefix+'dm'
    runfile = SCRIPTS+'/run_wsclean_datamask.sh'
    slurmfile = SCRIPTS+'/slurm_wsclean_datamask.sh'
    logfile = slurmfile.replace('.sh','.log')


    job_id_imgmask = 'WS_DM_'+prefix


    gen.write_runfile_wsclean(mslist=mslist,imgname='img_'+prefix+'_databdamask',datacol='DATA',opfile=runfile,bda=True,multiscale=True,imsize=12000,scales='0,3,9,27',niter=100000,mask='fits')
    gen.write_slurm(jobname,logfile,WSCLEAN_CONTAINER,runfile,slurmfile)


    syscall = job_id_imgmask+"=`sbatch"
    syscall += "-d afterok:${"+job_id_threshmask+"} "
    syscall += ' '+slurmfile+" | awk '{print $4}'`"
    f.write(syscall+'\n')


    # ---------------------------------------------------------

    # Predict MODEL_DATA from masked image

    runfile = SCRIPTS+'/run_predict_'+code+'.sh'
    slurmfile = SCRIPTS+'/slurm_predict_'+code+'.sh'
    logfile = slurmfile.replace('.sh','.log')
    gen.write_runfile_predict(myms,'img_'+prefix+'_databdamask',runfile)
    gen.write_slurm(code+'pdct',logfile,WSCLEAN_CONTAINER,runfile,slurmfile)


    job_id_predict = 'PREDICT_'+code


    syscall = job_id_predict+"=`sbatch "
    syscall += "-d afterok:${"+job_id_imgmask+"} "
    syscall += slurmfile+" | awk '{print $4}'`"
    f.write(syscall+'\n')


    # ---------------------------------------------------------

    # Calibrate phases

    jobname = code+'cbcl'
    runfile = SCRIPTS+'/run_cubical_'+code+'.sh'
    slurmfile = SCRIPTS+'/slurm_cubical_'+code+'.sh'
    logfile = slurmfile.replace('.sh','.log')
    job_id_cubical = 'CUBICAL_'+code


    gen.write_runfile_cubical(PARSETS+'/gc-phasecal.parset',myms,'pcal',runfile)
    gen.write_slurm(jobname,logfile,CUBICAL_CONTAINER,runfile,slurmfile)


    syscall = job_id_cubical+"=`sbatch "
    syscall += "-d afterok:${"+job_id_predict+"} "
    syscall += slurmfile+" | awk '{print $4}'`"
    f.write(syscall+'\n')


    # ---------------------------------------------------------

    # Image phase-calibrated data with mask

    jobname = prefix+'p'
    runfile = SCRIPTS+'/run_wsclean_pcal.sh'
    slurmfile = SCRIPTS+'/slurm_wsclean_pcal.sh'
    logfile = slurmfile.replace('.sh','.log')


    gen.write_runfile_wsclean(mslist=mslist,imgname='img_'+prefix+'_pcalbda',datacol='CORRECTED_DATA',opfile=runfile,bda=True,multiscale=True,imsize=12000,scales='0,3,9,27',niter=100000,mask='fits')
    gen.write_slurm(jobname,logfile,WSCLEAN_CONTAINER,runfile,slurmfile)


    job_id = 'WS_P_'+prefix
    

    syscall = job_id+"=`sbatch -d afterok"
    syscall += "-d afterok:${"+job_id_cubical+"} "
    syscall += ' '+slurmfile+" | awk '{print $4}'`"
    f.write(syscall+'\n')


    # ---------------------------------------------------------


    f.close()


    # ---------------------------------------------------------



if __name__ == "__main__":


    main()
