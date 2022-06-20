import sys
import glob
import os.path as o

sys.path.append(o.abspath(o.join(o.dirname(sys.modules[__name__].__file__), "..")))

from oxkat import generate_jobs as gen
from oxkat import config as cfg


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
        '#SBATCH --account=b24-thunderkat-ag\n',
        '#SBATCH --output='+logfile+'\n',
        syscall+'\n',
        'sleep 10\n'])
    f.close()


def main():

    INFRASTRUCTURE, CONTAINER_PATH = gen.set_infrastructure(('','idia'))
    ASTROPY_CONTAINER = gen.get_container(CONTAINER_PATH,cfg.ASTROPY_PATTERN,True)

    pattern = sys.argv[1]
    mslist = glob.glob(pattern)
    submit_file = 'submit_uvsub_jobs.sh'

    f = open(submit_file,'w')

    for myms in mslist:
        code = myms.split('_')[-1].rstrip('.ms').replace('scan','uvsub')
        syscall = 'singularity exec '+ASTROPY_CONTAINER+' '
        syscall += 'python3 tools/sum_MS_columns.py --src=MODEL_DATA --dest=CORRECTED_DATA --subtract '+myms

        slurm_file = 'SCRIPTS/slurm_uvsub_'+myms+'.sh'
        log_file = 'LOGS/slurm_uvsub_'+myms+'.log'

        write_slurm(opfile=slurm_file,jobname=code,logfile=log_file,syscall=syscall )
        f.writelines(['sbatch '+slurm_file+'\n'])

    f.close()
    gen.make_executable(submit_file)
    print('Wrote '+submit_file)


if __name__ == "__main__":


    main()