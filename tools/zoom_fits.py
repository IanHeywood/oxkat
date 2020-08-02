import sys
import glob


def write_slurm(opfile,
                jobname,
                logfile,
                container,
                syscall,
                ntasks='1',
                nodes='1',
                cpus='8',
                mem='8GB'):

    f = open(opfile,'w')
    f.writelines(['#!/bin/bash\n',
        '#file: '+opfile+':\n',
        '#SBATCH --job-name='+jobname+'\n',
        '#SBATCH --time=01:00:00\n',
        '#SBATCH --ntasks='+ntasks+'\n',
        '#SBATCH --nodes='+nodes+'\n',
        '#SBATCH --cpus-per-task='+cpus+'\n',
        '#SBATCH --mem='+mem+'\n',
        '#SBATCH --output='+logfile+'\n',
        syscall+'\n',
        'sleep 10\n'])
    f.close()



def main():


    MEQTREES_CONTAINER = '/idia/software/containers/STIMELA_IMAGES/stimela_meqtrees_1.2.4.sif'

    pattern = sys.argv[1]


    fitslist = glob.glob(pattern)

    slurmfile = 'slurm_zoom_fits.sh'
    logfile = 'slurm_zoom_fits.log'

    syscall = ''

    print(fitslist)

    for infits in fitslist:
        print(infits)
        syscall += 'singularity exec '+MEQTREES_CONTAINER+' fitstool.py -z 5450 '+infits+'\n'

    write_slurm(opfile=slurmfile,
            jobname='zoomfits',
            logfile=logfile,
            container=MEQTREES_CONTAINER,
            syscall=syscall)

    print('sbatch '+slurmfile)


if __name__ == "__main__":


    main()