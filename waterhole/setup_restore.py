import glob
import os
import os.path as o
import sys
sys.path.append(o.abspath(o.join(o.dirname(sys.modules[__name__].__file__), "..")))


from oxkat import generate_jobs as gen
from oxkat import config as cfg


def write_slurm(opfile,jobname,logfile,syscall):

    f = open(opfile,'w')
    f.writelines(['#!/bin/bash\n',
        '#file: '+opfile+':\n',
        '#SBATCH --job-name='+jobname+'\n',
        '#SBATCH --time=03:00:00\n',
        '#SBATCH --partition=Main\n'
        '#SBATCH --ntasks=1\n',
        '#SBATCH --nodes=1\n',
        '#SBATCH --cpus-per-task=4\n',
        '#SBATCH --mem=16GB\n',
        '#SBATCH --account=b24-thunderkat-ag\n',
        '#SBATCH --output='+logfile+'\n',
        syscall+'\n'])
    f.close()


def main():

    if len(sys.argv) == 1:
        print('Please specify the full path to the model image')
        sys.exit()
    else:
        model_fits = sys.argv[1]

    INFRASTRUCTURE, CONTAINER_PATH = gen.set_infrastructure(('','idia'))
    ASTROPY_CONTAINER = gen.get_container(CONTAINER_PATH,cfg.ASTROPY_PATTERN,True)

    intervals = sorted(glob.glob('INTERVALS/*scan*'))
    rootdir = os.getcwd()

    runfile = 'submit_restore_jobs.sh'

    f = open(runfile,'w')
    f.writelines(['#!/bin/bash\n'])

    for mydir in intervals:

        os.chdir(mydir)
        code = os.getcwd().split('/')[-1].split('_')[-1].replace('scan','rstor')
        syscall = 'singularity exec '+ASTROPY_CONTAINER+' '
        syscall += 'python3 '+rootdir+'/tools/restore_model.py '+model_fits

        slurm_file = 'slurm_'+code+'.sh'
        log_file = 'slurm_'+code+'.log'

        write_slurm(opfile=slurm_file,jobname=code,logfile=log_file,syscall=syscall )
        os.chdir('../../')

        f.writelines(['cd '+mydir+'\n',
            'sbatch '+slurm_file+'\n',
            'cd ../../\n'])

    f.close()
    gen.make_executable(runfile)
    print('\nWrote '+runfile+' script')

if __name__ == "__main__":


    main()
