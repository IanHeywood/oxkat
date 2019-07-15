import sys
import glob
from ..oxkat.generate_jobs import *



def main():


    pattern = sys.argv[1]

    gen.setup_dir(SCRIPTS)
    gen.setup_dir(PNGS)

    fitslist = glob.glob(pattern)

    slurmfile = SCRIPTS+'/slurm_render_pngs.sh'
    logfile = LOGS+'/slurm_render_pngs.log'

    syscall = ''

    for infits in fitslist:
        syscall += generate_syscall_mviewer(infits)

    gen.write_slurm(opfile=slurmfile,
            jobname='makepngs',
            logfile=logfile,
            container=KERN_CONTAINER,
            syscall=syscall)

    print('sbatch '+slurmfile)


if __name__ == "__main__":


    main()