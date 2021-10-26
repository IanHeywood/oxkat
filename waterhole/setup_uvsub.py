import sys
import glob


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
        '#SBATCH --mem=64GB\n',
        '#SBATCH --output='+logfile+'\n',
        syscall+'\n',
        'sleep 10\n'])
    f.close()


def main():


    OWLCAT_CONTAINER = '/idia/software/containers/caracal/STIMELA_IMAGES_1.6.8/stimela_owlcat_1.6.6.sif'

    pattern = sys.argv[1]

    mslist = glob.glob(pattern)

    for myms in mslist:
        code = myms.split('_')[-1].rstrip('.ms').replace('scan','uvsub')
        syscall = 'singularity exec '+OWLCAT_CONTAINER+' '
        syscall += 'python tools/sum_MS_columns.py --src=MODEL_DATA --dest=CORRECTED_DATA --subtract '+myms

        slurm_file = 'SCRIPTS/slurm_uvsub_'+myms+'.sh'
        log_file = 'LOGS/slurm_uvsub_'+myms+'.log'

        write_slurm(opfile=slurm_file,jobname=code,logfile=log_file,syscall=syscall )

        print('sbatch '+slurm_file)


if __name__ == "__main__":


    main()