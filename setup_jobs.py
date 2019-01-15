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
CASA_CONTAINER = '/users/ianh/containers/casa-5.1.1-wsclean.img'
WSCLEAN_CONTAINER = '/users/ianh/containers/casa-5.1.1-wsclean.img'
CUBICAL_CONTAINER = '/data/exp_soft/containers/kern4-2018-11-28.simg'



if not os.path.isdir(SCRIPTS):
    os.mkdir(SCRIPTS)



# ------------------------------------------------------------------------


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
        syscall += '-multiscale-scales 0,5,15 '
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


# globdir = CWD.split('/')
# globdir = globdir[:-1]
# globdir = "/".join(globdir)
# mslist = glob.glob(globdir+'/1*/*/*COSMOS.ms')


mslist = glob.glob(CWD+'/*wtspec.ms')

# AVERAGE UP FRONT, FLAG, REFCAL

code = get_code(myms)

cmd = 'casa -c '+OXKAT+'/01_casa_average_to_1k.py --nologger --log2term --nogui'
slurmfile = SCRIPTS+'/slurm_avg_'+code+'.sh'
logfile = slurmfile.replace('.sh','.log')
job_id_avg = 'AVG_'+code
write_slurm(code+'avrg',logfile,CASA_CONTAINER,cmd,slurmfile)

syscall = job_id_avg+"=`sbatch "
syscall += slurmfile+" | awk '{print $4}'`"
print syscall 

cmd = 'python '+OXKAT+'/00_setup.py '+myms
slurmfile = SCRIPTS+'/slurm_info_'+code+'.sh'
logfile = slurmfile.replace('.sh','.log')
job_id_info = 'INFO_'+code
write_slurm(code+'info',logfile,CUBICAL_CONTAINER,cmd,slurmfile)

syscall = job_id_info+"=`sbatch "
syscall += "-d afterok:${"+job_id_avg+"} "
syscall += slurmfile+" | awk '{print $4}'`"
print syscall 

cmd = 'casa -c '+OXKAT+'/01_casa_hardmask_and_flag.py --nologger --log2term --nogui'
slurmfile = SCRIPTS+'/slurm_flag_'+code+'.sh'
logfile = slurmfile.replace('.sh','.log')
job_id_flag = 'FLAG_'+code
write_slurm(code+'flag',logfile,CASA_CONTAINER,cmd,slurmfile)

syscall = job_id_flag+"=`sbatch "
syscall += "-d afterok:${"+job_id_info+"} "
syscall += slurmfile+" | awk '{print $4}'`"
print syscall 

cmd = 'casa -c '+OXKAT+'/02_casa_refcal.py --nologger --log2term --nogui'
slurmfile = SCRIPTS+'/slurm_refcal_'+code+'.sh'
logfile = slurmfile.replace('.sh','.log')
job_id_refcal = 'REFCAL_'+code
write_slurm(code+'rcal',logfile,CASA_CONTAINER,cmd,slurmfile)

syscall = job_id_refcal+"=`sbatch "
syscall += "-d afterok:${"+job_id_flag+"} "
syscall += slurmfile+" | awk '{print $4}'`"
print syscall 

# INFO, FLAG, REFCAL 


# for myms in mslist:

#     code = get_code(myms)
#     cmd = 'python 00_setup.py '+myms
#     slurmfile = SCRIPTS+'/slurm_info_'+code+'.sh'
#     logfile = slurmfile.replace('.sh','.log')
#     job_id_info = 'INFO_'+code
#     write_slurm(code+'info',logfile,CUBICAL_CONTAINER,cmd,slurmfile)

#     syscall = job_id_info+"=`sbatch "
#     syscall += slurmfile+" | awk '{print $4}'`"
#     print syscall 

#     cmd = 'casa -c 01_casa_hardmask_and_flag.py --nologger --log2term --nogui'
#     slurmfile = SCRIPTS+'/slurm_flag_'+code+'.sh'
#     logfile = slurmfile.replace('.sh','.log')
#     job_id_flag = 'FLAG_'+code
#     write_slurm(code+'flag',logfile,CASA_CONTAINER,cmd,slurmfile)

#     syscall = job_id_flag+"=`sbatch "
#     syscall += "-d afterok:${"+job_id_info+"} "
#     syscall += slurmfile+" | awk '{print $4}'`"
#     print syscall 

#     cmd = 'casa -c 02_casa_refcal.py --nologger --log2term --nogui'
#     slurmfile = SCRIPTS+'/slurm_refcal_'+code+'.sh'
#     logfile = slurmfile.replace('.sh','.log')
#     job_id_refcal = 'REFCAL_'+code
#     write_slurm(code+'rcal',logfile,CASA_CONTAINER,cmd,slurmfile)

#     syscall = job_id_refcal+"=`sbatch "
#     syscall += "-d afterok:${"+job_id_flag+"} "
#     syscall += slurmfile+" | awk '{print $4}'`"
#     print syscall 

# ------------------------------------------------------------------------

# IMAGE DATA WITH BDA, PARALLEL PREDICT, PARALLEL SELFCAL, IMAGE CORR WITH BDA

# mslist = glob.glob(CWD+'/*.ms')

# jobname = '059_252d'
# runfile = SCRIPTS+'/run_wsclean_data.sh'
# slurmfile = SCRIPTS+'/slurm_wsclean_data.sh'
# logfile = slurmfile.replace('.sh','.log')

# job_id_imgdata = 'WS_D_059_252'

# write_runfile_wsclean(mslist=mslist,imgname='img_COSMOS_pcalbda',datacol='DATA',opfile=runfile,bda=True)
# write_slurm(jobname,logfile,WSCLEAN_CONTAINER,runfile,slurmfile)

# syscall = job_id_imgdata+"=`sbatch"
# syscall += ' '+slurmfile+" | awk '{print $4}'`"
# print syscall


# # PREDICT AND CUBICAL LOOP for multiple MS

# cubical_dependencies = []

# for myms in mslist:
#     code = get_code(myms)

#     runfile = SCRIPTS+'/run_predict_'+code+'.sh'
#     slurmfile = SCRIPTS+'/slurm_predict_'+code+'.sh'
#     logfile = slurmfile.replace('.sh','.log')
#     write_runfile_predict(myms,'img_COSMOS_databda',runfile)
#     write_slurm(code+'pdct',logfile,WSCLEAN_CONTAINER,runfile,slurmfile)

#     job_id_predict = 'PREDICT_'+code

#     syscall = job_id_predict+"=`sbatch "
#     syscall += "-d afterok:${"+job_id_imgdata+"} "
#     syscall += slurmfile+" | awk '{print $4}'`"
#     print syscall

#     jobname = code+'cbcl'
#     runfile = SCRIPTS+'/run_cubical_'+code+'.sh'
#     slurmfile = SCRIPTS+'/slurm_cubical_'+code+'.sh'
#     logfile = slurmfile.replace('.sh','.log')
#     job_id_cubical = 'CUBICAL_'+code

#     cubical_dependencies.append(':$'+job_id_cubical)

#     write_runfile_cubical('phasecal.parset',myms,'pcal',runfile)
#     write_slurm(jobname,logfile,CUBICAL_CONTAINER,runfile,slurmfile)

#     syscall = job_id_cubical+"=`sbatch "
#     syscall += "-d afterok:${"+job_id_predict+"} "
#     syscall += slurmfile+" | awk '{print $4}'`"
#     print syscall

# jobname = '059_252p'
# runfile = SCRIPTS+'/run_wsclean_pcal.sh'
# slurmfile = SCRIPTS+'/slurm_wsclean_pcal.sh'
# logfile = slurmfile.replace('.sh','.log')

# write_runfile_wsclean(mslist=mslist,imgname='img_XMM12_pcalbda',datacol='CORRECTED_DATA',opfile=runfile,bda=True)
# write_slurm(jobname,logfile,WSCLEAN_CONTAINER,runfile,slurmfile)

# job_id = 'WS_P_059_252'

# syscall = job_id+"=`sbatch -d afterok"
# for cubical_id in cubical_dependencies:
#     syscall += cubical_id
# syscall += ' '+slurmfile+" | awk '{print $4}'`"
# print syscall


# ------------------------------------------------------------------------

# WSCLEAN LOOP for multiple MS

# for myms in mslist:
#   code = get_code(myms)
#   imgname = 'img_'+code+'_data'
#   runfile = SCRIPTS+'/run_wsclean_'+code+'.sh'
#   slurmfile = SCRIPTS+'/slurm_wsclean_'+code+'.sh'
#   write_runfile_wsclean([myms],imgname,'DATA',runfile,multiscale=False,bda=False,mask=False)
#   write_slurm(code+'wscl',WSCLEAN_CONTAINER,runfile,slurmfile)
#   print 'sbatch '+slurmfile

# ------------------------------------------------------------------------

# Remove cubical jobs function and put into main?

#cubical_jobs(mslist,'test.sh','WSCLEAN_ID')
