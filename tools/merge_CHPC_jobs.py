#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk

import sys
import os.path as o
sys.path.append(o.abspath(o.join(o.dirname(sys.modules[__name__].__file__), "..")))
from oxkat import config as cfg


submit_file = sys.argv[1]


pbs_config = cfg.PBS_WSCLEAN
pbs_program = pbs_config['PROGRAM']
pbs_walltime = '48:00:00'
pbs_queue = pbs_config['QUEUE']
pbs_nodes = pbs_config['NODES']
pbs_ppn = pbs_config['PPN']
pbs_mem = pbs_config['MEM']


outfile = submit_file.replace('submit','pbs_merged')
pbs_logfile = cfg.LOGS+'/'+outfile.replace('.sh','.log')
pbs_errfile = pbs_logfile.replace('.log','.err')



pbs_list = []
f = open(submit_file,'r')
line = f.readline()
while line:
    if line[0] != '#':
        cols = line.split()
        for col in cols:
            if '/pbs_' in col:
                pbs_list.append(col)
    line = f.readline()
f.close()


singularity_calls = []
for pbs_file in pbs_list:
    f = open(pbs_file,'r')
    line = f.readline()
    while line:
        cols = line.split()
        for col in cols:
            if 'exec' in col:
                singularity_calls.append(line)
        line = f.readline()
f.close()


f = open(outfile,'w')
f.writelines(['#!/bin/bash\n',
    '#PBS -N 1GC \n',
    '#PBS -P '+pbs_program+'\n',
    '#PBS -l walltime='+pbs_walltime+'\n',
    '#PBS -l nodes='+pbs_nodes+':ppn='+pbs_ppn+',mem='+pbs_mem+'\n',
    '#PBS -q '+pbs_queue+'\n',
    '#PBS -o '+pbs_logfile+'\n',
    '#PBS -e '+pbs_errfile+'\n',
    'module load chpc/singularity\n',
    'cd '+cfg.CWD+'\n'])
for ii in singularity_calls:
    f.writelines([ii])
f.writelines(['sleep 10\n'])


print('qsub '+outfile)
