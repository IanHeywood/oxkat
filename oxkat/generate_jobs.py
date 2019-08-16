#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk


import glob
import datetime
import time
import os


# ------------------------------------------------------------------------
#
# GENERAL CONFIGURATION
#


# Folders
CWD = os.getcwd()
OXKAT = CWD+'/oxkat'
PARSETS = CWD+'/parsets'
SCRIPTS = CWD+'/scripts'
LOGS = CWD+'/logs'


# Containers for IDIA
#CASA_CONTAINER = '/idia/software/containers/casa-stable-5.4.1-31.simg'
CASA_CONTAINER = '/idia/software/containers/casa-stable-4.7.2.simg'
CODEX_CONTAINER = '/users/ianh/containers/codex-africanus-1.1.1.simg'
CUBICAL_CONTAINER = '/users/ianh/containers/cubical-1.1.2.simg'
DDFACET_CONTAINER = '/users/ianh/containers/ddfacet-0.4.1.simg'
KILLMS_CONTAINER = '/users/ianh/containers/killms-2.7.0.simg'
SOURCEFINDER_CONTAINER = '/idia/software/containers/SF-PY3-bionic.simg'
TRICOLOUR_CONTAINER = '/users/ianh/containers/tricolour-1.1.3.simg'
WSCLEAN_CONTAINER = '/idia/software/containers/kern5-dev.simg'


# Containers for standalone servers
SERVER_CONTAINER_PATH = '/home/ianh/containers/'
XCASA_CONTAINER = SERVER_CONTAINER_PATH+'casa-stable-5.4.1-31.simg'
XCODEX_CONTAINER = SERVER_CONTAINER_PATH+'codex-africanus-1.1.1.simg'
XCUBICAL_CONTAINER = SERVER_CONTAINER_PATH+'cubical-1.1.5.simg'
XDDFACET_CONTAINER = SERVER_CONTAINER_PATH+'ddfacet-0.4.1.simg'
XKILLMS_CONTAINER = SERVER_CONTAINER_PATH+'killms-2.7.0.simg'
XSOURCEFINDER_CONTAINER = SERVER_CONTAINER_PATH+'SF-PY3-bionic.simg'
XTRICOLOUR_CONTAINER = SERVER_CONTAINER_PATH+'tricolour-1.1.3.simg'
XWSCLEAN_CONTAINER = SERVER_CONTAINER_PATH+'wsclean-1.1.5.simg'


# Miscellaneous
XCASA_EXEC = '/home/ianh/Software/casa-release-4.7.2-el7/bin/casa'
TRICOLOUR_VENV = '/users/ianh/venv/tricolour/bin/activate'
PLOT_SCRIPTS = '/users/ianh/Software/plot_utils'


#
#
# ------------------------------------------------------------------------


def setup_dir(DIR):

    # Make scripts folder if it doesn't exist

    if not os.path.isdir(DIR):
        os.mkdir(DIR)


def timenow():

    # Return a date and time string suitable for being part of a filename

    now = str(datetime.datetime.now()).replace(' ','-').replace(':','-').split('.')[0]
    return now


def get_code(myms):

    # Last three digits of the data set ID

    myms = myms.split('/')[-1]

    code = myms.split('_')[0][-3:]

    return code


def make_executable(infile):

    # https://stackoverflow.com/questions/12791997/how-do-you-do-a-simple-chmod-x-from-within-python

    mode = os.stat(infile).st_mode
    mode |= (mode & 0o444) >> 2
    os.chmod(infile, mode)


# ------------------------------------------------------------------------


def write_slurm(opfile,
                jobname,
                logfile,
                container,
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
        'singularity exec '+container+' '+syscall+'\n',
        'sleep 10\n'])
    f.close()

    make_executable(opfile)


def generate_syscall_cubical(parset,myms,prefix):

    now = timenow()
    outname = 'cube_'+prefix+'_'+myms.split('/')[-1]+'_'+now

    # Debugging stuff
    syscall = 'bash -c "/sbin/sysctl vm.max_map_count ; '
    syscall += 'df -h /dev/shm ; '

    syscall += 'gocubical '+parset+' '
    syscall += '--data-ms='+myms+' '
    syscall += '--out-name='+outname

    # Move output to logs...
    syscall += ' ; mv '+outname+'* '+LOGS+'"'

    return syscall


def generate_syscall_tricolour(myms='',datacol='DATA',fields='all'):


#    syscall = 'bash -c "source '+TRICOLOUR_VENV+' ; '

    syscall = 'python '+OXKAT+'/run_tricolour.py '
    syscall += '--col='+datacol+' '
    syscall += '--fields='+fields+' '
    syscall += myms

#   syscall += '; deactivate"'

    return syscall


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
        syscall += '-auto-mask 5.0 '
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


def generate_syscall_predict(msname,imgbase):

    # Generate system call to run wsclean in predict mode

    syscall = 'wsclean '
    syscall += '-log-time '
    syscall += '-predict '
    syscall += '-channelsout 8 '
    syscall += ' -size 8125 8125 '
    syscall += '-scale 1.5asec '
    syscall += '-name '+imgbase+' '
    syscall += '-mem 90 '
    syscall += '-predict-channels 64 '
    syscall += msname

    return syscall 


def generate_syscall_makemask(opfits,prefix='',thresh=6.0):

    # Generate call to MakeMask.py and an optional call to replace_FITS_data.py to make the
    # resulting header consistent with wsclean

    syscall = 'bash -c " '
    syscall += 'MakeMask.py --Th='+str(thresh)+' --RestoredIm='+prefix+'-MFS-image.fits '
    syscall += '; python '+OXKAT+'/merge_FITS_masks.py '+prefix+' '+opfits+' "'

    return syscall


def generate_syscall_crystalball(myms,
                        model,
                        outcol,
                        region,
                        num_workers=32,
                        mem_fraction=90):

    syscall = 'crystalball '
    syscall += '-sm '+model+' '
    syscall += '-o '+outcol+' '
    syscall += '-w '+region+' '
    syscall += '--spectra '
    syscall += '-j '+num_workers+' '
    syscall += '-mf '+mem_fraction+' '
    syscall += myms

    return syscall




# ------------------------------------------------------------------------

