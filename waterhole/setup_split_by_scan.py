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
        '#SBATCH --cpus-per-task=8\n',
        '#SBATCH --mem=32GB\n',
        '#SBATCH --account=b24-thunderkat-ag\n',
        '#SBATCH --output='+logfile+'\n',
        syscall+'\n'])
    f.close()


def main():

    if len(sys.argv) == 1:
        print('Please specify a Measurement Set to split')
        sys.exit()
    else:
        myms = sys.argv[1]

    INFRASTRUCTURE, CONTAINER_PATH = gen.set_infrastructure(('','idia'))
    CASA_CONTAINER = gen.get_container(CONTAINER_PATH,cfg.CASA_PATTERN,True)

    casa_file = 'casa_split_by_scan.py'
    slurm_file = 'slurm_split_by_scan.sh'
    log_file = slurm_file.replace('.sh','.log')

    f = open(casa_file,'w')
    f.writelines(['tb.open("'+myms+'")\n',
        'scans = sorted(set(tb.getcol("SCAN_NUMBER")))\n',
        'tb.done\n',
        'for scan in scans:\n',
        '    scan = str(scan)\n',
        '    opms = "'+myms+'".replace(".ms","_scan"+scan+".ms")\n',
        '    split(vis="'+myms+'",outputvis=opms,scan=scan,datacolumn="all")\n'])
    f.close()


    syscall = 'singularity exec '+CASA_CONTAINER+' casa -c '+casa_file+' --nologger --log2term --nogui'

    write_slurm(opfile=slurm_file,jobname='split',logfile=log_file,syscall=syscall )

    print('Run "sbatch '+slurm_file+'" to submit')


if __name__ == "__main__":

    main()
