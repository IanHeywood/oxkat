#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk


import glob
import datetime
import time
import os
import sys


# ------------------------------------------------------------------------
#
# GENERAL CONFIGURATION
#


# Folders
CWD = os.getcwd()
OXKAT = CWD+'/oxkat'
PARSETS = CWD+'/parsets'
SCRIPTS = CWD+'/scripts'
TOOLS = CWD+'/tools'
LOGS = CWD+'/logs'


# Containers for IDIA
IDIA_CONTAINER_PATH = '/users/ianh/containers/'
CASA_CONTAINER = '/idia/software/containers/casa-stable-5.6.2-2.simg'
CODEX_CONTAINER = IDIA_CONTAINER_PATH+'codex-africanus-1.1.1.simg'
CUBICAL_CONTAINER = IDIA_CONTAINER_PATH+'cubical-1.1.5.simg'
DDFACET_CONTAINER = IDIA_CONTAINER_PATH+'ddfacet-0.4.1.simg'
KILLMS_CONTAINER = IDIA_CONTAINER_PATH+'killms-2.7.0.simg'
CLUSTERCAT_CONTAINER = IDIA_CONTAINER_PATH+'ddfacet-0.5.0.simg'
SOURCEFINDER_CONTAINER = '/idia/software/containers/kern5.simg'
TRICOLOUR_CONTAINER = IDIA_CONTAINER_PATH+'tricolour-1.1.3.simg'
WSCLEAN_CONTAINER = IDIA_CONTAINER_PATH+'wsclean-1.2.4.simg'


# Containers for standalone servers
SERVER_CONTAINER_PATH = '/home/ianh/containers/'
XCASA_CONTAINER = SERVER_CONTAINER_PATH+'casa-stable-5.6.2-2.simg'
XCODEX_CONTAINER = SERVER_CONTAINER_PATH+'codex-africanus-1.1.1.simg'
XCUBICAL_CONTAINER = SERVER_CONTAINER_PATH+'cubical-1.2.3.simg'
XDDFACET_CONTAINER = SERVER_CONTAINER_PATH+'ddfacet-0.4.1.simg'
XKILLMS_CONTAINER = SERVER_CONTAINER_PATH+'killms-2.7.0.simg'
XCLUSTERCAT_CONTAINER = SERVER_CONTAINER_PATH+'ddfacet-0.5.0.simg'
XSOURCEFINDER_CONTAINER = SERVER_CONTAINER_PATH+'pybdsf-1.2.3'
XTRICOLOUR_CONTAINER = SERVER_CONTAINER_PATH+'tricolour-1.1.3.simg'
XWSCLEAN_CONTAINER = SERVER_CONTAINER_PATH+'wsclean-1.2.3.simg'


# Miscellaneous
#XCASA_EXEC = '/home/ianh/Software/casa-release-4.7.2-el7/bin/casa'
XCASA_EXEC = 'casa'
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

    code = code.replace('-','_')

    return code


def make_executable(infile):

    # https://stackoverflow.com/questions/12791997/how-do-you-do-a-simple-chmod-x-from-within-python

    mode = os.stat(infile).st_mode
    mode |= (mode & 0o444) >> 2
    os.chmod(infile, mode)


def is_odd(xx):
    if (xx % 2) == 0:
        odd = False
    else:
        odd = True
    return odd


def write_slurm(opfile,
                jobname,
                logfile,
                syscall,
                partition='Main',
                ntasks='1',
                nodes='1',
                cpus='32',
                mem='236GB'):

    f = open(opfile,'w')
    f.writelines(['#!/bin/bash\n',
        '#file: '+opfile+':\n',
        '#SBATCH --job-name='+jobname+'\n',
        '#SBATCH --partition='+partition+'\n'
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


def generate_syscall_tricolour(myms='',
                          config='',
                          datacol='DATA',
                          fields='all',
                          fs='polarisation',
                          runfile='run_tricolour.sh'):

#    syscall = 'bash -c "source '+TRICOLOUR_VENV+' ; '

    syscall = 'python '+OXKAT+'/run_tricolour.py '
    if config != '':
        syscall += '--config='+config+' '
    syscall += '--col='+datacol+' '
    syscall += '--fields='+fields+' '
    syscall += '--fs='+fs+' '
    syscall += '--runfile='+runfile+' '
    syscall += myms

#   syscall += '; deactivate"'

    return syscall


def generate_syscall_wsclean(mslist,
                          imgname,
                          datacol,
                          startchan=-1,
                          endchan=-1,
                          chanout=8,
                          imsize=10240,
                          cellsize='1.1asec',
                          briggs=-0.3,
                          niter=120000,
                          multiscale=False,
                          scales='0,3,9',
                          sourcelist=True,
                          bda=False,
                          nomodel=False,
                          mask='auto',
                          fitspectralpol=4):

    # Generate system call to run wsclean


    if is_odd(imsize):
        print('Do not use odd image sizes with wsclean')
        sys.exit()


    syscall = 'wsclean '
    syscall += '-log-time '
    if sourcelist and fitspectralpol != 0:
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
    if startchan != -1 and endchan != -1:
        syscall += '-channel-range '+str(startchan)+' '+str(endchan)+' '
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
    syscall += '-channels-out '+str(chanout)+' '
    if fitspectralpol != 0:
        syscall += '-fit-spectral-pol '+str(fitspectralpol)+' '
    syscall += '-join-channels '
    syscall += '-padding 1.3 '
    syscall += '-mem 90 '

    for myms in mslist:
        syscall += myms+' '

    return syscall


def generate_syscall_predict(msname,
                            imgbase,
                            channelsout=8,
                            imsize=10240,
                            cellsize='1.1asec',
                            predictchannels=64):

    # Generate system call to run wsclean in predict mode

    syscall = 'wsclean '
    syscall += '-log-time '
    syscall += '-predict '
    syscall += '-channelsout '+str(channelsout)+' '
    syscall += ' -size '+str(imsize)+' '+str(imsize)+' '
    syscall += '-scale '+cellsize+' '
    syscall += '-name '+imgbase+' '
    syscall += '-mem 90 '
    syscall += '-predict-channels '+str(predictchannels)+' '
    syscall += msname

    return syscall 


def generate_syscall_makemask(prefix,thresh=6.0):

    # Generate call to MakeMask.py and dilate the result

    syscall = 'MakeMask.py --Th='+str(thresh)+' --RestoredIm='+prefix+'-MFS-image.fits && '
    fitsmask = prefix+'-MFS-image.fits.mask.fits'
    syscall += 'python '+TOOLS+'/dilate_FITS_mask.py '+fitsmask+' 3 && '
    syscall += 'fitstool.py -z 10125 '+prefix+'MFS-image.fits.mask.fits \n'
#    syscall2 = 'python '+OXKAT+'/merge_FITS_masks.py '+prefix+' '+opfits+'\n'

 #   return syscall1,syscall2
    return syscall,fitsmask


def generate_syscall_ddfacet(mspattern,
                          imgname,
                          ddid='D*',
                          field='F0',
                          chunkhours=1,
                          colname='CORRECTED_DATA',
                          ncpu=32,
                          maxminoriter=120000,
                          maxmajoriter=3,
                          robust=-0.3,
                          npix=10215,
                          cell=1.1,
                          nfacets=16,
                          ndegridband=8,
                          beam='',
                          beamnband=10,
#                          beamsmooth=False,
                          dtbeammin=1,
                          FITSParAngleIncDeg=1,
                          nband=4,
                          mask='auto',
                          masksigma=5.5,
                          cachereset=0,
                          ddsols='',
                          initdicomodel=''):

    # Generate system call to run DDFacet

    syscall = 'DDF.py '
    syscall += '--Output-Name='+imgname+' '
    syscall += '--Data-MS '+mspattern+'//'+ddid+'//'+field+' '
    syscall += '--Data-ChunkHours '+str(chunkhours)+' '
    syscall += '--Deconv-PeakFactor 0.001000 '
    syscall += '--Data-ColName '+colname+' '
    syscall += '--Predict-ColName MODEL_DATA '
    syscall += '--Parallel-NCPU='+str(ncpu)+' '
    syscall += '--Output-Mode=Clean '
    syscall += '--Deconv-CycleFactor=0 '
    syscall += '--Deconv-MaxMajorIter='+str(maxmajoriter)+' '
    syscall += '--Deconv-MaxMinorIter='+str(maxminoriter)+' '
    syscall += '--Deconv-Mode SSD '
    syscall += '--Weight-Robust '+str(robust)+' '
    syscall += '--Image-NPix='+str(npix)+' '
    syscall += '--CF-wmax 8000 '
    syscall += '--CF-Nw 100 '
    syscall += '--Output-Also onNeds '
    syscall += '--Image-Cell '+str(cell)+' '
    syscall += '--Facets-NFacets='+str(nfacets)+' '
    syscall += '--Facets-PSFOversize=1.5 '
    syscall += '--SSDClean-NEnlargeData 0 '
    syscall += '--Freq-NDegridBand '+str(ndegridband)+' '
    if beam == '':
        syscall += '--Beam-Model=None '
    else:
        syscall += '--Beam-Model=FITS '
        syscall += "--Beam-FITSFile=\'"+str(beam)+"\' "
        syscall += '--Beam-NBand '+str(beamnband)+' '
        syscall += '--Beam-DtBeamMin='+str(dtbeammin)+' '
        syscall += '--Beam-FITSParAngleIncDeg='+str(FITSParAngleIncDeg)+' '
    syscall += '--Deconv-RMSFactor=3.000000 '
    syscall += '--Data-Sort 1 '
    syscall += '--Cache-Dir=. '
    syscall += '--Cache-HMP 1 '
    syscall += '--Freq-NBand='+str(nband)+' '
    if mask.lower() == 'fits':
        mymask = glob.glob('*mask.fits')[0]
        syscall += '--Mask-Auto=0 '
        syscall += '--Mask-External='+mymask+' '
    elif mask.lower() == 'auto':
        syscall += '--Mask-Auto=1 '
        syscall += '--Mask-SigTh='+str(masksigma)+' '
    else:
        syscall += '--Mask-Auto=0 '
        syscall += '--Mask-External='+mask+' '
    syscall += '--Cache-Reset '+str(cachereset)+' '
    syscall += '--Comp-GridDecorr=0.01 '
    syscall += '--Comp-DegridDecorr=0.01 '
    #syscall += '--SSDClean-MinSizeInit=10 '
    syscall += '--Facets-DiamMax .25 '
    syscall += '--Facets-DiamMin 0.05 '
    syscall += '--Misc-ConserveMemory 1 '
    syscall += '--Log-Memory 1 '
    if initdicomodel != '':
        syscall += '--Predict-InitDicoModel '+initdicomodel+' '
    if ddsols != '':
        syscall += '--DDESolutions-DDSols '+ddsols

    return syscall


def generate_syscall_killms(myms,
                        baseimg,
                        outsols,
                        nodesfile,
                        dicomodel,
                        incol='CORRECTED_DATA',
                        tchunk=0.2,
                        dt=12,
                        beam=''):

    # Generate system call to run killMS

    syscall = 'kMS.py '
    syscall+= '--MSName '+myms+' '
    syscall+= '--SolverType CohJones '
    syscall+= '--PolMode Scalar '
    syscall+= '--BaseImageName '+baseimg+' '
    syscall+= '--TChunk '+str(tchunk)+' '
    syscall+= '--dt '+str(dt)+' '
    syscall+= '--NCPU 32 '
    syscall+= '--OutSolsName '+outsols+' '
    syscall+= '--NChanSols 4 '
    syscall+= '--NIterKF 9 '
    syscall+= '--CovQ 0.05 '
    syscall+= '--UVMinMax=0.15,8500.0 '
    if beam == '':
        syscall+= '--BeamModel=None '
    else:
        syscall+= '--BeamModel=FITS '
        syscall+= '--BeamAt Facet '
        syscall+= "--FITSFile=\'"+str(beam)+"\' "
    syscall+= '--NChanBeamPerMS 95 '
    syscall+= '--FITSParAngleIncDeg 1 '
    syscall+= '--DtBeamMin 1 '
    syscall+= '--InCol '+incol+' '
    syscall+= '--OutCol '+incol+' '
    syscall+= '--Weighting Natural '
    syscall+= '--NodesFile '+nodesfile+' '
    syscall+= '--DicoModel '+dicomodel+' '
    syscall+= '--MaxFacetSize .25 '

    return syscall


def generate_syscall_pybdsf(fitsfile,
                        thresh_pix=5.0,
                        thresh_isl=3.0,
                        catalogtype='srl',
                        catalogformat='fits'):

    if catalogtype == 'srl':
        opfile = fitsfile+'.srl'
    elif catalogtype == 'gaul':
        opfile = fitsfile+'.gaul'

    if catalogformat == 'fits':
        opfile += '.fits'

    syscall = "python -c '"
    syscall += "import bdsf; "
    syscall += "img = bdsf.process_image(\""+fitsfile+"\","
    syscall += "thresh_pix="+str(thresh_pix)+","
    syscall += "thresh_isl="+str(thresh_isl)+","
    syscall += "adaptive_rms_box=True) ; "
    syscall += "img.write_catalog(outfile=\""+opfile+"\","
    syscall += "format=\""+catalogformat+"\","
    syscall += "catalog_type=\""+catalogtype+"\","
    syscall += "clobber=True,incl_empty=True)'"

    return syscall,opfile


def generate_syscall_clustercat(srl,
                        ndir=7,
                        centralradius=0.15,
                        ngen=100,
                        fluxmin=0.000001,
                        ncpu=32):

    opfile = srl.replace('.srl.fits','.srl.fits.'+str(ndir)+'.dirs.ClusterCat.npy')
    syscall = 'ClusterCat.py --SourceCat '+srl+' '
    syscall += '--NGen '+str(ngen)+' '
    syscall += '--NCluster '+str(ndir)+' '
    syscall += '--FluxMin='+str(fluxmin)+' '
    syscall += '--CentralRadius='+str(centralradius)+' '
    syscall += '--NCPU='+str(ncpu)+' '
    syscall += '--DoPlot=0 '
    syscall += '--OutClusterCat='+opfile

    return syscall, opfile


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

