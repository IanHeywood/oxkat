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
    CASA_CONTAINER = gen.CASA_CONTAINER
    WSCLEAN_CONTAINER = gen.WSCLEAN_CONTAINER
    CUBICAL_CONTAINER = gen.CUBICAL_CONTAINER


    PLOT_SCRIPTS = '/users/ianh/Software/plot_utils'


    gen.setup_scripts_dir()


    runfile = SCRIPTS+'/run_plots.sh'
    slurmfile = SCRIPTS+'/slurm_plots.sh'
    logfile = slurmfile.replace('.sh','.log')


    info = pickle.load(open('project_info.p','rb'))
    primary = info['primary'][1]
    secondary = info['secondary'][1]


    gaintab0 = glob.glob('cal_*.G0')[0]
    gaintab1 = glob.glob('cal_*.G1')[0]
    bptab = glob.glob('cal_*.B0')[0]


    f = open(runfile,'w')
    for corr in ['0','1']:
        syscall = 'python '+PLOT_SCRIPTS+'/plot_bandpass.py -f '+primary+' -c '+corr+' '+CWD+'/'+bptab+'\n'
        f.write(syscall)
        syscall = 'python '+PLOT_SCRIPTS+'/plot_bandpass.py -f '+primary+' -c '+corr+' '+CWD+'/'+gaintab0+'\n'
        f.write(syscall)
        syscall = 'python '+PLOT_SCRIPTS+'/plot_gaintab.py -f '+primary+' -c '+corr+' '+CWD+'/'+gaintab1+'\n'
        f.write(syscall)
        syscall = 'python '+PLOT_SCRIPTS+'/plot_gaintab.py -f '+secondary+' -c '+corr+' '+CWD+'/'+gaintab1+'\n'
        f.write(syscall)
    f.close()   

    gen.make_executable(runfile)

    gen.write_slurm('gainplot',logfile,CUBICAL_CONTAINER,runfile,slurmfile)


if __name__ == "__main__":


    main()
