#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk


import glob
import os


CWD = os.getcwd()
SLURM = CWD+'/slurm'
LOGS = CWD+'/logs'
IDIA_CONTAINER_PATH = '/users/ianh/containers/'
WSCLEAN_CONTAINER = IDIA_CONTAINER_PATH+'wsclean-1.1.5.simg'


def make_executable(infile):

    # https://stackoverflow.com/questions/12791997/how-do-you-do-a-simple-chmod-x-from-within-python

    mode = os.stat(infile).st_mode
    mode |= (mode & 0o444) >> 2
    os.chmod(infile, mode)


def write_slurm(opfile,
                jobname,
                logfile,
                syscall,
                ntasks='1',
                nodes='1',
                cpus='32',
                mem='230GB'):

    f = open(opfile,'w')
    f.writelines(['#!/bin/bash\n',
        '#file: '+opfile+':\n',
        '#SBATCH --job-name='+jobname+'\n',
        '#SBATCH --ntasks='+ntasks+'\n',
        '#SBATCH --nodes='+nodes+'\n',
        '#SBATCH --cpus-per-task='+cpus+'\n',
        '#SBATCH --mem='+mem+'\n',
        '#SBATCH --output='+logfile+'\n',
        syscall+'\n',
#        'singularity exec '+container+' '+syscall+'\n',
        'sleep 10\n'])
    f.close()

    make_executable(opfile)


def generate_syscall_wsclean(mslist,
                          imgname,
                          datacol,
                          imsize=8125,
                          cellsize='1.5asec',
                          briggs=-0.3,
                          niter=60000,
                          multiscale=False,
                          scales='0,5,15',
                          sourcelist=True,
                          bda=False,
                          nomodel=False,
                          mask='auto'):

    # Generate system call to run wsclean

    syscall = 'wsclean '
    syscall += '-log-time '
    if sourcelist:
        syscall += '-save-source-list '
    syscall += '-size '+str(imsize)+' '+str(imsize)+' '
    syscall += '-scale '+cellsize+' '
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
    syscall += '-data-column '+datacol+' '
    if mask.lower() == 'fits':
        mymask = glob.glob('*mask.fits')[0]
        syscall += '-fits-mask '+mymask+' '
    elif mask.lower() == 'none':    
        syscall += ''
    elif mask.lower() == 'auto':
        syscall += '-local-rms '
        syscall += '-auto-threshold 0.3 '
        syscall += '-auto-mask 4.5 '
    else:
        syscall += '-fits-mask '+mask+' '
    syscall += '-name '+imgname+' '
    syscall += '-channels-out 8 '
    syscall += '-fit-spectral-pol 4 '
    syscall += '-join-channels '
    syscall += '-mem 90 '

    for myms in mslist:
        syscall += myms+' '

    return syscall



def main():


	f = open('submit.sh','w')


	mslist = glob.glob('*.ms')


	for myms in mslist:


		if not os.path.isdir(SLURM):
			os.system('mkdir '+SLURM)
		if not os.path.isdir(LOGS):
			os.system('mkdir '+LOGS)


		sbid = myms.split('_')[0]
		test = CWD.split('/')[-2]
		imgname = 'img_'+sbid+'_GX339_'+test


		slurmfile = SLURM+'/slurm_'+sbid+'.sh'
		logfile = LOGS+'/'+sbid+'.log'
		code = sbid[-3:]+test[-5:]


		syscall = 'singularity exec '+WSCLEAN_CONTAINER+' '
		syscall += generate_syscall_wsclean(mslist=[myms],
			imgname=imgname,
			datacol='DATA',
			bda=True,
			niter=40000,
			mask='auto')


        write_slurm(opfile=slurmfile,
                    jobname=code,
                    logfile=logfile,
                    syscall=syscall)


        f.write('sbatch '+slurmfile+'\n')



if __name__ == "__main__":


    main()