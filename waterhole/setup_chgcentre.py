import glob
import os
import sys


def write_slurm(opfile,jobname,logfile,syscall):

    f = open(opfile,'w')
    f.writelines(['#!/bin/bash\n',
        '#file: '+opfile+':\n',
        '#SBATCH --job-name='+jobname+'\n',
        '#SBATCH --time=01:00:00\n',
        '#SBATCH --partition=Main\n'
        '#SBATCH --ntasks=1\n',
        '#SBATCH --nodes=1\n',
        '#SBATCH --cpus-per-task=8\n',
        '#SBATCH --mem=32GB\n',
        '#SBATCH --account=b24-thunderkat-ag\n',
        '#SBATCH --output='+logfile+'\n',
        syscall+'\n',
        'sleep 10\n'])
    f.close()


def main():


    CHGCENTRE_CONTAINER = '/idia/software/containers/STIMELA_IMAGES/stimela_chgcentre_1.2.0.sif'

    runfile = 'submit_chgcentre_jobs.sh'

    op = open(runfile,'w')
    op.writelines(['#!/bin/bash\n'])

    sunfile = sys.argv[1]
    f = open(sunfile)
    line = f.readline()
    while line:
        cols = line.split()
        if len(cols) == 18:
            scan = cols[5]
            field = cols[7]
            ra = cols[10]
            dec = cols[11]
            myms = glob.glob('*_'+field+'_scan'+scan+'.ms')

            if len(myms) == 1:

                myms = myms[0]
                code = 'chgcen'+scan
                syscall = 'singularity exec '+CHGCENTRE_CONTAINER+' '
                syscall += 'chgcentre '+myms+' '+ra+' '+dec

                slurm_file = 'SCRIPTS/slurm_'+code+'.sh'
                log_file = 'LOGS/slurm_'+code+'.log'

                write_slurm(opfile=slurm_file,jobname=code,logfile=log_file,syscall=syscall)

                op.writelines(['sbatch '+slurm_file+'\n'])

        line = f.readline()
    f.close()

    op.close()

    print('Wrote '+runfile+' script')

if __name__ == "__main__":


    main()