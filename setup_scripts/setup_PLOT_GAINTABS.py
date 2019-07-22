#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk


import sys
import glob
import pickle
from oxkat import generate_jobs as gen


def main():
    
    
    CWD = gen.CWD
    OXKAT = gen.OXKAT
    SCRIPTS = gen.SCRIPTS
    LOGS = gen.LOGS
    PARSETS = gen.PARSETS
    KERN_CONTAINER = gen.KERN_CONTAINER
    PLOT_SCRIPTS = gen.PLOT_SCRIPTS


    gen.setup_dir(SCRIPTS)
    gen.setup_dir(LOGS)


    slurmfile = SCRIPTS+'/slurm_plots.sh'
    logfile = slurmfile.replace('.sh','.log')


    info = pickle.load(open('project_info.p','rb'))
    primary = info['primary'][1]
    secondary = info['secondary'][1]


    gaintab0 = glob.glob('cal_*.G0')[0]
    gaintab1 = glob.glob('cal_*.G1')[0]
    bptab = glob.glob('cal_*.B0')[0]


    syscall = 'bash -c "'


    for corr in ['0','1']:
        syscall += 'python '+PLOT_SCRIPTS+'/plot_bandpass.py -f '+primary+' -c '+corr+' '+CWD+'/'+bptab+'; '
        syscall += 'python '+PLOT_SCRIPTS+'/plot_bandpass.py -f '+primary+' -c '+corr+' '+CWD+'/'+gaintab0+'; '
        syscall += 'python '+PLOT_SCRIPTS+'/plot_gaintab.py -f '+primary+' -c '+corr+' '+CWD+'/'+gaintab1+'; '
        syscall += 'python '+PLOT_SCRIPTS+'/plot_gaintab.py -f '+secondary+' -c '+corr+' '+CWD+'/'+gaintab1+'; '


    syscall += ' ; mv plot_cal*.png '+LOGS+'"'


    gen.write_slurm(opfile=slurmfile,
            jobname='plots',
            logfile=logfile,
            container=KERN_CONTAINER,
            syscall=syscall)


if __name__ == "__main__":


    main()
