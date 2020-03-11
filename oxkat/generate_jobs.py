#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk


import glob
import datetime
import time
import os
import os.path as o
import sys
sys.path.append(o.abspath(o.join(o.dirname(sys.modules[__name__].__file__), "..")))
import config as cfg


# ------------------------------------------------------------------------


def now():
    # stamp = time.strftime('[%H:%M:%S] ')
    stamp = time.strftime('[%Y-%m-%d %H:%M:%S]: ')
    # msg = '\033[92m'+stamp+'\033[0m' # time in green
    msg = stamp+' '
    return msg


def get_container(path,pattern):

    # Search for a file matching pattern in path

    path = path.rstrip('/')+'/'
    ll = sorted(glob.glob(path+'*'+pattern+'*img'))
    if len(ll) == 0:
        print(now()+'Failed to find container for '+pattern+' in '+path)
        sys.exit()
    elif len(ll) > 1:
        print(now()+'Warning, more than one match for '+pattern+' in '+path)
    container = ll[0]
    print(now()+'Using container: '+container)
    return container


def setup_dir(DIR):

    # Make scripts folder if it doesn't exist

    if not o.isdir(DIR):
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
                time='24:00:00',  
                partition='Main',
                ntasks='1',
                nodes='1',
                cpus='32',
                mem='236GB'):

    f = open(opfile,'w')
    f.writelines(['#!/bin/bash\n',
        '#file: '+opfile+':\n',
        '#SBATCH --job-name='+jobname+'\n',
        '#SBATCH --time='+time+'\n',
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


# def write_pbs(opfile,
#                 jobname,
#                 logfile,
#                 errfile,
#                 syscall,
#                 program='ASTR1301',
#                 walltime='24:00:00',  
#                 partition='serial',
#                 nodes='1',
#                 ppn='23',
#                 mem='120gb'):


#     make_executable(opfile)


def job_handler(syscall,
                jobname,
                infrastructure,
                dependency=None,
                slurm_time=cfg.SLURM_TIME,
                slurm_partition=cfg.SLURM_PARTITION,
                slurm_ntasks=cfg.SLURM_NTASKS,
                slurm_nodes=cfg.SLURM_NODES,
                slurm_cpus=cfg.SLURM_CPUS,
                slurm_mem=cfg.SLURM_MEM,
                pbs_program=cfg.PBS_PROGRAM,
                pbs_walltime=cfg.PBS_WALLTIME,
                pbs_queue=cfg.PBS_QUEUE,
                pbs_nodes=cfg.PBS_NODES,
                pbs_ppn=cfg.PBS_PPN,
                pbs_mem=cfg.PBS_MEM):

    if infrastructure == 'idia':

        slurm_runfile = cfg.SCRIPTS+'/slurm_'+jobname+'.sh'
        slurm_logfile = cfg.SCRIPTS+'/slurm_'+jobname+'.log'

        run_command = jobname+"=`sbatch "
        if dependency:
          run_command += "-d afterok:${"+dependency+"} "
        run_command += slurm_runfile+" | awk '{print $4}'`"

        f = open(slurm_runfile,'w')
        f.writelines(['#!/bin/bash\n',
            '#file: '+slurm_runfile+':\n',
            '#SBATCH --job-name='+jobname+'\n',
            '#SBATCH --time='+slurm_time+'\n',
            '#SBATCH --partition='+slurm_partition+'\n'
            '#SBATCH --ntasks='+slurm_ntasks+'\n',
            '#SBATCH --nodes='+slurm_nodes+'\n',
            '#SBATCH --cpus-per-task='+slurm_cpus+'\n',
            '#SBATCH --mem='+slurm_mem+'\n',
            '#SBATCH --output='+slurm_logfile+'\n',
            syscall,
            'sleep 10\n'])
        f.close()

        make_executable(slurm_runfile)

    elif infrastructure == 'chpc':

        pbs_runfile = cfg.SCRIPTS+'/pbs_'+jobname+'.sh'
        pbs_logfile = cfg.SCRIPTS+'/pbs_'+jobname+'.log'
        pbs_errfile = cfg.SCRIPTS+'/pbs_'+jobname+'.err'

        run_command = jobname+"=`qsub "
        if dependency:
          run_command += "depend=afterok:${"+dependency+"} "
        run_command += pbs_runfile+" | awk '{print $4}'`"

        f = open(pbs_runfile,'w')
        f.writelines(['#!/bin/bash\n',
            '#PBS -N '+jobname+'\n',
            '#PBS -P '+pbs_program+'\n'
            '#PBS -l walltime='+pbs_walltime+'\n',
            '#PBS -l nodes='+pbs_nodes+':ppn='+pbs_ppn+',mem='+pbs_mem+'\n',
            '#PBS -q '+pbs_queue+'\n'
            '#PBS -o '+pbs_logfile+'\n'
            '#PBS -e '+pbs_errfile+'\n'
            '\n',
            'module load chpc/singularity\n'
            'cd '+cfg.CWD+'\n',
            syscall+'\n',
            'sleep 10\n'])
        f.close()

        make_executable(pbs_runfile)


    elif infrastructure == 'node':

        run_command = syscall

    return run_command

        


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
    
    fitsmask = prefix+'-MFS-image.fits.mask.fits'

    syscall = 'bash -c "'
    syscall += 'MakeMask.py --Th='+str(thresh)+' --RestoredIm='+prefix+'-MFS-image.fits && '
    syscall += 'python '+TOOLS+'/dilate_FITS_mask.py '+fitsmask+' 3 && '
    syscall += 'fitstool.py -z 10125 '+prefix+'-MFS-image.fits.mask.fits '
    syscall += '"'
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
                          nfacets=32,
                          ndegridband=8,
                          beam='',
                          beamnband=10,
#                          beamsmooth=False,
                          dtbeammin=1,
                          FITSParAngleIncDeg=0.5,
                          nband=8,
                          mask='auto',
                          masksigma=5.5,
                          cachereset=0,
                          ddsols='',
                          initdicomodel=''):

    # Generate system call to run DDFacet

# Output key:
# Also                    =                   # Save also these images (i.e. adds to the default set of --Output-Images) #metavar:CODES #type:str
# Cubes       =                   # Also save cube versions for these images (only MmRrIi codes recognized) #metavar:CODES #type:str
# Images            = DdPAMRIikz        # Combination of letter codes indicating what images to save.
#     Uppercase for intrinsic flux scale [D]irty, [M]odel, [C]onvolved model, [R]esiduals, restored [I]mage;
#     Lowercase for apparent flux scale  [d]irty, [m]odel, [c]onvolved model, [r]esiduals, restored [i]mage;
#     Other images: [P]SF,
#     [N]orm, [n]orm facets,
#     [S] flux scale,
#     [A]lpha (spectral index),
#     [X] mixed-scale (intrinsic model, apparent residuals, i.e. Cyrils original output),
#     [o] intermediate mOdels (Model_i),
#     [e] intermediate rEsiduals (Residual_i),
#     [k] intermediate masK image,
#     [z] intermediate auto mask-related noiZe image,
#     [g] intermediate dirty images (only if [Debugging] SaveIntermediateDirtyImages is enabled).
#     Use "all" to save all.


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
    syscall += '--CF-wmax 0 '
    syscall += '--CF-Nw 100 '
    syscall += '--Output-Also nNs '
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
        syscall += '--Beam-CenterNorm=True '
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


def generate_syscall_ddfacet_hogbom(mspattern,
                          imgname,
                          ddid='D*',
                          field='F0',
                          chunkhours=1,
                          colname='CORRECTED_DATA',
                          ncpu=72,
                          maxminoriter=50000,
                          maxmajoriter=10,
                          polyfitorder=4,
                          deconvpeakfactor=0.4,
                          robust=-0.3,
                          npix=10215,
                          cell=1.1,
                          nfacets=32,
                          ndegridband=64,
                          beam='',
                          beamnband=10,
                          feedswap=1,
#                          beamsmooth=False,
                          dtbeammin=1.0,
                          FITSParAngleIncDeg=0.5,
                          nband=8,
                          mask='auto',
                          masksigma=5.5,
                          cachereset=0,
                          ddsols='',
                          initdicomodel=''):

    # Generate system call to run DDFacet with Hogbom clean

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
    syscall += '--Deconv-Mode Hogbom '
    syscall += '--Deconv-PeakFactor '+str(deconvpeakfactor)+' '
    syscall += '--Hogbom-PolyFitOrder '+str(polyfitorder)+' '
    syscall += '--Weight-Robust '+str(robust)+' '
    syscall += '--Image-NPix='+str(npix)+' '
    syscall += '--CF-wmax 0 '
    syscall += '--CF-Nw 100 '
    syscall += '--Output-Also nNs '
    syscall += '--Image-Cell '+str(cell)+' '
    syscall += '--Facets-NFacets='+str(nfacets)+' '
    syscall += '--Facets-PSFOversize=1.5 '
#    syscall += '--SSDClean-NEnlargeData 0 '
    syscall += '--Freq-NDegridBand '+str(ndegridband)+' '
    if beam == '':
        syscall += '--Beam-Model=None '
    else:
        syscall += '--Beam-Model=FITS '
        syscall += "--Beam-FITSFile=\'"+str(beam)+"\' "
        syscall += '--Beam-NBand '+str(beamnband)+' '
        syscall += '--Beam-DtBeamMin='+str(dtbeammin)+' '
        syscall += '--Beam-FITSParAngleIncDeg='+str(FITSParAngleIncDeg)+' '
        syscall += '--Beam-CenterNorm=True '
        syscall += '--Beam-FITSFeedSwap='+str(feedswap)+' '
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

