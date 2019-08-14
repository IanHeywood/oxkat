#!/usr/bin/env python
# ian.heywood@astro.ox.ac.uk


import pickle
from oxkat import generate_jobs as gen


def main():
    
    CWD = gen.CWD
    OXKAT = gen.OXKAT
    PARSETS = gen.PARSETS
    SCRIPTS = gen.SCRIPTS
    LOGS = gen.LOGS
    WSCLEAN_CONTAINER = gen.WSCLEAN_CONTAINER
    CUBICAL_CONTAINER = gen.CUBICAL_CONTAINER
    DDFACET_CONTAINER = gen.DDFACET_CONTAINER 


    submit_file = 'submit_2GC_jobs.sh'
    kill_file = 'kill_2GC_jobs.sh'


    gen.setup_dir(SCRIPTS)
    gen.setup_dir(LOGS)


    project_info = pickle.load(open('project_info.p','rb'))


    targets = project_info['target_list'] 


    f = open(submit_file,'w')


    for target in targets:


        code = target[0][-3:]
        myms = target[2].rstrip('/')


        data_prefix = 'img_'+myms+'_data'
        pcal_prefix = 'img_'+myms+'_pcal'


        # ------------------------------------------------------------------------------
        # Automask wsclean 


        slurmfile = SCRIPTS+'/slurm_wsclean_data_'+code+'.sh'
        logfile = LOGS+'/slurm_wsclean_data_'+code+'.log'


        wsclean = gen.generate_syscall_wsclean(mslist=[myms],
                                imgname=data_prefix,
                                datacol='DATA',
                                bda=True,
                                mask='auto')


        gen.write_slurm(opfile=slurmfile,
                    jobname=code+'wdata',
                    logfile=logfile,
                    container=WSCLEAN_CONTAINER,
                    syscall=wsclean)


        job_id_data = 'DATA_'+code
        syscall = job_id_data+"=`sbatch "+slurmfile+" | awk '{print $4}'`"
        f.write(syscall+'\n')




        # ------------------------------------------------------------------------------
        # Predict 


        slurmfile = SCRIPTS+'/slurm_wsclean_predict1_'+code+'.sh'
        logfile = LOGS+'/slurm_predict1_'+code+'.log'


        predict = gen.generate_syscall_predict(msname=myms,imgbase=data_prefix)


        gen.write_slurm(opfile=slurmfile,
                    jobname=code+'prdct',
                    logfile=logfile,
                    container=WSCLEAN_CONTAINER,
                    syscall=predict)


        job_id_predict = 'PREDICT_'+code
        syscall = job_id_predict+"=`sbatch -d afterok:${"+job_id_data+"} "+slurmfile+" | awk '{print $4}'`"
        f.write(syscall+'\n')


        # ------------------------------------------------------------------------------
        # Self-calibrate phases 


        slurmfile = SCRIPTS+'/slurm_wsclean_cubical1_'+code+'.sh'
        logfile = LOGS+'/slurm_cubical1_'+code+'.log'


        cubical = gen.generate_syscall_cubical(parset=PARSETS+'/phasecal.parset',
                    myms=myms,
                    prefix='pcal')


        gen.write_slurm(opfile=slurmfile,
                    jobname=code+'pcal1',
                    logfile=logfile,
                    container=CUBICAL_CONTAINER,
                    syscall=cubical)


        job_id_cubical = 'CUBICAL_'+code
        syscall = job_id_cubical+"=`sbatch -d afterok:${"+job_id_predict+"} "+slurmfile+" | awk '{print $4}'`"
        f.write(syscall+'\n')


        # ------------------------------------------------------------------------------
        # Masked wsclean CORRECTED_DATA


        slurmfile = SCRIPTS+'/slurm_wsclean_pcal_'+code+'.sh'
        logfile = LOGS+'/slurm_pcal1_'+code+'.log'


        wsclean = gen.generate_syscall_wsclean(mslist=[myms],
                                imgname=pcal_prefix,
                                datacol='CORRECTED_DATA',
                                bda=True,
                                mask='auto')


        gen.write_slurm(opfile=slurmfile,
                    jobname=code+'wpcal',
                    logfile=logfile,
                    container=WSCLEAN_CONTAINER,
                    syscall=wsclean)


        job_id_pcal = 'IMGMASK2_'+code
        syscall = job_id_pcal+"=`sbatch -d afterok:${"+job_id_cubical+"} "+slurmfile+" | awk '{print $4}'`"
        f.write(syscall+'\n')


        # ------------------------------------------------------------------------------


    kill = 'echo "scancel "$'+job_id_data+'" "$'+job_id_predict+'" "$'+job_id_cubical+'" "$'+job_id_pcal+' > '+kill_file

    f.write(kill+'\n')

    f.close()


if __name__ == "__main__":


    main()