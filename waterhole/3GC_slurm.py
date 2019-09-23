#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk


import os.path as o
import pickle
import sys
sys.path.append(o.abspath(o.join(o.dirname(sys.modules[__name__].__file__), "..")))


from oxkat import generate_jobs as gen


def main():
    
    CWD = gen.CWD
    OXKAT = gen.OXKAT
    PARSETS = gen.PARSETS
    SCRIPTS = gen.SCRIPTS
    LOGS = gen.LOGS
    DDFACET_CONTAINER = gen.DDFACET_CONTAINER 


    submit_file = 'submit_3GC_jobs.sh'
    kill_file = 'kill_3GC_jobs.sh'


    gen.setup_dir(SCRIPTS)
    gen.setup_dir(LOGS)


    with open('project_info.p','rb') as f:
        project_info = pickle.load(f,encoding='latin1')


    targets = project_info['target_list'] 


    f = open(submit_file,'w')


    for target in targets:


        fieldname = target[0]
        code = fieldname[-3:]
        myms = target[2].rstrip('/')


        pcal_prefix = 'img_'+myms+'_pcal'
        ddf1_prefix = 'img_'+myms+'_DDF_corr'



        # ------------------------------------------------------------------------------
        # Make FITS mask 


        slurmfile = SCRIPTS+'/slurm_makemask1_'+code+'.sh'
        logfile = LOGS+'/slurm_makemask1_'+code+'.log'

        syscall,fitsmask = gen.generate_syscall_makemask(pcal_prefix)
        syscall = 'singularity exec '+DDFACET_CONTAINER+' '+syscall


        gen.write_slurm(opfile=slurmfile,
                    jobname=code+'mask1',
                    logfile=logfile,
                    syscall=syscall)


        job_id_makemask1 = 'MAKEMASK1_'+code
        syscall = job_id_makemask1+"=`sbatch "+slurmfile+" | awk '{print $4}'`"
        f.write(syscall+'\n')


        # ------------------------------------------------------------------------------
        # DDFacet


        slurmfile = SCRIPTS+'/slurm_ddf_corr_'+code+'.sh'
        logfile = LOGS+'/slurm_ddf_corr_'+code+'.log'


        syscall = 'singularity exec '+DDFACET_CONTAINER+' '
        syscall += gen.generate_syscall_ddfacet(mspattern=myms,
                    imgname=ddf1_prefix,
                    chunkhours=2,
                    mask=fitsmask)


        gen.write_slurm(opfile=slurmfile,
                    jobname=code+'ddfac',
                    partition='HighMem',
                    logfile=logfile,
                    syscall=syscall)


        job_id_ddf1 = 'DDF1_'+code
        syscall = job_id_ddf1+"=`sbatch -d afterok:${"+job_id_makemask1+"} "+slurmfile+" | awk '{print $4}'`"
        f.write(syscall+'\n')





        # ------------------------------------------------------------------------------

    kill = 'echo "scancel "$'+job_id_ddf1+' > '+kill_file

    f.write(kill+'\n')

    f.close()


if __name__ == "__main__":


    main()