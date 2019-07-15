import sys
import glob


def write_slurm(opfile,
                jobname,
                logfile,
                container,
                syscall,
                ntasks='1',
                nodes='1',
                cpus='32',
                mem='230GB'):

    f = open(opfile,'w')
    f.writelines(['#!/bin/bash\n',
        '#file: '+opfile+':\n',
        '#SBATCH --job-name='+jobname+'\n',
        '#SBATCH --ntasks='+ntasks+'\n',
        '#SBATCH --nodes='+nodes+'\n',
        '#SBATCH --cpus-per-task='+cpus+'\n',
        '#SBATCH --mem='+mem+'\n',
        '#SBATCH --output='+logfile+'\n',
        syscall+'\n',
        'sleep 10\n'])
    f.close()


def generate_syscall_mviewer(infits):
    outpng = infits+'.png'
    syscall = 'mViewer '
    syscall += '-color yellow '
    syscall += '-grid Equatorial J2000 '
    syscall += '-ct 0 '
    syscall += '-gray '+infits+' '
#    syscall += '-3s max gaussian-log '
    syscall += '-1e-5 5e-5 '
    syscall += '-png '+outpng+' '
    syscall += '; '
    return syscall


def main():


    KERN_CONTAINER = '/data/exp_soft/containers/kern4-2018-11-28.simg'


    pattern = sys.argv[1]


    print(pattern)

    fitslist = glob.glob(pattern)

    slurmfile = 'slurm_render_pngs.sh'
    logfile = 'slurm_render_pngs.log'

    syscall = ''

    print(fitslist)

    for infits in fitslist:
        print(infits)
        syscall += 'srun singularity exec '+KERN_CONTAINER+' '+generate_syscall_mviewer(infits)+'\n'

    write_slurm(opfile=slurmfile,
            jobname='makepngs',
            logfile=logfile,
            container=KERN_CONTAINER,
            syscall=syscall)

    print('sbatch '+slurmfile)


if __name__ == "__main__":


    main()