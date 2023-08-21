#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk


import glob
import numpy
import os
import pickle
import sys
import os.path as o

sys.path.append(o.abspath(o.join(o.dirname(sys.modules[__name__].__file__), "..")))

from oxkat import generate_jobs as gen
from oxkat import config as cfg


def write_slurm(opfile,jobname,logfile,syscall):

    f = open(opfile,'w')
    f.writelines(['#!/bin/bash\n',
        '#file: '+opfile+':\n',
        '#SBATCH --job-name='+jobname+'\n',
        '#SBATCH --time=07:00:00\n',
        '#SBATCH --partition=Main\n'
        '#SBATCH --ntasks=1\n',
        '#SBATCH --nodes=1\n',
        '#SBATCH --cpus-per-task=16\n',
        '#SBATCH --mem=115GB\n',
        '#SBATCH --account=b24-thunderkat-ag\n',
        '#SBATCH --output='+logfile+'\n',
        syscall+'\n'])
    f.close()


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


def main():

    INFRASTRUCTURE, CONTAINER_PATH = gen.set_infrastructure(('','idia'))
    WSCLEAN_CONTAINER = gen.get_container(CONTAINER_PATH,cfg.WSCLEAN_PATTERN,True)


    scan_pickle = sys.argv[1]
    scan_times = get_scan_times(scan_pickle)

    if not os.path.isdir('INTERVALS'):
        os.mkdir('INTERVALS')


    runfile = 'submit_interval_jobs.sh'

    f = open(runfile,'w')
    f.writelines(['#!/bin/bash\n'])

    for ss in scan_times:
        targetname = ss[0]
        scans = ss[1]
        intervals = ss[2]
        print('Target:    '+targetname)
        print('Scans:     '+str(scans))
        print('Intervals: '+str(intervals))
        for i in range(0,len(scans)):
            myms = glob.glob('*'+targetname+'*scan'+str(scans[i])+'.ms')
            if len(myms) == 1:
                myms = myms[0]
                if os.path.isdir(myms):
                    opdir = 'INTERVALS/'+targetname+'_scan'+str(scans[i])
                    if not os.path.isdir(opdir):
                        os.mkdir(opdir)

                    imgname = opdir+'/img_'+myms+'_modelsub'
                    code = 'intrvl'+str(scans[i])

                    syscall = 'singularity exec '+WSCLEAN_CONTAINER+' '
                    syscall += 'wsclean -intervals-out '+str(intervals[i])+' -interval 0 '+str(intervals[i])+' '
                    syscall += '-log-time -field 0 -no-dirty -make-psf -size 4680 4680 -scale 1.1asec -baseline-averaging 10 -no-update-model-required '
                    syscall += '-nwlayers 1 -niter 0 -name '+imgname+' '
                    syscall += '-weight briggs -0.3 -data-column CORRECTED_DATA -padding 1.2 -absmem 110 '+myms

                    slurm_file = 'SCRIPTS/slurm_intervals_'+code+'.sh'
                    log_file = 'LOGS/slurm_intervals_'+code+'.log'

                    write_slurm(opfile=slurm_file,jobname=code,logfile=log_file,syscall=syscall)

                    f.writelines(['sbatch '+slurm_file+'\n'])
                    
    f.close()
    gen.make_executable(runfile)
    print('Wrote '+runfile+' script')


if __name__ == "__main__":


    main()
