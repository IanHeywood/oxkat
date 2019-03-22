#!/usr/bin/env python
# ianh@astro.ox.ac.uk


import glob
import datetime
import time
import os



CWD = os.getcwd()
OXKAT = CWD+'/oxkat'
SCRIPTS = CWD+'/scripts'
LOGS = CWD+'/logs'
PARSETS = CWD+'/oxkat'
#CASA_CONTAINER = '/users/ianh/containers/casa-5.1.1-wsclean.img'
CASA_CONTAINER = '/data/exp_soft/containers/casa-stable-5.4.1-31.simg'
WSCLEAN_CONTAINER = '/users/ianh/containers/casa-5.1.1-wsclean.img'
CUBICAL_CONTAINER = '/data/exp_soft/containers/kern4-2018-11-28.simg'



# ------------------------------------------------------------------------

def setup_scripts_dir():

    # Make scripts folder if it doesn't exist

    if not os.path.isdir(SCRIPTS):
        os.mkdir(SCRIPTS)



def timenow():

    # Return a date and time string suitable for being part of a filename

    now = str(datetime.datetime.now()).replace(' ','-').replace(':','-').split('.')[0]
    return now


def get_code(myms):

    # Last three digits of the data set ID, plus the sub-band

    myms = myms.split('/')[-1]

    if 'HI' in myms:
        band = 'H'
    elif 'LO' in myms:
        band = 'L'
    else:
        band = 'F'

    code = myms.split('_')[0][-3:]

    return code+band


def make_executable(infile):

    # https://stackoverflow.com/questions/12791997/how-do-you-do-a-simple-chmod-x-from-within-python

    mode = os.stat(infile).st_mode
    mode |= (mode & 0o444) >> 2
    os.chmod(infile, mode)


# ------------------------------------------------------------------------


def write_runfile_cubical(parset,myms,prefix,opfile):

    # Generate shell script to run CubiCal, to be invoked by slurm script

    now = timenow()
    outname = 'cube_'+prefix+'_'+myms.split('/')[-1]+'_'+now

    syscall = 'gocubical '+parset+' '
    syscall += '--data-ms='+myms+' '
    syscall += '--out-name='+outname

    f = open(opfile,'w')
    f.writelines(['#!/bin/bash\n',
        'source ~/venv/meerkat/bin/activate\n',
        'export PATH=/users/ianh/.local/bin:$PATH\n',
        syscall+'\n'])
    f.close()

    make_executable(opfile)


def write_slurm(jobname,logfile,container,runfile,opfile):

    # Generate slurm script for running CubiCal

    f = open(opfile,'w')
    f.writelines(['#!/bin/bash\n',
        '#file: '+opfile+':\n',
        '#SBATCH --job-name='+jobname+'\n',
        '#SBATCH --ntasks=1\n',
        '#SBATCH --nodes=1\n',
        '#SBATCH --cpus-per-task=32\n',
        '#SBATCH --mem=230GB\n',
        '#SBATCH --output='+logfile+'\n',
        'singularity exec '+container+' '+runfile+'\n',
        'sleep 10\n'])
    f.close()

    make_executable(opfile)

def cubical_jobs(mslist,opfile,dependency=None):

    # CubiCal job submission commands with depdencies

    for i in range(0,len(mslist)):

        myms = mslist[i]
        jobname = get_code(myms)+'cal'
        runfile = 'run_cubical_'+str(i)+'.sh'
        slurmfile = 'slurm_cubical_'+str(i)+'.sh'
        job_id = 'CUBICAL_ID_'+str(i)
        
        write_runfile_cubical('test.parset',myms,'pcal',runfile)
        write_slurm(jobname,'mycontainer.img',runfile,slurmfile)

        syscall = job_id+"=`sbatch "
        if dependency:
            syscall += "-d afterok:${"+dependency+"} "
        syscall += slurmfile+" | awk '{print $4}'`"
        print syscall 


def write_runfile_wsclean(mslist,
                          imgname,datacol,opfile,
                          briggs=-0.3,niter=100000,multiscale=False,
                          scales='0,5,15',
                          bda=False,nomodel=False,mask=False):

    # Generate shell script to run wsclean, to be invoked by slurm script

    syscall = 'wsclean '
    syscall += '-log-time '
    syscall += '-size 8192 8192 '
    syscall += '-scale 1.5asec '
    if bda:
        syscall += '-baseline-averaging 24 '
        syscall += '-no-update-model-required '
    elif not bda and nomodel:
        syscall += '-no-update-model-required '
    if multiscale:
        syscall += '-multiscale '
        syscall += '-multiscale-scales '+scales+' '
    syscall += '-niter '+str(niter)+' '
    syscall += '-gain 0.1 '
    syscall += '-mgain 0.85 '
    syscall += '-weight briggs '+str(briggs)+' '
    syscall += '-datacolumn '+datacol+' '
    if mask:
        syscall += '-fitsmask '+mask+' '
    else:
        syscall += '-local-rms '
        syscall += '-auto-threshold 0.3 '
        syscall += '-auto-mask 5.5 '
    syscall += '-name '+imgname+' '
    syscall += '-channelsout 8 '
    syscall += '-fit-spectral-pol 4 '
    syscall += '-joinchannels '
    syscall += '-mem 90 '

    for myms in mslist:
        syscall += myms+' '

    f = open(opfile,'w')
    f.writelines(['#!/bin/bash\n',
        syscall+'\n'])
    f.close()

    make_executable(opfile)


def write_runfile_predict(msname,imgbase,opfile):
    syscall = 'wsclean -log-time -predict -channelsout 8 -size 8192 8192 '
    syscall+= '-scale 1.5asec -name '+imgbase+' -mem 90 '
    syscall+= '-no-reorder ' # TEST THE SPEED OF THIS
    syscall+= '-predict-channels 64 '+msname

    f = open(opfile,'w')
    f.writelines(['#!/bin/bash\n',
        syscall+'\n'])
    f.close()

    make_executable(opfile)


    f = open(opfile,'w')
    f.writelines(['#!/bin/bash\n',
        syscall+'\n'])
    f.close()

    make_executable(opfile)

# ------------------------------------------------------------------------

