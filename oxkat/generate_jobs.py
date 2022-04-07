#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk


import glob
import datetime
import time
import os
import os.path as o
import sys
sys.path.append(o.abspath(o.join(o.dirname(sys.modules[__name__].__file__), "..")))
from oxkat import config as cfg


# ------------------------------------------------------------------------

def preamble():
    print('---------------------+----------------------------------------------------------')
    print('                     |')
    print('                     | v0.3')  
    print('    o  x  k  a  t    | Please file an issue for bugs / help:')
    print('                     | https://github.com/IanHeywood/oxkat')
    print('                     |')
    print('---------------------+----------------------------------------------------------')
    print(now()+'Observing band is '+cfg.BAND)
    # if cfg.BAND[0].upper() == 'L':
    #     print(now()+'Configured for L-band processing')
    # elif cfg.BAND[0].upper() == 'U':
    #     print(now()+'Configured for UHF processing')


def now():
    # stamp = time.strftime('[%H:%M:%S] ')
    stamp = time.strftime(' %Y-%m-%d %H:%M:%S | ')
    # msg = '\033[92m'+stamp+'\033[0m' # time in green
    msg = stamp
    return msg


def col(txt=''):
    colstr = ' '+txt.ljust(20)+'| '
    return colstr


def print_spacer():
    print('---------------------+----------------------------------------------------------')


def set_infrastructure(args):

    if len(args) == 1:
        print(col()+'Please specify infrastructure (idia / chpc / hippo / node)')
        print_spacer()
        sys.exit()

    if args[1].lower() not in ['idia','chpc','hippo','node']:
        print(col()+'Please specify infrastructure (idia / chpc / hippo / node)')
        print_spacer()
        sys.exit()

    if args[1].lower() == 'idia':
        infrastructure = 'idia'
        CONTAINER_PATH = cfg.IDIA_CONTAINER_PATH
    elif args[1].lower() == 'chpc':
        infrastructure = 'chpc'
        CONTAINER_PATH = cfg.CHPC_CONTAINER_PATH
    elif args[1].lower() == 'node':
        infrastructure = 'node'
        CONTAINER_PATH = cfg.NODE_CONTAINER_PATH
    elif args[1].lower() == 'hippo':
        infrastructure = 'hippo'
        CONTAINER_PATH = None

        
    print(col('Infrastructure')+infrastructure.upper())
    if cfg.USE_SINGULARITY:
        print(col('Singularity')+'Enabled')
        print(col('Container path')+str(CONTAINER_PATH))
    else:
        print(col('Singularity')+'Not enabled')


    return infrastructure,CONTAINER_PATH


def get_container(pathlist,pattern,use_singularity):
    
    # For running without containers
    if pathlist is None: # Retain backwards compatibility with hippo fix
        return ''
    if not use_singularity:
        return ''

    ll = []
    for path in pathlist:
        # Search for a file matching pattern in path
        path = path.rstrip('/')+'/'
        ll.extend(sorted(glob.glob(path+'*'+pattern+'*img')))
        ll.extend(sorted(glob.glob(path+'*'+pattern+'*sif')))

    # Exclude stimela's casa4.7 and casarest containers
    if 'casa' in pattern.lower():
        for ii in ll:
            if 'casa47' in ii or 'casarest' in ii:
                ll.remove(ii)

    if len(ll) == 0:
        print(col(pattern)+'not found!')
        print_spacer()
        sys.exit()
    container = ll[-1]
    opstr = container.split('/')[-1]
    if len(ll) > 1:
        opstr += ' (multiple matches found)'
    print(col(pattern)+opstr)
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
    code = code.replace('.','X')
    return code


def get_mms_code(myms):

    # Last three digits of the data set ID

    myms = myms.split('/')[-1]
    code = myms.split('.')[-2][-3:]
    return code


def get_target_code(targetname):

    # Last three digits of the target name

    code = targetname.replace('-','_').replace('.','p').replace(' ','')[-3:]
    return code


def scrub_target_name(targetname):
#    scrubbed = targetname.replace('+','p').replace(' ','_')
    scrubbed = targetname.replace(' ','_')
    return scrubbed


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


def job_handler(syscall,
                jobname,
                infrastructure,
                dependency = None,
                slurm_config = cfg.SLURM_DEFAULTS,
                slurm_account = cfg.SLURM_ACCOUNT,
                slurm_reservation = cfg.SLURM_RESERVATION,
                slurm_nodelist = cfg.SLURM_NODELIST,
                slurm_exclude = cfg.SLURM_EXCLUDE,
                pbs_config = cfg.PBS_DEFAULTS,
                bind = cfg.BIND):
                # slurm_time=cfg.SLURM_TIME,
                # slurm_partition=cfg.SLURM_PARTITION,
                # slurm_ntasks=cfg.SLURM_NTASKS,
                # slurm_nodes=cfg.SLURM_NODES,
                # slurm_cpus=cfg.SLURM_CPUS,
                # slurm_mem=cfg.SLURM_MEM,
                # pbs_program=cfg.PBS_PROGRAM,
                # pbs_walltime=cfg.PBS_WALLTIME,
                # pbs_queue=cfg.PBS_QUEUE,
                # pbs_nodes=cfg.PBS_NODES,
                # pbs_ppn=cfg.PBS_PPN,
                # pbs_mem=cfg.PBS_MEM):


    if infrastructure == 'idia' or infrastructure == 'hippo':


        slurm_time = slurm_config['TIME']
        slurm_partition = slurm_config['PARTITION']
        slurm_ntasks = slurm_config['NTASKS']
        slurm_nodes = slurm_config['NODES']
        slurm_cpus = slurm_config['CPUS']
        slurm_mem = slurm_config['MEM']
        
        # HACK: Override idia settings if hippo here
        # (really this should be broken down as slurm vs. non-slurm scheduler
        if infrastructure == 'hippo':
            if int(slurm_cpus) > 20:
                slurm_cpus='20'
            if int(slurm_cpus) < 20:
                slurm_mem = '60000'
            else:
                slurm_mem = '64000'
            slurm_partition = 'debug'

        slurm_runfile = cfg.SCRIPTS+'/slurm_'+jobname+'.sh'
        slurm_logfile = cfg.LOGS+'/slurm_'+jobname+'.log'

        run_command = jobname+"=`sbatch "
        if dependency:
            #run_command += "-d afterok:${"+dependency+"} "
            run_command += '-d afterok:'+'${'+dependency.replace(':','}:${')+'} '
        run_command += slurm_runfile+" | awk '{print $4}'`"

        if cfg.SLURM_NODELIST != '':
            slurm_nodelist = '#SBATCH --nodelist='+cfg.SLURM_NODELIST+'\n'
        else:
            slurm_nodelist = ''

        if cfg.SLURM_EXCLUDE != '':
            slurm_exclude = '#SBATCH --exclude='+cfg.SLURM_EXCLUDE+'\n'
        else:
            slurm_exclude = ''

        if cfg.SLURM_ACCOUNT != '':
            slurm_account = '#SBATCH --account='+cfg.SLURM_ACCOUNT+'\n'
        else:
            slurm_account = ''

        if cfg.SLURM_RESERVATION != '':
            slurm_reservation = '#SBATCH --reservation='+cfg.SLURM_RESERVATION+'\n'
        else:
            slurm_reservation = ''

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
            slurm_nodelist,
            slurm_exclude,
            slurm_account,
            slurm_reservation,
            'SECONDS=0\n',
            syscall+'\n',
            'echo "****ELAPSED "$SECONDS" '+jobname+'"\n'])
#            'sleep 10\n'])
        f.close()

        make_executable(slurm_runfile)

    elif infrastructure == 'chpc':

        pbs_program = pbs_config['PROGRAM']
        pbs_walltime = pbs_config['WALLTIME']
        pbs_queue = pbs_config['QUEUE']
        pbs_nodes = pbs_config['NODES']
        pbs_ppn = pbs_config['PPN']
        pbs_mem = pbs_config['MEM']

        pbs_runfile = cfg.SCRIPTS+'/pbs_'+jobname+'.sh'
        pbs_logfile = cfg.LOGS+'/pbs_'+jobname+'.log'
        pbs_errfile = cfg.LOGS+'/pbs_'+jobname+'.err'

        run_command = jobname+"=`qsub "
        if dependency:
          run_command += "-W depend=afterok:${"+dependency+"} "
        run_command += pbs_runfile+" | awk '{print $1}'`"

        f = open(pbs_runfile,'w')
        f.writelines(['#!/bin/bash\n',
            '#PBS -N '+jobname+'\n',
            '#PBS -P '+pbs_program+'\n'
            '#PBS -l walltime='+pbs_walltime+'\n',
            '#PBS -l nodes='+pbs_nodes+':ppn='+pbs_ppn+',mem='+pbs_mem+'\n',
            '#PBS -q '+pbs_queue+'\n'
            '#PBS -o '+pbs_logfile+'\n'
            '#PBS -e '+pbs_errfile+'\n'
            'SECONDS=0\n'
            'module load chpc/singularity\n'
            'cd '+cfg.CWD+'\n',
            syscall+'\n',
            'echo "****ELAPSED "$SECONDS" "'+jobname+'"\n',
            'sleep 10\n'])
        f.close()

        make_executable(pbs_runfile)

    elif infrastructure == 'node':

        node_logfile = cfg.LOGS+'/oxk_'+jobname+'.log'
        run_command = syscall+' | tee '+node_logfile
        

    run_command += '\n'

    return run_command


def mem_string_to_gb(mem):
    headroom = 0.98 # fraction of memory specified in IDIA/CHPC config to convert to absmem (hippo a special case)
    mem = mem.upper().replace('B','')
    if 'M' in mem:
        factor = 1e-3
    if 'G' in mem:
        factor = 1
    if 'T' in mem:
        factor = 1e3
    absmem = float(''.join(x for x in mem if x.isdigit()))
    absmem = int(absmem * factor * headroom)
    return absmem


def absmem_helper(step,infrastructure,absmem):
    if infrastructure == 'chpc':
        config_mem = step['pbs_config']['MEM']
    elif infrastructure == 'idia':
        config_mem = step['slurm_config']['MEM']
    elif infrastructure == 'hippo':
        slurm_cpus = step['slurm_config']['CPUS']
        if int(slurm_cpus) > 20:
            slurm_cpus='20'
        if int(slurm_cpus) < 20:
            config_mem = '60gb'
        else:
            config_mem = '64gb'
    if infrastructure != 'node':
        absmem = mem_string_to_gb(config_mem)
    return absmem


def get_scan_times(scanpickle):
    scan_times = []
    ss = pickle.load(open(scanpickle,'rb'))
    fields = []
    for ii in ss:
        fields.append(ii[1])
    fields = numpy.unique(fields).tolist()
    for field in fields:
        scans = []
        intervals = []
        for ii in ss:
            if ii[1] == field:
                scans.append(ii[0])
                intervals.append(ii[5])
        scan_times.append((field,scans,intervals))
    return scan_times



def generate_syscall_casa(casascript,casalogfile='',extra_args=''):

    syscall = 'casa -c '+casascript+' '
    if casalogfile != '':
        syscall += '--logfile '+casalogfile+' '
    else:
        syscall += '--log2term '
    syscall += '--nogui '
    if extra_args != '':
      syscall += extra_args
#    syscall += '\n'

    return syscall


def generate_syscall_cubical(parset,myms,extra_args=''):

    # now = timenow()
    # outname = 'cube_'+prefix+'_'+myms.split('/')[-1]+'_'+now

    # # Debugging stuff
    # syscall = 'bash -c "/sbin/sysctl vm.max_map_count ; '
    # syscall += 'df -h /dev/shm ; '

    # syscall += 'gocubical '+parset+' '
    # syscall += '--data-ms='+myms+' '
    # syscall += '--out-name='+outname

    # # Move output to logs...
    # syscall += ' ; mv '+outname+'* '+LOGS+'"'

    syscall = 'gocubical '+parset+' '
    syscall += '--data-ms='+myms+' '
    if extra_args != '':
        syscall += extra_args
#        syscall += '--out-name '+outname+' '

    return syscall


def generate_syscall_tricolour(myms = '',
                          config = '',
                          datacol = 'DATA',
                          subtractcol = '',
                          fields = 'all',
                          strategy = 'polarisation'):

    syscall = 'tricolour '
    syscall += '--config '+config+' '
    syscall += '--data-column '+datacol+' '
    if subtractcol != '':
        syscall += '--subtract-model-colum '+subtractcol+' '
    if fields != 'all':
        syscall += '--field-names '+fields+' '
    syscall += '--flagging-strategy '+strategy+' '
    syscall += myms

    return syscall


def generate_syscall_wsclean(mslist,
                          imgname,
                          datacol,
                          continueclean = cfg.WSC_CONTINUE,
                          field = cfg.WSC_FIELD,
                          makepsf = cfg.WSC_MAKEPSF,
                          nodirty = cfg.WSC_NODIRTY,
                          startchan = cfg.WSC_STARTCHAN,
                          endchan = cfg.WSC_ENDCHAN,
                          minuvl = cfg.WSC_MINUVL,
                          maxuvl = cfg.WSC_MAXUVL,
                          even = cfg.WSC_EVEN,
                          odd = cfg.WSC_ODD,
                          chanout = cfg.WSC_CHANNELSOUT,
                          interval0 = cfg.WSC_INTERVAL0,
                          interval1 = cfg.WSC_INTERVAL1,
                          intervalsout = cfg.WSC_INTERVALSOUT,
                          imsize = cfg.WSC_IMSIZE,
                          cellsize = cfg.WSC_CELLSIZE,
                          briggs = cfg.WSC_BRIGGS,
                          tapergaussian = cfg.WSC_TAPERGAUSSIAN,
                          niter = cfg.WSC_NITER,
                          gain = cfg.WSC_GAIN,
                          mgain = cfg.WSC_MGAIN,
                          multiscale = cfg.WSC_MULTISCALE,
                          scales = cfg.WSC_SCALES,
                          nonegative = cfg.WSC_NONEGATIVE,
                          sourcelist = cfg.WSC_SOURCELIST,
                          bda = cfg.WSC_BDA,
                          bdafactor = cfg.WSC_BDAFACTOR,
                          nwlayersfactor = cfg.WSC_NWLAYERSFACTOR,
                          joinchannels = cfg.WSC_JOINCHANNELS,
                          padding = cfg.WSC_PADDING,
                          nomodel = cfg.WSC_NOMODEL,
                          mask = cfg.WSC_MASK,
                          threshold = cfg.WSC_THRESHOLD,
                          autothreshold = cfg.WSC_AUTOTHRESHOLD,
                          automask = cfg.WSC_AUTOMASK,
                          localrms = cfg.WSC_LOCALRMS,
                          stopnegative = cfg.WSC_STOPNEGATIVE,
                          fitspectralpol = cfg.WSC_FITSPECTRALPOL,
                          circularbeam = cfg.WSC_CIRCULARBEAM,
                          mem = cfg.WSC_MEM,
                          absmem = cfg.WSC_ABSMEM,
                          useidg = cfg.WSC_USEIDG,
                          idgmode = cfg.WSC_IDGMODE,
                          paralleldeconvolution = cfg.WSC_PARALLELDECONVOLUTION):

    # Generate system call to run wsclean


    if is_odd(imsize):
        print(col('wsclean')+'Do not use odd image sizes')
        sys.exit()

    if continueclean and bda:
        print(col('wsclean')+'Cannot continue deconvolution if BDA is enabled')
        sys.exit()

    if even and odd:
        print(col('wsclean')+'Even and odd timeslots selections are both enabled, defaulting to all.')
        even = False
        odd = False

    syscall = 'wsclean '
    syscall += '-log-time '
    syscall += '-parallel-reordering 8 '
    if continueclean:
        syscall += '-continue '
    syscall += '-field '+str(field)+' '
    if makepsf:
        syscall += '-make-psf '
    if nodirty:
        syscall += '-no-dirty '
    if sourcelist: # and fitspectralpol != 0:
        syscall += '-save-source-list '
    syscall += '-size '+str(imsize)+' '+str(imsize)+' '
    syscall += '-scale '+cellsize+' '
    if bda and not useidg:
        syscall += '-baseline-averaging '+str(bdafactor)+' '
        syscall += '-no-update-model-required '
    elif not bda and nomodel:
        syscall += '-no-update-model-required '
    syscall += '-nwlayers-factor '+str(nwlayersfactor)+' '
    if useidg:
        syscall += '-use-idg '
        syscall += '-idg-mode '+idgmode+' '
    if multiscale:
        syscall += '-multiscale '
        syscall += '-multiscale-scales '+scales+' '
    syscall += '-niter '+str(niter)+' '
    syscall += '-gain '+str(gain)+' '
    syscall += '-mgain '+str(mgain)+' '
    if nonegative:
        syscall += '-no-negative '
    syscall += '-weight briggs '+str(briggs)+' '
    if tapergaussian != '':
        syscall += '-taper-gaussian '+str(tapergaussian)+' '
    syscall += '-data-column '+datacol+' '
    if paralleldeconvolution != 0:
        syscall += '-parallel-deconvolution '+str(paralleldeconvolution)+' '
    if startchan != -1 and endchan != -1:
        syscall += '-channel-range '+str(startchan)+' '+str(endchan)+' '
    if minuvl != '':
        syscall += '-minuv-l '+str(minuvl)+' '
    if maxuvl != '':
        syscall += '-maxuv-l '+str(maxuvl)+' '
    if even:
        syscall += '-even-timesteps '
    if odd:
        syscall += '-odd-timesteps '
    if interval0 and interval1:
        syscall += '-intervals '+str(interval0)+' '+str(interval1)+' '
    if intervalsout:
        syscall += '-intervalsout '+str(intervalsout)+' '
    if mask:
        if mask.lower() == 'fits':
            mymask = glob.glob('*mask.fits')[0]
            syscall += '-fits-mask '+mymask+' '
        else:
            syscall += '-fits-mask '+mask+' '
    if automask:
        syscall += '-auto-mask '+str(automask)+' '
#    if autothreshold:
        syscall += '-auto-threshold '+str(autothreshold)+' '
#    if localrms:
        syscall += '-local-rms '
    if threshold:
        syscall += '-threshold '+str(threshold)+' '
    if stopnegative:
        syscall += '-stop-negative '        
    syscall += '-name '+imgname+' '
    if chanout:
        syscall += '-channels-out '+str(chanout)+' '
    if fitspectralpol != 0:
        syscall += '-fit-spectral-pol '+str(fitspectralpol)+' '
    if joinchannels:
        syscall += '-join-channels '
    syscall += '-padding '+str(padding)+' '
    if circularbeam:
        syscall += '-circular-beam '
    if absmem < 0:
        syscall += '-mem '+str(mem)+' '
    else:
        syscall += '-abs-mem '+str(absmem)+' '
    for myms in mslist:
        syscall += myms+' '

    return syscall


def generate_syscall_predict(msname,
                            imgbase,
                            field = cfg.WSC_FIELD,
                            nwlayersfactor = cfg.WSC_NWLAYERSFACTOR,
                            chanout = cfg.WSC_CHANNELSOUT,
#                            imsize = cfg.WSC_IMSIZE,
#                            cellsize = cfg.WSC_CELLSIZE,
#                            predictchannels = cfg.WSC_PREDICTCHANNELS,
                            mem = cfg.WSC_MEM,
                            absmem = cfg.WSC_ABSMEM):

    # Generate system call to run wsclean in predict mode

    syscall = 'wsclean '
    syscall += '-log-time '
    syscall += '-predict '
    syscall += '-field '+str(field)+' '
    syscall += '-nwlayers-factor '+str(nwlayersfactor)+' '
    syscall += '-channels-out '+str(chanout)+' '
#    syscall += '-size '+str(imsize)+' '+str(imsize)+' '
#    syscall += '-scale '+cellsize+' '
    syscall += '-name '+imgbase+' '
    if absmem < 0:
        syscall += '-mem '+str(mem)+' '
    else:
        syscall += '-abs-mem '+str(absmem)+' '
#    syscall += '-predict-channels '+str(predictchannels)+' '
    syscall += msname

    return syscall 


MAKEMASK_THRESH = 6.0
MAKEMASK_DILATION = 3
MAKEMASK_BOXSIZE = 500
MAKEMASK_SMALLBOX = 50
MAKEMASK_ISLANDSIZE = 5000


def generate_syscall_makemask(restoredimage,
                            outfile = '',
                            thresh = cfg.MAKEMASK_THRESH,
                            boxsize = cfg.MAKEMASK_BOXSIZE,
                            smallbox = cfg.MAKEMASK_SMALLBOX,
                            islandsize = cfg.MAKEMASK_ISLANDSIZE,
                            dilation = cfg.MAKEMASK_DILATION,
                            zoompix = cfg.DDF_NPIX):

    # Generate call to MakeMask.py and dilate the result
  
    if outfile == '':
        outfile = restoredimage.replace('.fits','.mask.fits')

    syscall = 'bash -c "'
    syscall += 'python '+cfg.TOOLS+'/pyMakeMask.py '
    syscall += '--dilate='+str(dilation)+' '
    syscall += '--boxsize='+str(boxsize)+' '
    syscall += '--smallbox='+str(smallbox)+' '
    syscall += '--islandsize='+str(islandsize)+' '
    syscall += '--threshold='+str(thresh)+' '
    syscall += '--outfile='+str(outfile)+' '
    syscall += restoredimage

    if zoompix != '':
        zoomfits = outfile.replace('.fits','.zoom'+str(zoompix)+'.fits')
        syscall += ' && fitstool.py -z '+str(zoompix)+' -o '+zoomfits+' '
        syscall += outfile
    syscall += '"'

    return syscall,outfile


def generate_syscall_ddfacet(mspattern,
                          imgname,
                          ddid = cfg.DDF_DDID,
                          field = cfg.DDF_FIELD,
                          colname = cfg.DDF_COLNAME,
                          chunkhours = cfg.DDF_CHUNKHOURS,
                          datasort = cfg.DDF_DATASORT,
                          predictcolname = cfg.DDF_PREDICTCOLNAME,
                          initdicomodel = cfg.DDF_INITDICOMODEL,
                          outputalso = cfg.DDF_OUTPUTALSO,
                          outputimages = cfg.DDF_OUTPUTIMAGES,
                          outputcubes = cfg.DDF_OUTPUTCUBES,
                          npix = cfg.DDF_NPIX,
                          cell = cfg.DDF_CELL,
                          diammax = cfg.DDF_DIAMMAX,
                          diammin = cfg.DDF_DIAMMIN,
                          nfacets =cfg.DDF_NFACETS,
                          psfoversize = cfg.DDF_PSFOVERSIZE,
                          padding = cfg.DDF_PADDING,
                          robust = cfg.DDF_ROBUST,
                          sparsification = cfg.DDF_SPARSIFICATION,
                          ncpu = cfg.DDF_NCPU,
                          cachereset = cfg.DDF_CACHERESET,
                          cachedir = cfg.DDF_CACHEDIR,
                          cachehmp = cfg.DDF_CACHEHMP,
                          beam = cfg.DDF_BEAM,
                          beamnband = cfg.DDF_BEAMNBAND,
                          dtbeammin = cfg.DDF_DTBEAMMIN,
                          fitsparangleincdeg = cfg.DDF_FITSPARANGLEINCDEG,
                          beamcentrenorm = cfg.DDF_BEAMCENTRENORM,
                          beamsmooth = cfg.DDF_BEAMSMOOTH,
                          feedswap = cfg.DDF_FEEDSWAP,
                          nband = cfg.DDF_NBAND,
                          ndegridband = cfg.DDF_NDEGRIDBAND,
                          ddsols = cfg.DDF_DDSOLS,
                          ddmodegrid = cfg.DDF_DDMODEGRID,
                          ddmodedegrid = cfg.DDF_DDMODEDEGRID,
                          gain = cfg.DDF_GAIN,
                          fluxthreshold = cfg.DDF_FLUXTHRESHOLD,
                          cyclefactor = cfg.DDF_CYCLEFACTOR,
                          rmsfactor = cfg.DDF_RMSFACTOR,
                          deconvmode = cfg.DDF_DECONVMODE,
                          ssd_deconvpeakfactor = cfg.DDF_SSD_DECONVPEAKFACTOR,
                          ssd_maxminoriter = cfg.DDF_SSD_MAXMINORITER,
                          ssd_maxmajoriter = cfg.DDF_SSD_MAXMAJORITER,
                          ssd_enlargedata = cfg.DDF_SSD_ENLARGEDATA,
                          hogbom_deconvpeakfactor = cfg.DDF_HOGBOM_DECONVPEAKFACTOR,
                          hogbom_maxminoriter = cfg.DDF_HOGBOM_MAXMINORITER,
                          hogbom_maxmajoriter = cfg.DDF_HOGBOM_MAXMAJORITER,
                          hogbom_polyfitorder = cfg.DDF_HOGBOM_POLYFITORDER,
                          mask = cfg.DDF_MASK,
                          masksigma = cfg.DDF_MASKSIGMA,
                          conservememory = cfg.DDF_CONSERVEMEMORY):

    syscall = 'DDF.py '
    # [Data]
    syscall += '--Data-MS '+mspattern+'//'+ddid+'//'+field+' '
    syscall += '--Data-ColName '+colname+' '
    syscall += '--Data-ChunkHours '+str(chunkhours)+' '
    syscall += '--Data-Sort '+str(datasort)+' '
    # [Predict]
    if predictcolname:
        syscall += '--Predict-ColName '+predictcolname+' '
    if initdicomodel != '':
        syscall += '--Predict-InitDicoModel '+initdicomodel+' '
    # [Output]
    syscall += '--Output-Name '+imgname+' '
    syscall += '--Output-Mode Clean '
    syscall += '--Output-Also '+outputalso+' '
    syscall += '--Output-Images '+outputimages+' '
    if outputcubes != '':
        syscall += '--Output-Cubes '+outputcubes+' '
    # [Image]
    syscall += '--Image-NPix '+str(npix)+' '
    syscall += '--Image-Cell '+str(cell)+' '
    # [Facets]
    syscall += '--Facets-DiamMax '+str(diammax)+' '
    syscall += '--Facets-DiamMin '+str(diammin)+' '
    syscall += '--Facets-NFacets '+str(nfacets)+' '
    syscall += '--Facets-PSFOversize '+str(psfoversize)+' '
    syscall += '--Facets-Padding '+str(padding)+' '
    # [Weight]
    syscall += '--Weight-Robust '+str(robust)+' '
    # [CF]
    # syscall += '--CF-wmax 0 '
    # syscall += '--CF-Nw 100 '
    # [Comp]
    syscall += '--Comp-GridDecorr 0.01 '
    syscall += '--Comp-DegridDecorr 0.01 '
    syscall += '--Comp-Sparsification '+str(sparsification)+' '
    # [Parallel]
    syscall += '--Parallel-NCPU '+str(ncpu)+' '
    # [Cache]    
    syscall += '--Cache-Reset '+str(cachereset)+' '
    syscall += '--Cache-Dir '+str(cachedir)+' '
    syscall += '--Cache-HMP '+str(cachehmp)+' '
    # [Beam]
    if beam == '':
        syscall += '--Beam-Model None '
    else:
        syscall += '--Beam-Model FITS '
        syscall += "--Beam-FITSFile \'"+str(beam)+"\' "
        syscall += '--Beam-NBand '+str(beamnband)+' '
        syscall += '--Beam-DtBeamMin '+str(dtbeammin)+' '
        syscall += '--Beam-FITSParAngleIncDeg '+str(fitsparangleincdeg)+' '
        syscall += '--Beam-CenterNorm '+str(beamcentrenorm)+' '
        syscall += '--Beam-FITSFeedSwap '+str(feedswap)+' '
        syscall += '--Beam-Smooth '+str(beamsmooth)+' '
    # [Freq]
    syscall += '--Freq-NBand '+str(nband)+' '
    syscall += '--Freq-NDegridBand '+str(ndegridband)+' '
    # [DDESolutions]
    if ddsols != '':
        syscall += '--DDESolutions-DDSols '+ddsols+' '
        syscall += '--DDESolutions-DDModeGrid '+ddmodegrid+' '
        syscall += '--DDESolutions-DDModeDeGrid '+ddmodedegrid+' '
    # [Deconv]
    syscall += '--Deconv-Gain '+str(gain)+' '
    syscall += '--Deconv-FluxThreshold '+str(fluxthreshold)+' '
    syscall += '--Deconv-CycleFactor '+str(cyclefactor)+' '
    syscall += '--Deconv-RMSFactor '+str(rmsfactor)+' '
    if deconvmode.lower() == 'ssd':
        syscall += '--Deconv-Mode SSD '
        syscall += '--Deconv-PeakFactor '+str(ssd_deconvpeakfactor)+' '
        syscall += '--Deconv-MaxMajorIter '+str(ssd_maxmajoriter)+' '
        syscall += '--Deconv-MaxMinorIter '+str(ssd_maxminoriter)+' '
        syscall += '--SSDClean-NEnlargeData '+str(ssd_enlargedata)+' '
    elif deconvmode.lower() == 'hogbom':
        syscall += '--Deconv-Mode Hogbom '
        syscall += '--Deconv-PeakFactor '+str(hogbom_deconvpeakfactor)+' '
        syscall += '--Deconv-MaxMajorIter '+str(hogbom_maxmajoriter)+' '
        syscall += '--Deconv-MaxMinorIter '+str(hogbom_maxminoriter)+' '    
        syscall += '--Hogbom-PolyFitOrder '+str(hogbom_polyfitorder)+' '
    # [Mask]
    if mask.lower() == 'fits':
        mymask = sorted(glob.glob('*mask.fits')[0])
        syscall += '--Mask-Auto 0 '
        syscall += '--Mask-External '+mymask+' '
    elif mask.lower() == 'auto':
        syscall += '--Mask-Auto 1 '
        syscall += '--Mask-SigTh '+str(masksigma)+' '
    else:
        syscall += '--Mask-Auto 0 '
        syscall += '--Mask-External '+mask+' '
    # [Misc]
    syscall += '--Misc-ConserveMemory '+str(conservememory)+' '
    syscall += '--Log-Memory 1 '
    syscall += '--Log-Boring 1 '

    return syscall


def generate_syscall_killms(myms,
                        baseimg,
                        outsols,
                        nodesfile,
                        dicomodel = cfg.KMS_DICOMODEL,
                        tchunk = cfg.KMS_TCHUNK,
                        incol = cfg.KMS_INCOL,
                        outcol = cfg.KMS_OUTCOL,
                        beam = cfg.KMS_BEAM,
                        beamat = cfg.KMS_BEAMAT,
                        dtbeammin = cfg.KMS_DTBEAMMIN,
                        centrenorm = cfg.KMS_CENTRENORM,
                        nchanbeamperms = cfg.KMS_NCHANBEAMPERMS,
                        fitsparangleincdeg = cfg.KMS_FITSPARANGLEINCDEG,
                        fitsfeedswap = cfg.KMS_FITSFEEDSWAP,
                        maxfacetsize = cfg.KMS_MAXFACETSIZE,
                        uvminmax = cfg.KMS_UVMINMAX,
                        fieldid = cfg.KMS_FIELDID,
                        ddid = cfg.KMS_DDID,
                        ncpu = cfg.KMS_NCPU,
                        dobar = cfg.KMS_DOBAR,
                        debugpdb = cfg.KMS_DEBUGPDB,
                        solvertype= cfg.KMS_SOLVERTYPE,
                        dt = cfg.KMS_DT,
                        nchansols = cfg.KMS_NCHANSOLS,
                        niterkf = cfg.KMS_NITERKF,
                        covq = cfg.KMS_COVQ):

    # Generate system call to run killMS

    syscall = 'kMS.py '
    # [VisData]
    syscall+= '--MSName '+myms+' '
    syscall+= '--TChunk '+str(tchunk)+' '
    syscall+= '--InCol '+incol+' '
    syscall+= '--OutCol '+outcol+' '
    # [Beam]
    if beam == '':
        syscall+= '--BeamModel None '
    else:
        syscall+= '--BeamModel FITS '
        syscall+= '--BeamAt '+beamat+' '
        syscall+= '--DtBeamMin '+str(dtbeammin)+' '
        syscall+= '--CenterNorm '+str(centrenorm)+' '
        syscall+= '--NChanBeamPerMS '+str(nchanbeamperms)+' '
        syscall+= "--FITSFile \'"+str(beam)+"\' "
        syscall+= '--FITSParAngleIncDeg '+str(fitsparangleincdeg)+' '
        syscall+= '--FITSFeedSwap '+str(fitsfeedswap)+' '
    # [ImageSkyModel]
    syscall+= '--BaseImageName '+baseimg+' '
    if dicomodel != '':
        syscall+= '--DicoModel '+dicomodel+' '
    syscall+= '--NodesFile '+nodesfile+' '
    syscall+= '--MaxFacetSize '+str(maxfacetsize)+' '
    # [DataSelection]
    syscall+= '--UVMinMax '+uvminmax+' '
    syscall+= '--FieldID '+str(fieldid)+' '
    syscall+= '--DDID '+str(ddid)+' '
    # [Weighting]
    syscall+= '--Weighting Natural '
    # [Actions]
    syscall+= '--NCPU '+str(ncpu)+' '
    syscall+= '--DoBar '+str(dobar)+' '
#    syscall+= '--DebugPdb '+str(debugpdb)+' '
    # [Solutions]
    syscall+= '--OutSolsName '+outsols+' '
    # [Solvers]
    syscall+= '--SolverType '+solvertype+' '
    syscall+= '--PolMode Scalar '
    syscall+= '--dt '+str(dt)+' '
    syscall+= '--NChanSols '+str(nchansols)+' '
    # [KAFCA]
    syscall+= '--NIterKF '+str(niterkf)+' '
    syscall+= '--CovQ '+str(covq)+' '

    return syscall


def generate_syscall_pybdsf(fitsfile,
                        thresh_pix = cfg.PYBDSF_THRESH_PIX,
                        thresh_isl = cfg.PYBDSF_THRESH_ISL,
                        catalogtype = cfg.PYBDSF_CATALOGTYPE,
                        catalogformat = cfg.PYBDSF_CATALOGFORMAT):

    if catalogtype == 'srl':
        opfile = fitsfile+'.srl'
    elif catalogtype == 'gaul':
        opfile = fitsfile+'.gaul'

    if catalogformat == 'fits':
        opfile += '.fits'

    syscall = "python3 -c '"
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
                        ndir = cfg.CLUSTERCAT_NDIR,
                        centralradius = cfg.CLUSTERCAT_CENTRALRADIUS,
                        ngen = cfg.CLUSTERCAT_NGEN,
                        fluxmin = cfg.CLUSTERCAT_FLUXMIN,
                        ncpu = cfg.CLUSTERCAT_NCPU):

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

