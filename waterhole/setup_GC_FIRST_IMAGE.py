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
    CASA_CONTAINER = gen.CASA_CONTAINER
    WSCLEAN_CONTAINER = gen.WSCLEAN_CONTAINER


    submit_file = 'submit_2GC_jobs.sh'
    kill_file = 'kill_2GC_jobs.sh'


    gen.setup_dir(SCRIPTS)
    gen.setup_dir(LOGS)


#    project_info = pickle.load(open('project_info.p','rb'))
    with open('project_info.p','rb') as f:
        project_info = pickle.load(f,encoding='latin1')


    targets = project_info['target_list'] 


    f = open(submit_file,'w')
    f.write('touch '+kill_file+'\n')

    robs = [-1.5,-1.0,-0.5]


    for target in targets:

        myms = target[2].rstrip('/')
        code = target[0][-3:]

        job_ids = []
        for i in range(0,len(robs)):
            job_ids.append('GCIM_'+code+'_'+str(rob[i]))

        for i in range(0,len(robs)):

            rob = robs[i]

            image_prefix = 'img_'+myms+'_datar'+str(rob)


            slurmfile = SCRIPTS+'/slurm_wsclean_gc_r'+str(rob)+'_'+code+'.sh'
            logfile = LOGS+'/slurm_wsclean_gc_r'+str(rob)+'_'+code+'.log'

            syscall = 'singularity exec '+WSCLEAN_CONTAINER+' '

            syscall += gen.generate_syscall_wsclean(mslist=[myms],
                                    imgname=image_prefix,
                                    datacol='DATA',
                                    imsize=8192,
                                    briggs=rob,
                                    bda=True,
                                    niter=250000,
                                    multiscale=True,
                                    scales='0,3,9,27,81',
                                    mask='none')


            gen.write_slurm(opfile=slurmfile,
                        jobname=code+str(rob),
                        logfile=logfile,
                        syscall=syscall)


            job_id = job_ids[i]

            if rob == robs[0]:
                syscall = job_id+"=`sbatch "+slurmfile+" | awk '{print $4}'`"
            else:
                syscall = job_id+"=`sbatch -d afterok:${"+job_ids[i-1]+"} "+slurmfile+" | awk '{print $4}'`"

            f.write(syscall+'\n')

            kill = 'echo "scancel "$'+job_id+' >> '+kill_file

    f.write(kill+'\n')

    f.close()


if __name__ == "__main__":


    main()