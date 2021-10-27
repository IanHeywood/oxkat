#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk


import glob
import numpy
import os
import pickle
import sys

sys.path.append(o.abspath(o.join(o.dirname(sys.modules[__name__].__file__), "..")))

from oxkat import generate_jobs as gen
from oxkat import config as cfg


def write_slurm(opfile,jobname,logfile,syscall):

    f = open(opfile,'w')
    f.writelines(['#!/bin/bash\n',
        '#file: '+opfile+':\n',
        '#SBATCH --job-name='+jobname+'\n',
        '#SBATCH --time=04:00:00\n',
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

    
    WSCLEAN_CONTAINER = gen.get_container(CONTAINER_PATH,cfg.WSCLEAN_PATTERN,USE_SINGULARITY)


    scan_pickle = sys.argv[1]
    scan_times = get_scan_times(scan_pickle)


    for ss in scan_times:
        targetname = ss[0]
        scans = ss[1]
        intervals = ss[2]
        print('Target:    '+targetname)
        print('Scans:     '+str(scans))
        print('Intervals: '+str(intervals))
        for i in range(0,len(scans)):
            myms = glob.glob('*'+targetname+'*scan'+str(scans[i])+'.ms')[0]
            if os.path.isdir(myms):
                opdir = 'INTERVALS/'+targetname+'_scan'+str(scans[i])
                if not os.path.isdir(opdir):
                    os.mkdir(opdir)

                imgname = opdir+'/img_'+myms+'_modelsub'
                code = 'scan'+str(scans[i])

                syscall = 'singularity exec '+WSCLEAN_CONTAINER+' '
                syscall += gen.generate_syscall_wsclean(mslist = [myms],
                            imgname = imgname,
                            datacol = 'CORRECTED_DATA',
                            bda = True,
                            imsize = 4096,
                            cellsize = '2.0asec',
                            niter = 0,
                            briggs = -0.3,
                            chanout = None,
                            joinchannels = None,
                            absmem = 110)

                slurm_file = 'SCRIPTS/slurm_intervals_'+code+'.sh'
                log_file = 'LOGS/slurm_intervals_'+code+'.sh'

                write_slurm(opfile=slurm_file,jobname=code,logfile=log_file,syscall=syscall)

                print('sbatch '+slurm_file)




if __name__ == "__main__":


    main()
