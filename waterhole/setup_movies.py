import glob
import os
import sys


def write_slurm(opfile,jobname,logfile,syscall):

    f = open(opfile,'w')
    f.writelines(['#!/bin/bash\n',
        '#file: '+opfile+':\n',
        '#SBATCH --job-name='+jobname+'\n',
        '#SBATCH --time=06:00:00\n',
        '#SBATCH --partition=Main\n'
        '#SBATCH --ntasks=1\n',
        '#SBATCH --nodes=1\n',
        '#SBATCH --cpus-per-task=4\n',
        '#SBATCH --mem=16GB\n',
        '#SBATCH --account=b24-thunderkat-ag\n',
        '#SBATCH --output='+logfile+'\n',
        syscall+'\n',
        'sleep 10\n'])
    f.close()


def main():


    MOVIE_CONTAINER = '/idia/software/containers/ASTRO-PY3-2021-10-26.simg'

    intervals = sorted(glob.glob('INTERVALS/*scan*'))
    rootdir = os.getcwd()


    for mydir in intervals:

        os.chdir(mydir)
        code = os.getcwd().split('/')[-1].split('_')[-1].replace('scan','movie')
        syscall = 'singularity exec '+MOVIE_CONTAINER+' '
        syscall += 'python '+rootdir+'/tools/make_movie.py'

        slurm_file = 'slurm_'+code+'.sh'
        log_file = 'slurm_'+code+'.log'

        write_slurm(opfile=slurm_file,jobname=code,logfile=log_file,syscall=syscall )
        os.chdir('../../')

        print('cd '+mydir)
        print('sbatch '+slurm_file)
        print('cd ../../')

if __name__ == "__main__":


    main()